import hashlib
import os

from .util import LARGE_LINE_COUNT, SMALL_LINE_COUNT, random_lines


def test_small_local_file_sha1_hash(ssh_server, file_finder):
    text = random_lines(SMALL_LINE_COUNT)
    hasher = hashlib.sha1()
    hasher.update(text.encode())
    true_hash = hasher.hexdigest()
    with open("test_text_file.txt", "w") as file:
        file.write(text)
    file_finder.local_hash("test_text_file.txt")
    computed_hash = file_finder.local_hash("test_text_file.txt")
    os.remove("test_text_file.txt")
    assert true_hash == computed_hash


def test_large_local_file_sha1_hash(ssh_server, file_finder):
    text = random_lines(LARGE_LINE_COUNT)
    hasher = hashlib.sha1()
    hasher.update(text.encode())
    true_hash = hasher.hexdigest()
    with open("test_text_file.txt", "w") as file:
        file.write(text)
    file_finder.local_hash("test_text_file.txt")
    computed_hash = file_finder.local_hash("test_text_file.txt")
    os.remove("test_text_file.txt")
    assert true_hash == computed_hash
