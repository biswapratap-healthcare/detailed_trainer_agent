FROM python:3.6.4-slim-jessie
COPY data_connector.py /app
COPY feature_extractor.py /app
COPY db.py /app
COPY train_model.py /app
COPY annotation.py /app
COPY dicom_parser.py /app
COPY requirements.txt /app
COPY driver.py /app
COPY vgg16_weights_tf_dim_ordering_tf_kernels_notop.h5 ~/.keras/models
WORKDIR /app
RUN apt-get update
RUN apt-get -y install python-opencv
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD python driver.py
