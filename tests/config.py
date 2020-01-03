from random import randint
import os
import tempfile

test_file_finder_config = {
    "host": "127.0.0.1",
    "remote_dir": tempfile.mkdtemp(),
    "local_dir": tempfile.mkdtemp(),
    "out_dir": os.path.join(tempfile.gettempdir(), "out_dir" + str(randint(10, 9999))),
    "port": 2222,
    "username": "test-user",
    "password": None,
    "no_symlinks": False,
    "hard": False,
    "keyfile": os.path.join("tests", "test_rsa_key"),
    "verbosity": 2,
    "clean": False,
    "hash_function": "sha1",
    "copy": False,
    "req_existing_hostkey": False,
    "no_local_keys": False,
    "no_file_attributes": False,
}
