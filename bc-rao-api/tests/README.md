# BC-RAO Backend Test Suite

Comprehensive pytest test suite for the BC-RAO FastAPI backend.

## Overview

This test suite covers the most critical business logic paths in the BC-RAO backend:
- **ISC Gating** - Safety feature preventing risky content in high-sensitivity communities
- **Blacklist Validation** - Content safety through pattern matching
- **Regex Filtering** - Pre-filter to reduce low-quality posts before AI processing
- **Monitoring Service** - Post lifecycle tracking and status management
- **Cost Tracker** - Budget enforcement and usage tracking
- **Error Handling** - Standardized error codes and responses
- **Collection Service** - Reddit post collection with validation

## Test Files

```
tests/
├── conftest.py                    # Shared fixtures and mocks
├── test_isc_gating.py             # ISC gating logic (CRITICAL)
├── test_blacklist_validator.py    # Blacklist pattern matching
├── test_regex_filter.py           # Regex pre-filter for collection
├── test_monitoring_service.py     # Monitoring intervals and status
├── test_cost_tracker.py           # Cost tracking and budget checks
├── test_errors.py                 # Error codes and AppError
└── test_collection_service.py     # Collection validation
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_isc_gating.py
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

### Run tests matching pattern
```bash
pytest -k "test_high_isc"
```

## Test Coverage

### ISC Gating (test_isc_gating.py)
- ✅ Low ISC allows all archetypes
- ✅ High ISC (>7.5) blocks Journey and ProblemSolution
- ✅ High ISC forces zero links
- ✅ New account warm-up mode (Feedback only)
- ✅ Archetype-specific constraints
- ✅ Boundary testing (ISC exactly 7.5)
- ✅ Edge cases (ISC 1.0, 10.0)

### Blacklist Validator (test_blacklist_validator.py)
- ✅ Clean text passes validation
- ✅ Forbidden patterns detected
- ✅ Case-insensitive matching
- ✅ Multiple violations captured
- ✅ Empty pattern list handling
- ✅ Invalid regex pattern handling
- ✅ Word boundary respect
- ✅ Real-world spam detection

### Regex Filter (test_regex_filter.py)
- ✅ Keyword matching increases score
- ✅ Personal pronouns boost relevance
- ✅ Questions boost score
- ✅ Emotional language detection
- ✅ Specific numbers/metrics boost
- ✅ Post length bonus
- ✅ Engagement ratio scoring
- ✅ Rejection criteria (short, removed, link-only)
- ✅ Top N% selection for classification
- ✅ 80% rejection rate targeting

### Monitoring Service (test_monitoring_service.py)
- ✅ Check interval calculation (1h new, 4h established)
- ✅ next_check_at scheduling
- ✅ Status transitions (Ativo → Shadowbanned/Removido)
- ✅ total_checks increment
- ✅ Dashboard statistics
- ✅ 7-day audit classification
- ✅ Success rate calculation

### Cost Tracker (test_cost_tracker.py)
- ✅ Budget check under/over/at cap
- ✅ **Zero cap edge case (BUG-A17 fix)**
- ✅ Billing cycle filtering (current month only)
- ✅ Plan tier differences (trial/starter/growth)
- ✅ Unknown plan defaults to trial
- ✅ Usage recording
- ✅ Usage summary with action breakdown

### Error Handling (test_errors.py)
- ✅ All error codes exist (including DUPLICATE_RESOURCE)
- ✅ AppError creation and attributes
- ✅ Custom status codes
- ✅ Details dictionary support
- ✅ Common error scenarios
- ✅ Default values

### Collection Service (test_collection_service.py)
- ✅ **Subreddit r/ prefix rejection (BUG-A18 fix)**
- ✅ Empty subreddit list error
- ✅ Valid subreddit names accepted
- ✅ Campaign not found handling
- ✅ Access control (wrong user)
- ✅ Retry logic for scraping failures
- ✅ Partial failure handling

## Key Features

### Mocking Strategy
All external dependencies are mocked:
- **Supabase** - Mock client with configurable table data
- **Redis** - In-memory mock with dict storage
- **Apify** - Scraping mocked in collection tests
- **OpenRouter** - LLM calls mocked in inference tests

### No Database Required
Tests use mock Supabase client - no actual database connection needed.

### No Package Installation
Tests are designed to run against the existing codebase without installing additional packages.

## Test Fixtures (conftest.py)

### Mock Clients
- `mock_supabase` - Configurable mock Supabase client
- `mock_redis` - In-memory Redis mock
- `mock_supabase_response` - Factory for creating mock responses

### Test Data
- `test_user_id` - Consistent test user UUID
- `test_campaign_id` - Consistent test campaign UUID
- `mock_campaign` - Sample campaign object
- `mock_profile` - Sample community profile
- `mock_draft` - Sample draft object
- `forbidden_patterns` - Sample blacklist patterns

### Helpers
- `mock_jwt_token` - Mock authentication token

## Critical Bug Fixes Tested

### BUG-A17: Zero Cap Edge Case
**Issue**: Users with zero budget cap (expired plans) could still make API calls.

**Test**: `test_cost_tracker.py::TestZeroCapEdgeCase::test_zero_cap_returns_false`

**Fix Verification**: Zero cap immediately returns `(False, 0.0)` without checking usage.

### BUG-A18: Subreddit r/ Prefix
**Issue**: Subreddit names submitted with "r/" prefix caused Apify scraper failures.

**Test**: `test_collection_service.py::TestSubredditValidation::test_subreddit_with_r_prefix_rejected`

**Fix Verification**: Validation error raised before scraping if any subreddit contains "r/" prefix.

## Parametrized Tests

Many tests use `@pytest.mark.parametrize` for comprehensive coverage:
- ISC gating: All archetypes at various ISC levels
- Blacklist: Different forbidden phrases
- Cost tracking: Various budget thresholds
- Error codes: All error code values

## Best Practices

1. **Test Isolation** - Each test is independent and can run in any order
2. **Descriptive Names** - Test names clearly describe what they verify
3. **Edge Cases** - Boundary conditions and edge cases explicitly tested
4. **Realistic Data** - Tests use realistic post content and scenarios
5. **Mocking** - All external dependencies mocked for speed and reliability

## Adding New Tests

When adding new features, follow this pattern:

```python
class TestNewFeature:
    """Test new feature description."""

    def test_basic_functionality(self):
        """Test the happy path."""
        # Arrange
        # Act
        # Assert

    def test_edge_case(self):
        """Test boundary condition."""
        # Arrange
        # Act
        # Assert

    def test_error_handling(self):
        """Test error scenario."""
        # Arrange
        # Act
        # Assert
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- Fast execution (all mocked)
- No external dependencies
- Deterministic results
- Clear failure messages

## Contributing

When contributing:
1. Write tests for new features
2. Update existing tests if behavior changes
3. Ensure all tests pass before committing
4. Follow existing test structure and naming conventions
5. Document any new fixtures in conftest.py
