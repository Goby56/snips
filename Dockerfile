FROM python:3.9-bullseye

RUN pip install --upgrade pip

COPY ./requirements.txt . 
RUN pip install -r requirements.txt

COPY ./src /app
WORKDIR /app

COPY ./entrypoint.sh /
ENTRYPOINT [ "sh", "/entrypoint.sh" ]
