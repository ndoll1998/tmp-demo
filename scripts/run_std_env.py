from environment.remote import RemoteEnv
from environment.std_actions.image import ImageActions
from environment.std_actions.vlm import VisionLanguageModelAction
from utils.logging import setup_logging

setup_logging()

env = RemoteEnv()

vlm = VisionLanguageModelAction(model="gpt-4o")
env.register_action(vlm.prompt_vision_model)

# register object detection
image_actions = ImageActions()
env.register_action(image_actions.detect_objects)
env.register_action(image_actions.crop_image)
env.register_action(image_actions.draw_bounding_boxes)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    from utils.constants import STD_ENV_HOST_ADRESS, STD_ENV_PORT

    # create the app that serves the environment
    app = FastAPI()
    app.include_router(env)

    uvicorn.run(app, host=STD_ENV_HOST_ADRESS, port=STD_ENV_PORT, reload=False)
