FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /drodos
COPY requirements.txt /drodos/
RUN pip install -r requirements.txt
COPY . /drodos/