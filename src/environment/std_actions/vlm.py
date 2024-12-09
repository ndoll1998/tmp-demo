from llama_index.core.llms import ChatMessage, ImageBlock, MessageRole, TextBlock
from llama_index.llms.openai import OpenAI
from PIL import Image

from environment.utils import pil_image_to_bytes


class VisionLanguageModelAction(OpenAI):
    def prompt_vision_model(self, prompt: str, image: Image.Image | None = None) -> str:
        """Python function used to prompt a vision language model to get detailed
        descriptions of images or objects in images.

        Args:
            prompt (str): The prompt for the LLM.
            image (PIL.Image.Imagel): An image that is given to the LLM.

        Returns:
            str: The response completion of the LLM.
        """
        # If an image is provided, process with both image and text
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=prompt),
            ],
        )

        if image is not None:
            msg.blocks.append(ImageBlock(image=pil_image_to_bytes(image)))

        # Use LLMImageResponse to send both the prompt and image
        response = self.chat(messages=[msg])
        # Retrieve the LLM's response text
        return response.message.content
