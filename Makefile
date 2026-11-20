# Makefile

.PHONY: all format check validate test test-cov test-integration test-all vulture complexity xenon bandit pyright fix reformat-ruff fix-ruff mutation

# Default target: runs format and check
all: validate test

# Format the code using ruff
format:
	uv run ruff format --check --diff .

reformat-ruff:
	uv run ruff format .

# Check the code using ruff
check:
	uv run ruff check .

fix-ruff:
	uv run ruff check . --fix

fix: reformat-ruff fix-ruff
	@echo "Updated code."

test:
	uv run pytest tests/unit

test-cov:
	uv run pytest tests/unit --cov --cov-report=xml --cov-report=term-missing

test-integration:
	uv run pytest tests/integration -v --timeout=120

test-all: test-cov
	uv run pytest tests/integration -v --timeout=120

# Mutation testing (mutates twitcharchiver/, runs the unit suite per mutant)
mutation:
	uv run mutmut run
	uv run mutmut results

vulture:
	uv run vulture . --exclude .venv,tests,mutants --make-whitelist

complexity:
	uv run radon cc . -a -nc

xenon:
	uv run xenon -b D -m B -a B .

bandit:
	uv run bandit -c pyproject.toml -r .

pyright:
	uv run pyright

# Validate the code (format + check + quality)
validate: format check complexity bandit pyright vulture
	@echo "Validation passed. Your code is ready to push."
