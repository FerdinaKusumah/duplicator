.PHONY: build install test clean format lint

build:
	poetry build

install:
	poetry install

format:
	poetry run black .

lint:
	poetry run black --check .

test:
	poetry run coverage run -m django test duplicator.tests --settings=duplicator.tests.settings --pythonpath=.
	poetry run coverage report

clean:
	rm -rf dist/ .coverage
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
