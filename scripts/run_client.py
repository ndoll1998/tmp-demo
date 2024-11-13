import asyncio
import json

import httpx
import websockets

from agent.dto import ChatMessage, MessageRole


def format_to_kwargs(args: str) -> str:
    d = json.loads(args)

    formatted_kwargs = []

    for key, value in d.items():
        # Check if the value is a multiline string
        if isinstance(value, str) and "\n" in value:
            # Format multiline strings with triple backticks and further indentation
            formatted_value = f"```\n        {value.replace('\n', '\n        ')}\n    ```"
        else:
            # Use repr for single-line values and add normal indentation
            formatted_value = repr(value)

        # Format each key-value pair as a keyword argument with initial indentation
        formatted_kwargs.append(f"    {key}={formatted_value}")

    # Join each argument on a new line
    return "\n".join(formatted_kwargs)


async def connect_and_receive_messages(message: str, host: str = "localhost", port: int = 8001):
    client = httpx.AsyncClient(base_url=f"http://{host}:{port}", timeout=None)

    async with websockets.connect(f"ws://{host}:{port}/ws/steps") as websocket:
        coro = client.post("/chat", params={"message": message})
        task = asyncio.create_task(coro)

        try:
            # Continuously listen for messages from the server
            async for data in websocket:
                chat_message = ChatMessage.model_validate_json(data)

                if chat_message.role == MessageRole.USER:
                    # print(f"USER: {chat_message.content}")
                    pass
                elif chat_message.role == MessageRole.TOOL:
                    tool_name = chat_message.additional_kwargs["name"]
                    print(f"TOOL[{tool_name}]: {chat_message.content}")
                elif chat_message.role == MessageRole.ASSISTANT:
                    if "tool_calls" in chat_message.additional_kwargs:
                        for tool_call in chat_message.additional_kwargs["tool_calls"]:
                            tool_name = tool_call["function"]["name"]
                            arguments = format_to_kwargs(tool_call["function"]["arguments"])
                            print(f"ASSISTANT: {tool_name}(\n{arguments}\n)")
                    else:
                        print(f"ASSISTANT: {chat_message.content}")

                print()

        except websockets.ConnectionClosed:
            print("WebSocket connection closed")

        response = await task
        print("Final Response:", response.text)


if __name__ == "__main__":
    # reset agent
    httpx.get("http://localhost:8001/reset")

    while (user_input := input("USER: ")) != "":
        # Run the WebSocket client
        asyncio.run(connect_and_receive_messages(user_input))
