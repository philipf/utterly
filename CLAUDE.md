# Utterly Codebase Guide

## Build, Test & Lint Commands
```bash
# Install project in development mode
pip install -e .

# Run all tests 
pytest

# Run a specific test file
pytest tests/test_speaker_mapper.py

# Run a specific test function
pytest tests/test_speaker_mapper.py::test_function_name

# Linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Code Style Guidelines
- **Imports**: Standard library first, third-party second, relative imports last; group by source
- **Naming**: snake_case for functions/variables; prefix private functions with underscore
- **Types**: Use type hints for parameters and return values; use Optional for nullable params
- **Documentation**: Google-style docstrings with Args, Returns, Raises sections
- **Error Handling**: Custom exception classes; catch specific exceptions; detailed error messages
- **Formatting**: 4-space indentation; ~100 char line length; aligned parameters for readability