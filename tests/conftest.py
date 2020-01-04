from file_finder import FileFinder
import mockssh
from pytest import yield_fixture, fixture
from .config import default_config, new_config


@yield_fixture(scope="package")
def ssh_server():
    with mockssh.Server(
        {default_config["username"]: default_config["keyfile"]},
        host=default_config["host"],
        port=default_config["port"],
    ) as s:
        yield s


@fixture()
def file_finder():
    config = new_config()
    return FileFinder(**config)
