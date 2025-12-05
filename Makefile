.PHONY: build install test clean format

build:
	poetry build

install:
	pip install .

format:
	poetry run black .

test:
	poetry run django-admin test duplicator.tests --settings=duplicator.tests.settings --pythonpath=.

clean:
	rm -rf dist/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete