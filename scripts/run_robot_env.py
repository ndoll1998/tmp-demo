import logging
import logging.config
import sys

import uvicorn
from fastapi import FastAPI

from environment.remote import RemoteEnv
from robot.actions import RobotActions
from robot.transform import WorldTransform

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

ENV_DESCRIPTION = """## Environment
The environment is a workspace where a robot arm can move, interact with objects, and perform basic manipulation tasks. The robot arm can precisely navigate to different coordinates within this workspace, allowing it to approach and engage with various objects positioned throughout the area. It can grab a single object, holding it securely until instructed to release it. The robot can only handle one object at a time and does not have the ability to pick up multiple objects simultaneously. Tasks may involve positioning, moving, or sorting objects based on their location or type."""  # noqa: E501

env = RemoteEnv(description=ENV_DESCRIPTION)

# register all robot actions
robot = RobotActions()
for action in robot.actions:
    env.register_action(action)

# register world transform actions
world_transform = WorldTransform("data/world_state.yaml")
env.register_action(world_transform.transform_pixel_to_world_coords)
env.register_action(world_transform.transform_world_to_pixel_coords)

# register world boundaries
env.register_const(
    name="world_boundaries",
    description="Defines the robot's operational area with coordinates (min_x, min_y, max_x, max_y).",  # noqa: E501
    value=(150, -250, 400, 250),
)

# create the app that serves the environment
app = FastAPI()
app.include_router(env, prefix="/env")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
