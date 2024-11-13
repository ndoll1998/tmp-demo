import logging
from asyncio import Queue

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute, APIRouter, APIWebSocketRoute
from llama_index.core.agent import AgentChatResponse, AgentRunner
from llama_index.core.memory import ChatMemoryBuffer

from agent.callbacks import AgentCallback
from agent.dto import ChatMessage, MessageRole

logger = logging.getLogger(__name__)


class AgentService(APIRouter):
    def __init__(
        self, agent: AgentRunner, prefix: str = "", callbacks: list[AgentCallback] = []
    ) -> None:
        self.agent = agent
        self.callbacks = callbacks
        self.step_history = Queue()

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
        self.empty_step_history()
        logger.info("Agent resetted.")

    async def chat(self, message: str) -> str:
        await self.empty_step_history()
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
        for cb in self.callbacks:
            cb.on_start(ChatMessage(role=MessageRole.USER, content=message))

        task = self.agent.create_task(message)
        i = 0
        while not (await self.agent.arun_step(task.task_id)).is_last:
            new_memory: ChatMemoryBuffer = task.extra_state["new_memory"]
            messages = await new_memory.chat_store.aget_messages(new_memory.chat_store_key)
            for chat_message in messages[i:]:
                assert isinstance(chat_message, ChatMessage)
                await self.step_history.put(chat_message)

                for cb in self.callbacks:
                    cb.on_step(chat_message)

                i += 1

        await self.step_history.put(None)

        # now that the step execution is done, we can finalize response
        response: AgentChatResponse = self.agent.finalize_response(task.task_id)

        for cb in self.callbacks:
            cb.on_completion(response.response)

        return response
