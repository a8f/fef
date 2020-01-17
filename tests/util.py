import hashlib
import os
import random
import tempfile
from string import ascii_letters
from typing import Callable

LINE_LENGTH = 1000
SMALL_LINE_COUNT = 10000
LARGE_LINE_COUNT = 100000


default_config = {
    "host": "127.0.0.1",
    "remote_dir": None,
    "local_dir": None,
    "out_dir": None,
    "port": 2222,
    "username": "test-user",
    "password": None,
    "symlinks": False,
    "hard": False,
    "keyfile": os.path.join("tests", "test_rsa_key"),
    "verbosity": 2,
    "clean": False,
    "hash_function": "sha1",
    "copy": False,
    "req_existing_hostkey": False,
    "no_local_keys": False,
    "force_newer": False,
    "log_file": "stdout",
}


def new_config():
    config = default_config.copy()
    config["remote_dir"] = tempfile.mkdtemp()
    config["local_dir"] = tempfile.mkdtemp()
    # Get a valid output directory using mkdtemp then delete it so FileFinder creates it
    out_dir = tempfile.mkdtemp()
    os.rmdir(out_dir)
    config["out_dir"] = out_dir
    return config


def random_lines(num_lines: int) -> str:
    """
    Returns a string of num_lines strings of LINE_LENGTH random characters
    delimited by newlines
    """
    return "\n".join([random.choice(ascii_letters) for i in range(num_lines)])


def file_sha1(filename: str) -> str:
    hasher = hashlib.sha1()
    with open(filename, "rb") as file:
        hasher.update(file.read())
    return hasher.hexdigest()


# Creates file at path containing body and returns hash of body with hash_function
def create_file(path: str, body: str, hash_function: Callable = hashlib.sha1) -> str:
    # Make the file
    if os.path.exists(path):
        raise FileExistsError(path)
    with open(path, "w") as file:
        file.write(body)
    # Compute and return the hash
    hasher = hash_function()
    hasher.update(body.encode())
    return hasher.hexdigest()


# Creates a small file at path and returns the hash of the file's contents
def create_small_file(path: str, hash_function: Callable = hashlib.sha1) -> str:
    return create_file(path, random_lines(SMALL_LINE_COUNT), hash_function)


# Creates a large file at path and returns the hash of the file's contents
def create_large_file(path: str, hash_function: Callable = hashlib.sha1) -> str:
    return create_file(path, random_lines(LARGE_LINE_COUNT), hash_function)
