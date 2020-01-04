## Contributing

### Style

Code should be formatted with [Black](https://github.com/psf/black). Comments and string literals should not go over Black's 88 character line limit (autoformatting with Black will not enforce this).

### Testing

[PyTest](https://docs.pytest.org/en/latest/) is used for testing. Any additional features should have new tests added to ensure their continued functionality. All tests should be located in the `tests/` directory. **Tests should be run while in the top level `fef` directory.** To run all tests, use `pytest`. To run a specific test, use `pytest -q tests/testname.py`.
