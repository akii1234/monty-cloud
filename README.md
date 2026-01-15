# Monty Cloud Image Service

Image upload and storage service built with API Gateway + Lambda + S3 + DynamoDB.
Supports JSON base64 uploads and multipart/form-data uploads.

## Requirements
- Python 3.7+
- Node.js 18+ (for Serverless Framework)
- LocalStack (for local AWS services)

## Setup
1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt -r requirements-dev.txt`
2. Install Serverless Framework and plugins:
   - `npm i -g serverless`
   - `serverless plugin install -n serverless-python-requirements`
   - `serverless plugin install -n serverless-localstack`

## LocalStack
Start LocalStack separately, then deploy:
- `serverless deploy --stage local`

Optional bootstrap (if you want to create resources manually):
- `pip install awscli-local`
- `bash scripts/bootstrap_localstack.sh`

## API Usage
See `docs/API.md` for endpoint details and examples.

## Tests
- `pytest`

## Makefile
Common shortcuts:
- `make install`
- `make test`
- `make bootstrap-localstack`

