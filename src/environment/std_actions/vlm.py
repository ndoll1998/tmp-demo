from llama_index.core.schema import ImageDocument
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from PIL import Image

from environment.utils import pil_image_to_base64


class VisionLanguageModelAction(OpenAIMultiModal):
    def prompt_vision_model(self, prompt: str, image: Image.Image | None = None) -> str:
        """Prompt a vision language model to get detailed
        descriptions of images or objects in images.

        Args:
            prompt (str): The prompt for the LLM.
            image (PIL.Image.Imagel): An image that is given to the LLM.

        Returns:
            str: The response completion of the LLM.
        """
        # If an image is provided, process with both image and text
        if image is not None:
            image_doc = ImageDocument(image=pil_image_to_base64(image))
            # Use LLMImageResponse to send both the prompt and image
            response = self.complete(prompt=prompt, image_documents=[image_doc])
        else:
            # Only send the text prompt
            response = self.complete(prompt=prompt)

        # Retrieve the LLM's response text
        return response.text
