# Run linter

lint:
	@echo "Running linter"
	@ruff check --select I --fix .

mypy:
	@echo "Running mypy"
	@mypy .

test:
	@echo "Running tests"
	@python -m pytest -vv tests
