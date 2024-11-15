import os

AGENT_HOST_ADRESS = os.getenv("AGENT_HOST_ADRESS", "localhost")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8000"))
STD_ENV_HOST_ADRESS = os.getenv("STD_ENV_HOST_ADRESS", "localhost")
STD_ENV_PORT = int(os.getenv("STD_ENV_PORT", "8001"))
ENV_HOST_ADRESS = os.getenv("ENV_HOST_ADRESS", "localhost")
ENV_PORT = int(os.getenv("ENV_PORT", "8002"))
