ARG PYTHON_VERSION=3.7.1


FROM python:${PYTHON_VERSION}-stretch as builder
ENV PYTHONUNBUFFERED 1

RUN python3 -m venv /venv

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN /venv/bin/pip install -r /app/requirements.txt

COPY . /app
#RUN /venv/bin/pip install -e /app


FROM python:${PYTHON_VERSION}-slim-stretch
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY --from=builder /venv /venv
COPY . /app

ENTRYPOINT ["/venv/bin/python3", "iam_roller.py"]
