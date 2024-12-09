import asyncio
from typing import TypeVar

import httpx
import websockets

from agent.callbacks import AgentCallback
from agent.dto import ChatMessage

T = TypeVar("T", str, None)


async def connect_and_receive_messages(
    message: T = None,
    host: str = "localhost",
    port: int = 8000,
    callbacks: list[AgentCallback] = [],
) -> T:
    client = httpx.AsyncClient(base_url=f"http://{host}:{port}", timeout=None)

    async with websockets.connect(f"ws://{host}:{port}/ws/messages") as websocket:
        if message is not None:
            coro = client.post("/chat", params={"message": message})
            task = asyncio.create_task(coro)

        try:
            # Continuously listen for messages from the server
            async for data in websocket:
                chat_message = ChatMessage.model_validate_json(data)
                for cb in callbacks:
                    cb.on_step(chat_message)

        except websockets.ConnectionClosed:
            print("WebSocket connection closed")

        if message is not None:
            return await task
