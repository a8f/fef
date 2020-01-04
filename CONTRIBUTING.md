## Contributing

### Style

Code should be formatted with [Black](https://github.com/psf/black). Comments and string literals should not go over Black's 88 character line limit (autoformatting with Black will not enforce this).

### Testing

[PyTest](https://docs.pytest.org/en/latest/) is used for testing. Tests are located in the `tests/` directory.

To run tests, you will `pytest`, `paramiko`, and a [custom version of `mock-ssh-server`](https://github.com/a8f/mock-ssh-server/). You can install all requirements globally with `pip install -r tests/requirements.txt`.

**Tests should be run while in the top level `fef` directory.** To run all tests, use `pytest`. To run a specific test, use `pytest -q tests/testname.py`.
