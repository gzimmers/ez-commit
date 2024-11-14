.PHONY: test cc venv clean install deps

test: deps
	python3 -m pytest tests/

deps:
	pip install pytest

cc:
	git diff > commit.txt

venv:
	python3 -m venv venv && \
	. venv/bin/activate && \
	pip install -r requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	rm -rf build/ dist/

install:
	pip install -e .
