# Makefile

.PHONY: all format check validate test test-cov test-integration test-all vulture complexity xenon bandit pyright fix reformat-ruff fix-ruff

# Default target: runs format and check
all: validate test

# Format the code using ruff
format:
	ruff format --check --diff .

reformat-ruff:
	ruff format .

# Check the code using ruff
check:
	ruff check .

fix-ruff:
	ruff check . --fix

fix: reformat-ruff fix-ruff
	@echo "Updated code."

test:
	pytest tests/unit

test-cov:
	pytest tests/unit --cov --cov-report=xml --cov-report=term-missing

test-integration:
	pytest tests/integration -v --timeout=120

test-all: test-cov
	pytest tests/integration -v --timeout=120

vulture:
	vulture . --exclude .venv,tests --make-whitelist

complexity:
	radon cc . -a -nc

xenon:
	xenon -b D -m B -a B .

bandit:
	bandit -c pyproject.toml -r .

pyright:
	pyright

# Validate the code (format + check + quality)
validate: format check complexity bandit pyright vulture
	@echo "Validation passed. Your code is ready to push."
