FROM python:3.11-slim

WORKDIR /home/flask-app

COPY ./payment/requirements.txt .

RUN pip install -r requirements.txt

COPY ./payment .

COPY ./common ./common

EXPOSE 5000
