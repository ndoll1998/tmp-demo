import asyncio
import logging
from typing import Any

from fastapi.routing import APIRoute, APIRouter, APIWebSocketRoute
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from llama_index.core.agent import AgentChatResponse, AgentRunner
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.llms import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass
        finally:
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()

    async def disconnect_all(self) -> None:
        to_remove = self.active_connections
        self.active_connections = []
        await asyncio.gather(*[ws.close() for ws in to_remove])

    async def send_personal_message(self, data: dict, websocket: WebSocket) -> None:
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_json(data)

    async def broadcast(self, data: dict, exclude: list[WebSocket] | None = None) -> None:
        exclude = exclude or []
        exclude = [ws.client for ws in exclude]

        for connection in self.active_connections:
            if connection.application_state == WebSocketState.CONNECTED:
                if connection.client not in exclude:
                    await connection.send_json(data)
            else:
                self.disconnect(connection)


class MessageQueueCallbackHandler(BaseCallbackHandler):
    """A llama-index callback handler that puts all chat messages
    in an asyncio queue.
    """

    def __init__(self, queue: asyncio.Queue[ChatMessage]) -> None:
        super().__init__(event_starts_to_ignore=[], event_ends_to_ignore=[])
        self.queue = queue
        self._history = []

    def start_trace(self, trace_id: str | None = None) -> None:
        return None

    def end_trace(
        self, trace_id: str | None = None, trace_map: dict[str, list[str]] | None = None
    ) -> None:
        return None

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: dict[str, Any] | None = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        if (
            event_type in [CBEventType.LLM, CBEventType.AGENT_STEP, CBEventType.FUNCTION_CALL]
            and payload is not None
        ):
            self.process_payload(payload)

        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: dict[str, Any] | None = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        if (
            event_type in [CBEventType.LLM, CBEventType.AGENT_STEP, CBEventType.FUNCTION_CALL]
            and payload is not None
        ):
            self.process_payload(payload)

        return event_id

    def process_payload(self, payload: dict) -> None:
        if EventPayload.MESSAGES in payload:
            messages: list[ChatMessage] = payload[EventPayload.MESSAGES]
            response: ChatResponse = payload.get(EventPayload.RESPONSE)

            if response is not None:
                messages.append(response.message)

            messages = [message for message in messages if message not in self._history]

            self._history.extend(messages)
            for message in messages:
                self.queue.put_nowait(message)


class AgentService(APIRouter):
    def __init__(self, agent: AgentRunner, prefix: str = "") -> None:
        self.agent = agent
        self.agent_lock = asyncio.Lock()
        self.connection_manager = ConnectionManager()
        self.message_queue: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self.callback_handler = MessageQueueCallbackHandler(self.message_queue)
        agent.callback_manager.add_handler(self.callback_handler)

        routes = [
            APIRoute(path="/reset", endpoint=self.reset, methods=["GET"]),
            APIRoute(path="/chat", endpoint=self.chat, methods=["POST"]),
            APIWebSocketRoute(path="/ws/messages", endpoint=self.ws_messages),
        ]

        super().__init__(
            prefix=prefix,
            routes=routes,
        )

    async def reset(self) -> None:
        self.agent.reset()
        logger.info("Agent resetted.")

    async def chat(self, message: str) -> str:
        message_loop_task = asyncio.create_task(self.broadcast_messages())
        async with self.agent_lock:
            # run the agent
            response = await self.run_task(message=message)
            # this stops message broadcasting
            await self.message_queue.put(None)

        await message_loop_task
        return response.response

    async def ws_messages(self, websocket: WebSocket) -> None:
        await self.connection_manager.connect(websocket)

        try:
            while True:
                await websocket.receive()

        except WebSocketDisconnect:
            print("WebSocket disconnected")
        except Exception as e:
            print(f"Error in WebSocket communication: {e}")
        finally:
            await self.connection_manager.disconnect(websocket)

    async def run_task(self, message: str) -> AgentChatResponse:
        task = self.agent.create_task(message)
        while not (await self.agent.arun_step(task.task_id)).is_last:
            pass
        # now that the step execution is done, we can finalize response
        return self.agent.finalize_response(task.task_id)

    async def broadcast_messages(self) -> None:
        while (chat_message := await self.message_queue.get()) is not None:
            await self.connection_manager.broadcast(chat_message.model_dump())

        await self.connection_manager.disconnect_all()
