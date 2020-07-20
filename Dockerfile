FROM python:3.6.4-slim-jessie
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get -y install python-opencv
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python -c 'from keras.applications import VGG16; VGG16(weights="imagenet")'
CMD python driver.py
