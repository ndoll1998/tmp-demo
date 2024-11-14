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

env.register_const("Const", 5, "A Constant")

@env.register_action
def detect_objects() -> dict[str, str]:
    """Detects objects in the scene.

    Returns:
        (dict[str, str]): A dictionary of the following schema:
        {
            <object_id (str)>: {
                "description": <object_description (str)>,
                "x": <position_x (float)>,
                "y": <position_y (float)>,
            }
        }
    """
    return {
        "0": {
            "description": "A green apple.",
            "x": 0,
            "y": 0,
        },
        "1": {
            "description": "A lemon.",
            "x": 10,
            "y": 10,
        },
        "2": {
            "description": "An orange.",
            "x": 0,
            "y": 0,
        },
    }


@env.register_action
def move_object(obj_id: str, x: float, y: float) -> bool:
    """Moves the object with `obj_id` to position (x, y).

    Args:
        obj_id (str): The object_id of the object to move.
        x (float): The x coordinate to move to.
        y (float): The y coordinate to move to.

    Returns:
        (bool): True if successfull, False otherwise
    """
    return True


# create the app that serves the environment
app = FastAPI()
app.include_router(env, prefix="/env")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
