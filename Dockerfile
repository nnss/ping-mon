FROM python:alpine as build

LABEL maintainer="Matias 'nnss' Palomec"
ENV db_path /ping-data/

RUN mkdir -p /ping-data/
RUN mkdir -p /ping-mon/static/

COPY app.py requirements.txt README.md LICENSE prepare.py /ping-mon/

WORKDIR /ping-mon/

RUN python prepare.py

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "/ping-mon/app.py"]
