import logging
import logging.config
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI

from environment.remote import RemoteEnv
from robot.actions import RobotActions

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

ENV_DESCRIPTION = """The environment is a workspace where a robot arm can move, interact with objects, and perform basic manipulation tasks. The robot arm can precisely navigate to different coordinates within this workspace, allowing it to approach and engage with various objects positioned throughout the area. It can grab a single object, holding it securely until instructed to release it. The robot can only handle one object at a time and does not have the ability to pick up multiple objects simultaneously. Tasks may involve positioning, moving, or sorting objects based on their location or type."""  # noqa: E501

env = RemoteEnv(description=ENV_DESCRIPTION)

env.register_const(
    "conveyer_belt_bbox",
    value=(0, 0, 20, 100),
    description="The bounding box coordinates of the conveyer belt as (x_0, y_0, x_1, y_1).",
)
env.register_const(
    "conveyer_belt_height", value=10, description="The height the conveyer belt is placed at."
)

# register all robot actions
robot = RobotActions()
for action in robot.actions:
    env.register_action(action)


@env.register_action
def detect_objects() -> list[dict[str, Any]]:
    """Detects objects in the curent image and returns a list of detected objects.

    Each detected object is represented as a dictionary containing:
    - "object_id" (int): A unique identifier for the object.
    - "bbox" (tuple[int, int, int, int]): The bounding box coordinates for the object as
      (x_min, y_min, x_max, y_max), defining the object's location in the image.
    - "description" (str): A label or description for the object.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each representing a detected object
        with "id", "bbox", and "description" fields.
    """

    return [
        {"id": 0, "bbox": (300, 150, 350, 200), "description": "Spray"},
        {"id": 1, "bbox": (300, -150, 350, -200), "description": "Mug"},
        {"id": 2, "bbox": (200, -25, 250, 25), "description": "Pen"},
    ]


# create the app that serves the environment
app = FastAPI()
app.include_router(env, prefix="/env")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
