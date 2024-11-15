from PIL import Image

from environment.remote import RemoteEnv
from utils.logging import setup_logging

setup_logging()

env = RemoteEnv()
env.register_const(
    "conveyer_belt_bbox",
    value=(0, 0, 20, 100),
    description="The bounding box coordinates of the conveyer belt as (x_0, y_0, x_1, y_1).",
)
env.register_const(
    "conveyer_belt_height", value=10, description="The height the conveyer belt is placed at."
)


@env.register_action
def capture_image(brightness: float = 1.5, contrast: float = 1.5) -> Image.Image | None:
    """
    Captures an image from the webcam and returns the image as a Pillow Image object.

    Args:
        brightness (float): Brightness factor used to enhance the image brightness.
        contrast (float): Contrast factor used to enhance the image contrast.

    Returns:
        PIL.Image.Image | None: The image if capture is successful,
        or None if the image capture failed.
    """
    return Image.open("data/example_image.jpeg")


@env.register_action
def grab_object() -> bool:
    """Commands the robot to grab the object at it's current position.

    This function instructs the robot to attempt to grasp an object
    placed at it's current position..

    Returns:
        bool: True if the robot successfully grabbed the object, False otherwise.
    """
    return True


@env.register_action
def release_object() -> bool:
    """Commands the robot to release a currently held object.

    This function sends a command to the robot to release the object it is
    currently holding, dropping it at its current position.

    Returns:
        bool: True if the robot successfully released the object, False otherwise.
    """
    return True


@env.register_action
def move_to(x: float, y: float) -> bool:
    """
    Commands the robot to move to a specified (x, y) position in world space.

    Args:
        x (float): The x-coordinate of the target position in world space.
        y (float): The y-coordinate of the target position in world space.

    Returns:
        bool: True if the robot successfully reached the specified position,
        False otherwise.
    """
    return True


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    from utils.constants import ENV_HOST_ADRESS, ENV_PORT

    # create the app that serves the environment
    app = FastAPI()
    app.include_router(env)

    uvicorn.run(app, host=ENV_HOST_ADRESS, port=ENV_PORT, reload=False)
