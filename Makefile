# Default rule/target
.DEFAULT_GOAL := build

COMPONENT := dungeon
IMAGE_REPOSITORY := ghcr.io/freegroup
VERSION := $(shell uuidgen)
IMAGE_NAME := $(IMAGE_REPOSITORY)/$(COMPONENT):$(VERSION)



## Build all docker files
.PHONY: build
build: 
	@echo "Building Docker Image for [$(COMPONENT)]"
	@docker build --rm -t $(IMAGE_NAME) --progress=plain -f ./Dockerfile .
	@docker push $(IMAGE_NAME)

