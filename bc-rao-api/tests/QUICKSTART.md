# Quick Start Guide - BC-RAO Backend Tests

Get up and running with the test suite in under 2 minutes.

---

## TL;DR

```bash
cd bc-rao-api
pytest tests/                    # Run all 167 tests
pytest tests/ -v                 # Verbose output
pytest tests/ --cov=app          # With coverage
```

---

## What's Included

### Test Files (167 tests total)
```
tests/
├── conftest.py                    # Shared fixtures & mocks
├── test_isc_gating.py             # 28 tests - ISC safety (CRITICAL)
├── test_blacklist_validator.py    # 22 tests - Content safety
├── test_regex_filter.py           # 29 tests - Quality filtering
├── test_monitoring_service.py     # 22 tests - Post lifecycle
├── test_cost_tracker.py           # 17 tests - Budget enforcement
├── test_errors.py                 # 31 tests - Error handling
├── test_collection_service.py     # 15 tests - Input validation
├── README.md                      # Full documentation
├── TEST_SUMMARY.md                # Detailed summary
└── QUICKSTART.md                  # This file
```

---

## Prerequisites

```bash
# Already installed with bc-rao-api
pytest>=7.0.0
```

No additional packages needed!

---

## Running Tests

### All Tests
```bash
pytest tests/
```

**Expected output**:
```
======================== test session starts =========================
collected 167 items

tests/test_isc_gating.py ............................          [ 16%]
tests/test_blacklist_validator.py ......................        [ 29%]
tests/test_regex_filter.py .............................        [ 46%]
tests/test_monitoring_service.py ......................         [ 59%]
tests/test_cost_tracker.py .................                   [ 69%]
tests/test_errors.py ...............................            [ 87%]
tests/test_collection_service.py ...............                [100%]

========================= 167 passed in 2.34s ========================
```

---

### Single Test File
```bash
pytest tests/test_isc_gating.py
```

---

### Specific Test
```bash
pytest tests/test_isc_gating.py::TestISCGatingBasics::test_high_isc_blocks_journey
```

---

### With Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # View in browser
```

---

### Verbose Mode
```bash
pytest tests/ -v
```

Shows individual test names as they run.

---

### Run Tests Matching Pattern
```bash
pytest tests/ -k "test_high_isc"      # All tests with "high_isc" in name
pytest tests/ -k "test_zero_cap"      # All tests with "zero_cap"
```

---

## What Gets Tested

### 🔴 Critical Safety (P0)
- **ISC Gating**: Prevents risky content in sensitive communities
- **Blacklist**: Blocks forbidden promotional patterns

### 🟡 Core Logic (P1)
- **Regex Filter**: Quality filtering for post collection
- **Monitoring**: Post lifecycle and status tracking

### 🟢 Infrastructure (P2)
- **Cost Tracker**: Budget enforcement (includes BUG-A17 fix)
- **Errors**: Consistent error handling
- **Collection**: Input validation (includes BUG-A18 fix)

---

## Bug Fixes Verified

### ✅ BUG-A17: Zero Cap Edge Case
**Test**: `test_cost_tracker.py::test_zero_cap_returns_false`

Users with expired plans (cap=0) now immediately blocked.

---

### ✅ BUG-A18: Subreddit r/ Prefix
**Test**: `test_collection_service.py::test_subreddit_with_r_prefix_rejected`

Subreddit names with "r/" prefix now rejected before scraping.

---

## Common Issues

### Import Errors
```bash
# If you see: ModuleNotFoundError: No module named 'app'
# Solution: Run from bc-rao-api directory
cd bc-rao-api
pytest tests/
```

### Missing Dependencies
```bash
# If pytest not found
pip install pytest

# If coverage not found
pip install pytest-cov
```

### Tests Fail
1. Check you're on latest code (after bug fixes)
2. Verify you're in `bc-rao-api/` directory
3. Check Python version (3.11+)
4. Clear pytest cache: `pytest --cache-clear`

---

## Useful Commands

```bash
# Run fastest tests first
pytest tests/ --ff

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Run last failed tests
pytest tests/ --lf

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto

# Generate JUnit XML report
pytest tests/ --junitxml=report.xml

# Show test duration
pytest tests/ --durations=10
```

---

## Next Steps

1. ✅ **Run all tests**: `pytest tests/`
2. 📊 **Check coverage**: `pytest tests/ --cov=app --cov-report=html`
3. 📖 **Read docs**: See `README.md` for full documentation
4. 🔍 **Explore tests**: Look at test files to understand patterns
5. ➕ **Add tests**: Follow existing patterns when adding features

---

## Getting Help

- **Full docs**: `tests/README.md`
- **Detailed info**: `tests/TEST_SUMMARY.md`
- **Bug fixes**: See "Bug Fixes Verified" sections in test files
- **Fixtures**: Check `tests/conftest.py` for available mocks

---

## CI/CD Integration

Add to your pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest tests/ --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

**That's it!** You're ready to run tests. 🚀

Start with: `pytest tests/`
