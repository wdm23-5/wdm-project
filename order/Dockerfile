FROM python:3.11-slim

WORKDIR /home/flask-app

COPY ./order/requirements.txt .

RUN pip install -r requirements.txt

COPY ./order .

COPY ./common ./common

EXPOSE 5000
