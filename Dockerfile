FROM python:alpine as build

LABEL maintainer="Matias 'nnss' Palomec"

RUN mkdir -p /ping-mon/static/
COPY app.py requirements.txt README.md LICENSE /ping-mon/
COPY static /ping-mon/static/

WORKDIR /ping-mon/

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "/ping-mon/app.py"]
