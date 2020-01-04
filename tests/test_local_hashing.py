import hashlib
import os
import random
from string import ascii_letters

LINE_LENGTH = 1000
SMALL_LINE_COUNT = 10000
LARGE_LINE_COUNT = 100000


def random_lines(num_lines: int) -> str:
    """
    Returns a string of num_lines strings of LINE_LENGTH random characters
    delimited by newlines
    """
    return "\n".join([random.choice(ascii_letters) for i in range(num_lines)])


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
