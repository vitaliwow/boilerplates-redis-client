.PHONY: format lint check test install-dev clean stage check-format lint-fix fix

# Format code with ruff
format:
	python -m ruff format .

# Check formatting without making changes
check-format:
	python -m ruff format --check .

# Lint code with ruff
lint:
	python -m ruff check .

# Fix linting issues automatically
lint-fix:
	python -m ruff check --fix .

# Run both format check and lint
check: check-format lint

# Run tests
test:
	pytest tests/ -v

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Clean cache and temporary files
makclean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	rm -rf build/ dist/ .coverage htmlcov/

# Format and lint in one command
fix: format lint-fix

# Check code quality, run tests, then stage all changes
stage: check test
	@echo "All checks passed! Staging changes..."
	git add .
	@echo "Changes staged successfully."
