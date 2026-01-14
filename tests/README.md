# Testing Documentation

This directory contains unit tests for the QuantAgentic API, covering CrewAI tools, service layer methods, and utilities.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_nws_polling_tool.py       # Tests for NWS polling tool
└── test_event_service.py          # Tests for EventService methods
```

## Running Tests

### Prerequisites

Make sure you have installed all dependencies:
```bash
pip install -r requirements.txt
```

### Basic Commands

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_nws_polling_tool.py
pytest tests/test_event_service.py
pytest tests/test_event_confirmation_service.py
pytest tests/test_event_creation_processor.py
```

**Run specific test class:**
```bash
pytest tests/test_nws_polling_tool.py::TestNWSPollingTool
pytest tests/test_event_service.py::TestCreateEventFromAlert
pytest tests/test_event_service.py::TestUpdateEventFromAlert
```

**Run specific test method:**
```bash
pytest tests/test_nws_polling_tool.py::TestNWSPollingTool::test_async_poll_success
pytest tests/test_event_service.py::TestCreateEventFromAlert::test_create_event_from_alert_success
```

### Advanced Options

**Run with coverage report:**
```bash
pytest --cov=app --cov-report=html
```
This generates an HTML coverage report in `htmlcov/index.html`.

**Run with coverage in terminal:**
```bash
pytest --cov=app --cov-report=term
```

**Stop on first failure:**
```bash
pytest -x
```

**Run tests in parallel (requires pytest-xdist):**
```bash
pytest -n auto
```

**Show print statements:**
```bash
pytest -s
```

**Run only tests matching a pattern:**
```bash
pytest -k "polling"      # Run all polling-related tests
pytest -k "event_service"  # Run all event service tests
pytest -k "create"       # Run all tests with "create" in the name
```

## Test Coverage

### Current Test Files

The test suite includes **19 test files** covering all major components:

1. **test_nws_polling_tool.py** - NWS API polling functionality
2. **test_event_service.py** - Event service facade methods
3. **test_event_create_service.py** - Event creation logic
4. **test_event_update_service.py** - Event update logic
5. **test_event_read_service.py** - Event read operations
6. **test_event_service_facade.py** - Service facade delegation
7. **test_event_creation_processor.py** - Event creation processor (includes FWW filtering and HWW validation)
8. **test_event_completion_service.py** - Event completion logic
9. **test_event_confirmation_service.py** - Event confirmation service (LSR processing, smart polling)
10. **test_event_confirmation_tool.py** - Event confirmation tool (geospatial validation)
11. **test_location.py** - Location utilities (FIPS parsing, coordinate extraction)
12. **test_nws_alert_parser.py** - NWS alert parsing utilities
13. **test_datetime_utils.py** - Datetime utility functions
14. **test_arcgis_wildfire_parser.py** - ArcGIS wildfire data parser
15. **test_wildfire_utils.py** - Wildfire utility functions
16. **test_wildfire_crud_service.py** - Wildfire CRUD operations
17. **test_wildfire_processor.py** - Wildfire processing logic
18. **test_drought_crud_service.py** - Drought CRUD operations
19. **test_drought_service.py** - Drought service logic

**Total: 283 tests** (all passing ✅)

### Key Test Coverage Areas

- **Event Management**: Creation, updates, completion, confirmation, deactivation
- **Event Filtering**: FWW (Fire Weather Warning) filtering
- **Wind Validation**: HWW (High Wind Warning) validation with configurable threshold
- **Event Confirmation**: LSR processing, smart polling, geospatial validation
- **Wildfire Processing**: ArcGIS API integration, lifecycle management
- **Drought Processing**: US Drought Monitor integration, county-level tracking
- **Location Utilities**: FIPS codes, coordinate extraction, polygon handling
- **NWS Integration**: Alert polling, parsing, VTEC key generation

## Test Fixtures

Fixtures are defined in `conftest.py`:

- `mock_state`: Mock state object for testing
- `mock_nws_client`: Mock NWS client for async testing
- `sample_nws_alert`: Sample NWS alert data structure

## Writing New Tests

### Test File Structure

```python
"""
Unit tests for YourTool.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.crews.tools.your_tool import YourTool


class TestYourTool:
    """Test cases for YourTool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return YourTool()
    
    def test_basic_functionality(self, tool):
        """Test basic tool functionality."""
        result = tool._run(param="value")
        assert "expected" in result
    
    @patch('app.crews.tools.your_tool.SomeDependency')
    def test_with_mock(self, mock_dependency, tool):
        """Test with mocked dependencies."""
        mock_dependency.return_value = "mocked"
        result = tool._run()
        assert result == "expected"
```

### Best Practices

1. **Use descriptive test names**: `test_poll_nws_alerts_success` not `test_poll`
2. **One assertion per test**: Focus each test on one behavior
3. **Use fixtures**: Share common setup code via fixtures
4. **Mock external dependencies**: Don't make real API calls in tests
5. **Test edge cases**: Include error conditions and boundary cases
6. **Use async mocks**: For async functions, use `AsyncMock`

## Continuous Integration

Tests are configured to run automatically in GitHub Actions on PR commits.

### Pytest Configuration

The `pytest.ini` file configures:
- Test discovery patterns
- Output verbosity
- Async test mode
- Warning filters

### GitHub Actions Integration

To set up GitHub Actions, create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v
```

## Debugging Tests

### Run with PDB (Python Debugger)

```bash
pytest --pdb
```
Drops into debugger on failure.

### Show local variables on failure

```bash
pytest -l
```

### Run with detailed traceback

```bash
pytest --tb=long
```

### Run with no traceback

```bash
pytest --tb=no
```

## Common Issues

### Import Errors

If you see import errors, make sure:
1. Virtual environment is activated
2. All dependencies are installed: `pip install -r requirements.txt`
3. You're running from the project root directory

### Async Test Issues

For async tests, ensure:
- Using `pytest-asyncio` (included in requirements)
- Using `AsyncMock` for async functions
- Using `@pytest.mark.asyncio` decorator if needed

### Mock Not Working

If mocks aren't working:
- Check the import path matches exactly
- Use `patch` with the full module path
- Ensure you're patching before the import happens

## Test Data

Sample test data is provided in `conftest.py`:
- `sample_nws_alert`: Complete NWS alert structure
- Mock state objects with realistic data

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Aim for >80% code coverage
4. Update this README if adding new test patterns

