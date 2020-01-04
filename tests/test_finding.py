import hashlib
import os
import shutil
from .util import random_lines, SMALL_LINE_COUNT, LARGE_LINE_COUNT


def test_small_sha1_move(ssh_server, file_finder):
    text = random_lines(SMALL_LINE_COUNT)
    hasher = hashlib.sha1()
    hasher.update(text.encode())
    true_hash = hasher.hexdigest()
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    with open(local_path, "w") as file:
        file.write(text)
    print(os.path.exists(local_path))
    print(os.listdir(file_finder.local_path + "/"))
    remote_path = os.path.join(file_finder.remote_path, "test_remote_file.txt")
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "test_remote_file.txt")
    if os.path.exists(moved_path):
        os.remove(moved_path)
    file_finder.run()
    # File was matched and moved successfully
    assert os.path.isfile(moved_path)
    # Correct file was moved
    hasher = hashlib.sha1()
    with open(moved_path, "rb") as file:
        for l in file.readlines():
            hasher.update(l)
    os.remove(moved_path)
    assert hasher.hexdigest() == true_hash
