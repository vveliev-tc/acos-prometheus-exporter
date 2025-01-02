ARG PYTHON_VERSION=3.12
ARG BASE_IMAGE=slim-bookworm

FROM python:${PYTHON_VERSION}-${BASE_IMAGE} AS build

RUN pip install --upgrade pip
RUN pip install pipenv

WORKDIR /app

COPY src/acos_exporter.py /app/acos_exporter.py
COPY src/Pipfile /app/Pipfile
COPY src/Pipfile.lock /app/Pipfile.lock
COPY build/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN pipenv install --deploy

EXPOSE 9734

LABEL service="a10-exporter"
LABEL org.opencontainers.image.source=https://github.com/vveliev-tc/acos-prometheus-exporter
LABEL org.opencontainers.image.description="A10 Networks Prometheus Exporter"

ENTRYPOINT ["/entrypoint.sh"]

FROM python:${PYTHON_VERSION}-${BASE_IMAGE} AS production

WORKDIR /app

COPY src/acos_exporter.py /app/acos_exporter.py
COPY build/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --from=build /root/.local/share/virtualenvs /root/.local/share/virtualenvs

EXPOSE 9734

LABEL service="a10-exporter"
LABEL org.opencontainers.image.source=https://github.com/vveliev-tc/acos-prometheus-exporter
LABEL org.opencontainers.image.description="A10 Networks Prometheus Exporter"

ENTRYPOINT ["/entrypoint.sh"]