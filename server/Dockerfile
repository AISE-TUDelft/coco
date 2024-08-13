# using the official python image
FROM nvidia/cuda:12.6.0-base-ubuntu20.04

# as the official image is based on ubuntu, we need to update the package list
# and install some dependencies
RUN apt-get update && apt-get install -y \
    libnvidia-ml-dev \
    software-properties-common \
    nvidia-container-toolkit

# install python and pip python3.10 (simply because it was used for the development)
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-distutils python3.10-venv python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    ln -s /usr/bin/python3.10 /usr/bin/python

RUN python3.10 -m pip install --upgrade --force-reinstall pip

WORKDIR /app

COPY requirements.txt .

RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
