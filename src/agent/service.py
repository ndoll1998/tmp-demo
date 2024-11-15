import logging
from asyncio import Queue

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute, APIRouter, APIWebSocketRoute
from llama_index.core.agent import AgentChatResponse, AgentRunner

from agent.callbacks import AgentCallback
from agent.dto import ChatMessage

logger = logging.getLogger(__name__)


class AgentService(APIRouter):
    def __init__(
        self, agent: AgentRunner, prefix: str = "", callbacks: list[AgentCallback] = []
    ) -> None:
        self.agent = agent
        self.callbacks = callbacks
        self.step_history = Queue()
        self.step_idx = 0

        routes = [
            APIRoute(path="/reset", endpoint=self.reset, methods=["GET"]),
            APIRoute(path="/chat", endpoint=self.chat, methods=["POST"]),
            APIWebSocketRoute(path="/ws/steps", endpoint=self.ws_steps),
        ]

        super().__init__(
            prefix=prefix,
            routes=routes,
        )

    async def reset(self) -> None:
        self.agent.reset()
        self.step_idx = 0
        await self.empty_step_history()

        logger.info("Agent resetted.")

    async def chat(self, message: str) -> str:
        if not self.step_history.empty():
            raise RuntimeError("Agent is running.")

        response = await self.run_task(message=message)
        return response.response

    async def ws_steps(self, websocket: WebSocket) -> None:
        await websocket.accept()  # Accept the WebSocket connection

        try:
            while (chat_message := await self.step_history.get()) is not None:
                # Send each generated message over the WebSocket
                await websocket.send_text(chat_message.model_dump_json(indent=2))

        except WebSocketDisconnect:
            print("WebSocket disconnected")
        except Exception as e:
            print(f"Error in WebSocket communication: {e}")
        finally:
            await websocket.close()

    async def empty_step_history(self) -> None:
        while not self.step_history.empty():
            await self.step_history.get()

    async def run_task(self, message: str) -> AgentChatResponse:
        task = self.agent.create_task(message)

        while not (await self.agent.arun_step(task.task_id)).is_last:
            await self.gather_new_messages()

        # now that the step execution is done, we can finalize response
        response: AgentChatResponse = self.agent.finalize_response(task.task_id)

        await self.gather_new_messages()
        await self.step_history.put(None)

        return response

    async def gather_new_messages(self) -> None:
        chat_messages = await self.agent.memory.chat_store.aget_messages(
            self.agent.memory.chat_store_key
        )

        for chat_message in chat_messages[self.step_idx :]:
            assert isinstance(chat_message, ChatMessage)
            await self.step_history.put(chat_message)

            for cb in self.callbacks:
                cb.on_step(chat_message)

        self.step_idx += len(chat_messages[self.step_idx :])
