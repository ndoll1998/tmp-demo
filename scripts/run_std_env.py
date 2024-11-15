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


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    # create the app that serves the environment
    app = FastAPI()
    app.include_router(env, prefix="/env")

    uvicorn.run(app, host="127.0.0.1", port=8002, reload=False)
