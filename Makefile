APPLICATION_NAME := acos-prometheus-exporter
GITHUB_USERNAME := ${GITHUB_USERNAME}
VERSION ?= $(shell git describe --tags)

DOCKER_FILE := "./build/Dockerfile"
DOCKER_PROXY := "ghcr.io/$(GITHUB_USERNAME)"

sandbox:
	docker compose -f docker-compose.yml up -d
	docker exec -it ${APPLICATION_NAME} bash

rebuild: 
	docker compose -f docker-compose.yml up -d --build

init:
	export COMPOSE_DOCKER_CLI_BUILD=0
	export DOCKER_BUILDKIT=0

login: check-github-username
	docker login ghcr.io -u ${GITHUB_USERNAME}

d-build: check-version
	docker build  \
	-f ${DOCKER_FILE} \
	--platform=linux/amd64 \
	--tag ${DOCKER_PROXY}/${APPLICATION_NAME}:$(VERSION)  \
	.

d-push: check-version
	docker push ${DOCKER_PROXY}/${APPLICATION_NAME}:$(VERSION)

check-github-username:
ifndef GITHUB_USERNAME
	$(error GITHUB_USERNAME is undefined)
endif

check-version:
ifndef VERSION
	$(error VERSION is undefined)
endif
