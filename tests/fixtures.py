from file_finder import FileFinder
import mockssh
import os
from pytest import yield_fixture
from .config import test_file_finder_config as config


@yield_fixture()
def ssh_server_with_keyfile():
    with mockssh.Server(
        {config["username"]: config["keyfile"]},
        host=config["host"],
        port=config["port"],
    ) as s:
        yield s


@yield_fixture()
def file_finder():
    yield FileFinder(**config)
