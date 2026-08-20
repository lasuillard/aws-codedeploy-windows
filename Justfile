_default:
    just --list

# Install deps and tools
install:
    uv python install
    uv sync --frozen

# Update deps and tools
update:
    pre-commit autoupdate
    uv sync --upgrade

alias up := update

# =============================================================================
# Development
# =============================================================================

# Run all checks
ci: (format "yes") lint test

# Autoformat code
[arg("check", long="check", value="yes")]
format check="no":
    uv run ruff format {{ if check == "yes" { "--check" } else { "" } }} .

alias fmt := format

# Run all linters
lint:
    uv run ruff check .
    uv run ty check .

# Run all tests
test:
    uv run pytest

# Apply autofixes
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Run development server
run:
    uv run fastapi dev

# =============================================================================
# Utility
# =============================================================================

# Remove temporary files
clean:
    rm --recursive --force \
        .mypy_cache/ \
        .pytest_cache/ \
        .ruff_cache/ \
        htmlcov/ \
        coverage.xml \
        junit.xml
    find . -path '*/__pycache__*' -delete
    find . -path "*.log*" -delete
