import logging
import logging.config
import sys

import uvicorn
from fastapi import FastAPI

from environment.remote import RemoteEnv

# Define basic configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Apply the configuration
logging.config.dictConfig(logging_config)

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
def detect_objects() -> dict[str, str]:
    """Detects objects in the scene.

    Returns:
        (dict[str, str]): A dictionary of the following schema:
        {
            <object_id (str)>: {
                "description": <object_description (str)>,
                "x": <(left_x, right_x) (tuple[float, float])>,
                "y": <(upper_y, lower_y) tuple[float, float]>,
                "z": <height (float)>
            }
        }
    """
    return {
        "0": {
            "description": "A green apple.",
            "x": (20, 22),
            "y": (78, 80),
            "z": 10,
        },
        "1": {
            "description": "A lemon.",
            "x": (10, 13),
            "y": (40, 42),
            "z": 10,
        },
        "2": {
            "description": "An orange.",
            "x": (56, 58),
            "y": (33, 36),
            "z": 10,
        },
    }


@env.register_action
def grab_object(x: float, y: float, z: float) -> bool:
    """Grabs an object at position (x, y, z). Make sure to
    always grab at the middlepoint of an object.

    Args:
        x (float): The x coordinate to grab at.
        y (float): The y coordinate to grab at.
        z (float): The z coordinate to grab at.

    Returns:
        (bool): True if successfull, False otherwise
    """
    return True


@env.register_action
def release_object() -> bool:
    """Release the current object.

    Returns:
        (bool): True if successfull, False otherwise
    """
    return True


@env.register_action
def move(obj_id: str, x: float, y: float, z: float) -> bool:
    """Move to location (x, y, z).

    Args:
        x (float): The x coordinate to move to.
        y (float): The y coordinate to move to.
        z (float): The z coordinate to move to.

    Returns:
        (bool): True if successfull, False otherwise
    """
    return True


# create the app that serves the environment
app = FastAPI()
app.include_router(env, prefix="/env")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
