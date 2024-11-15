FROM python:3.12-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Update the package list and install Git
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0

COPY pyproject.toml .
RUN mkdir src/ && \
    mkdir src/agent && \
    mkdir src/environment && \
    mkdir src/robot && \
    mkdir src/utils
# install dependencies
RUN pip install --upgrade pip && \
    pip install -e . && \
    pip cache purge

# install source code
COPY src/ src/
RUN pip install -e . --no-deps && \
    rm pyproject.toml && \
    find . -type d -name "*.egg-info" -exec rm -rf {} +

# install scripts
COPY scripts/ scripts/

# # cleanup source files
# # 1. compile all source code
# # 2. delete all source code
# # 3. rename all compiled files removing the compiler postfix
# # 4. move compiled files out of __pycache__ directories
# # 5. delete __pycache__ directories
# RUN python -OO -m compileall -f src && \
#     find . -name "*.py" -exec rm {} + && \
#     find . -name "*.pyc" -exec sh -c 'f="{}"; mv "$f" "${f%.cpython-311*.pyc}.pyc"' \; && \
#     find . -path "**/__pycache__/*" -execdir mv -t ../ {} + && \
#     find . -path "**/__pycache__" -execdir rm -r {} +
