FROM python:3.8-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/iadapter

RUN apk update \
    && apk add gcc libc-dev libffi-dev openssl-dev python3-dev cargo rust

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
WORKDIR /usr/src/iadapter