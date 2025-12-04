.PHONY: build install test clean

build:
	poetry build

install:
	pip install .

format:
	poetry run black .

test:
	poetry run pytest

clean:
	rm -rf dist/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete