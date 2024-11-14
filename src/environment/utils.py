import base64
from io import BytesIO

from PIL import Image


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


def base64_to_pil_image(str_base64: str) -> Image.Image:
    """
    Convert a base64 encoded string back to a PIL Image.

    This function decodes the base64 string and converts it
    into a PIL Image object, which can then be used for further
    image processing.

    Args:
        str_base64 (str): The base64 encoded string representing the image.

    Returns:
        Image.Image: The decoded image as a PIL Image object.
    """
    # Decode the base64 string to bytes
    image_data = base64.b64decode(str_base64)
    # Create a BytesIO buffer from the binary data
    buffer = BytesIO(image_data)
    # Open the buffer as an image
    image = Image.open(buffer)
    return image
