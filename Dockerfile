FROM nginx:latest

COPY nginx.conf /etc/nginx/nginx.conf

FROM python:3.9-bullseye

RUN pip install -r requirements.txt

