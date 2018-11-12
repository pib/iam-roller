FROM python:3.7.1-alpine as base

FROM base as builder
ENV PYTHONUNBUFFERED 1
WORKDIR /install

RUN apk --no-cache add --update build-base libffi-dev openssl-dev

COPY requirements.txt /requirements.txt

RUN pip install --install-option="--prefix=/install" -r /requirements.txt


FROM base
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . /app

ENTRYPOINT ["python3", "iam_roller.py"]
