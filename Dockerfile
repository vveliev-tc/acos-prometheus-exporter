ARG PYTHON_VERSION=3.8
ARG BASE_IMAGE=slim-bookworm

FROM python:${PYTHON_VERSION}-${BASE_IMAGE} AS development

RUN apt-get update --fix-missing
RUN apt-get install -y build-essential

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["acos_exporter.py"]