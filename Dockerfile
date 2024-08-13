# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.12
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/