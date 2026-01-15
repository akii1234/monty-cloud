SHELL := /bin/bash
.DEFAULT_GOAL := help

VENV_DIR ?= .venv

.PHONY: help venv install test clean bootstrap-localstack deploy-localstack

help:
	@echo "Targets:"
	@echo "  venv               Create virtual environment"
	@echo "  install            Install dependencies into venv"
	@echo "  test               Run unit tests"
	@echo "  bootstrap-localstack  Create local S3 bucket and DynamoDB table"
	@echo "  deploy-localstack     Deploy CloudFormation stack to LocalStack"
	@echo "  clean              Remove venv and caches"

venv:
	python -m venv $(VENV_DIR)

install: venv
	source $(VENV_DIR)/bin/activate && \
	pip install -r requirements.txt -r requirements-dev.txt

test: install
	source $(VENV_DIR)/bin/activate && \
	pytest

bootstrap-localstack:
	source $(VENV_DIR)/bin/activate && \
	bash scripts/bootstrap_localstack.sh

deploy-localstack:
	source $(VENV_DIR)/bin/activate && \
	bash scripts/deploy_localstack.sh

clean:
	rm -rf $(VENV_DIR) .pytest_cache __pycache__ tests/__pycache__

