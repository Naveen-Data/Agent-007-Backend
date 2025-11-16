# Test Suite Documentation

This document describes the test module organization for Agent 007 Backend.

## Test Structure

The test suite is organized into categorized modules following Python packaging standards:

```
tests/
├── __init__.py                     # Common test fixtures and configuration
├── pytest.ini                     # Test configuration and settings
├── unit/                          # Unit tests for individual components
│   ├── __init__.py               
│   ├── test_agent_service.py      # Agent service unit tests
│   ├── test_basic_functionality.py # Basic import and health tests
│   ├── test_llm_service.py        # LLM service unit tests
│   └── test_tool_service.py       # Tool service unit tests
├── integration/                   # Integration tests for service interactions
│   ├── __init__.py
│   └── test_service_integration.py # Service integration tests
└── functional/                    # End-to-end functional tests
    ├── __init__.py
    ├── test_agent_functionality.py # Complete agent functionality tests
    └── test_smoke.py              # Quick smoke tests
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Single classes, functions, or modules
- **Mocking**: Heavy use of mocks to isolate dependencies
- **Examples**: Agent service initialization, LLM service methods, tool functionality

### Integration Tests (`tests/integration/`)
- **Purpose**: Test interactions between services and components
- **Scope**: Multiple components working together
- **Mocking**: Limited mocking, focus on real interactions
- **Examples**: Agent service with tool service, dependency injection

### Functional Tests (`tests/functional/`)
- **Purpose**: End-to-end testing of complete workflows
- **Scope**: Full system behavior from user perspective
- **Mocking**: Minimal mocking, test real system behavior
- **Examples**: Complete agent conversations, mode comparisons, error scenarios

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Functional tests only
python -m pytest tests/functional/ -v
```

### Run Specific Test Files
```bash
python -m pytest tests/unit/test_agent_service.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Test Configuration

### pytest.ini
- **Test Discovery**: Configured to find tests in `tests/` directory
- **Warning Suppression**: Filters out external library warnings
- **Async Support**: Configured for asyncio testing
- **Markers**: Defined for test categorization

### Common Fixtures (tests/__init__.py)
- **Test Database**: In-memory database for isolated tests
- **Mock Services**: Reusable mock implementations
- **Test Data**: Common test fixtures and data

## Test Best Practices

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### Test Organization
- Group related tests in classes
- Use setup/teardown methods for test preparation
- Keep tests focused and atomic
- Use parametrized tests for multiple scenarios

### Mocking Guidelines
- Mock external dependencies in unit tests
- Use real implementations in integration tests
- Prefer dependency injection for testability
- Mock at the appropriate level (not too deep)

### Async Testing
- Use `@pytest.mark.asyncio` for async tests
- Use `AsyncMock` for async method mocking
- Ensure proper await syntax in test assertions

## Test Markers

The following markers are available for test categorization:

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests for service interactions
- `@pytest.mark.functional`: Functional tests for end-to-end scenarios
- `@pytest.mark.smoke`: Quick smoke tests for basic functionality
- `@pytest.mark.asyncio`: Tests using asyncio

### Running Tests by Marker
```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Run smoke tests for quick validation
python -m pytest -m smoke
```

## Continuous Integration

The test suite is designed to run efficiently in CI environments:

- **Fast Execution**: Unit tests run quickly with mocked dependencies
- **Parallel Execution**: Tests can run in parallel where appropriate
- **Clear Output**: Structured logging and clear assertions for debugging
- **Warning Suppression**: Clean output without external library warnings

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the virtual environment is activated and dependencies installed
2. **Async Test Failures**: Check that async tests use `@pytest.mark.asyncio`
3. **Mock Issues**: Verify that async methods use `AsyncMock`
4. **Path Issues**: Tests should be run from the project root directory

### Debug Mode
```bash
# Run with detailed output
python -m pytest tests/ -v -s

# Run with debugging on failure
python -m pytest tests/ --pdb

# Run specific failing test
python -m pytest tests/path/to/test.py::TestClass::test_method -v -s
```

## Coverage Reports

Generate coverage reports to ensure comprehensive testing:

```bash
# Terminal coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing

# HTML coverage report
python -m pytest tests/ --cov=app --cov-report=html

# XML coverage report (for CI)
python -m pytest tests/ --cov=app --cov-report=xml
```

Coverage reports help identify untested code paths and ensure comprehensive test coverage across the application.