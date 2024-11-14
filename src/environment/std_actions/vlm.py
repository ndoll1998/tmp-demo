import base64
from io import BytesIO

from llama_index.core.schema import ImageDocument
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from PIL import Image

DEFAULT_OPENAI_MODEL = "gpt-4o"


def pil_image_to_base64(image: Image.Image) -> str:
    # Convert image to RGB if it has an alpha channel (RGBA)
    if image.mode == "RGBA":
        image = image.convert("RGB")

    # Create an in-memory buffer to save the image
    buffer = BytesIO()
    # Save the image to the buffer in a specific format (e.g., JPEG)
    image.save(buffer, format="JPEG")
    # Get the binary data from the buffer
    image_bytes = buffer.getvalue()
    # Encode the binary data to a base64 string
    base64_string = base64.b64encode(image_bytes).decode("utf-8")
    return base64_string


class VisionLanguageModelAction:
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 1.0,
        max_retries: int = 3,
        timeout: float = 60.0,
        reuse_client: bool = True,
        api_key: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
    ) -> None:
        self.llm = OpenAIMultiModal(
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout,
            reuse_client=reuse_client,
            api_key=api_key,
            api_base=api_base,
            api_version=api_version,
        )

    def prompt(self, prompt: str, image: Image.Image | None = None) -> str:
        """Prompt a language model with a prompt and (optional) an image.

        This function is useful for getting a description of the image by an LLM.

        Args:
            prompt (str): The prompt for the LLM.
            image (PIL.Image.Image, optional): An image that is given to the LLM.

        Returns:
            (str): The response completion of the LLM.
        """
        # If an image is provided, process with both image and text
        if image is not None:
            image_doc = ImageDocument(image=pil_image_to_base64(image))
            # Use LLMImageResponse to send both the prompt and image
            response = self.llm.complete(prompt=prompt, image_documents=[image_doc])
        else:
            # Only send the text prompt
            response = self.llm.complete(prompt=prompt)

        # Retrieve the LLM's response text
        return response.text
