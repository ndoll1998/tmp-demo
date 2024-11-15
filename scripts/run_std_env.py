import logging
import logging.config
import sys

from environment.remote import RemoteEnv
from environment.std_actions.image import ImageActions
from environment.std_actions.vlm import VisionLanguageModelAction

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

vlm = VisionLanguageModelAction(model="gpt-4o")

env = RemoteEnv()
env.register_action(vlm.prompt)


# register object detection
image_actions = ImageActions()
env.register_action(image_actions.detect_objects)
env.register_action(image_actions.crop_image)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    # create the app that serves the environment
    app = FastAPI()
    app.include_router(env, prefix="/env")
    uvicorn.run(app, host="127.0.0.1", port=8002, reload=False)
