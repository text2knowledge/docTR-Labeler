.PHONY: quality style test  docs-single-version docs
# this target runs checks on all files
quality:
	ruff check .
	mypy labeler/

# this target runs checks on all files and potentially modifies some of them
style:
	ruff format .
	ruff check --fix .

# Run tests for the library
test:
	coverage run -m pytest tests/common/ -rs
	coverage report --fail-under=70 --show-missing
