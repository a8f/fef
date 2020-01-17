import hashlib
import os
import shutil

from .util import create_small_file, file_sha1


def test_simple_symlink(ssh_server, file_finder):
    file_finder.symlink = True
    file_finder.hardlink = False
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(file_finder.remote_path, "test_remote_file.txt")
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    hasher = hashlib.sha1()
    with open(moved_path, "rb") as file:
        for l in file.readlines():
            hasher.update(l)
    assert hasher.hexdigest() == true_hash
    # Check that symlink was created
    assert os.path.islink(local_path)
    assert os.path.abspath(os.readlink(local_path)) == os.path.abspath(moved_path)


def test_multiple_symlink(ssh_server, file_finder):
    num_files = 10
    file_finder.symlink = True
    file_finder.hardlink = False
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]

    # Create the files to test on
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])

    # Run fef
    file_finder.run()

    # Test
    for i in range(num_files):
        # File was matched and moved successfully
        assert os.path.isfile(moved_paths[i])
        # Correct file was moved
        assert file_sha1(moved_paths[i]) == hashes[i]
        # Check that symlink was created
        assert os.path.islink(local_paths[i])
        assert os.path.abspath(os.readlink(local_paths[i])) == os.path.abspath(
            moved_paths[i]
        )


def test_symlink_in_dir(ssh_server, file_finder):
    file_finder.symlink = True
    file_finder.hardlink = False
    os.mkdir(os.path.join(file_finder.local_path, "subdir"))
    local_path = os.path.join(file_finder.local_path, "subdir", "test_local_file.txt")
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(
        file_finder.remote_path, "subdir", "test_remote_file.txt"
    )
    os.mkdir(os.path.join(file_finder.remote_path, "subdir"))
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "subdir", "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that symlink was created
    assert os.path.islink(local_path)
    assert os.path.abspath(os.readlink(local_path)) == os.path.abspath(moved_path)


def test_symlink_only_remote_in_dir(ssh_server, file_finder):
    file_finder.symlink = True
    file_finder.hardlink = False
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(
        file_finder.remote_path, "subdir", "test_remote_file.txt"
    )
    os.mkdir(os.path.join(file_finder.remote_path, "subdir"))
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "subdir", "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that symlink was created
    assert os.path.islink(local_path)
    assert os.path.abspath(os.readlink(local_path)) == os.path.abspath(moved_path)


def test_symlink_only_local_in_dir(ssh_server, file_finder):
    file_finder.symlink = True
    file_finder.hardlink = False
    os.mkdir(os.path.join(file_finder.local_path, "subdir"))
    local_path = os.path.join(file_finder.local_path, "subdir", "test_local_file.txt")
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(file_finder.remote_path, "test_remote_file.txt")
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that symlink was created
    assert os.path.islink(local_path)
    assert os.path.abspath(os.readlink(local_path)) == os.path.abspath(moved_path)


def test_simple_hardlink(ssh_server, file_finder):
    file_finder.symlink = False
    file_finder.hardlink = True
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(file_finder.remote_path, "test_remote_file.txt")
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that file was created that points to same inode as moved path
    assert os.path.isfile(local_path)
    assert os.stat(local_path).st_ino == os.stat(moved_path).st_ino


def test_hardlink_in_dir(ssh_server, file_finder):
    file_finder.symlink = False
    file_finder.hardlink = True
    local_path = os.path.join(file_finder.local_path, "subdir", "test_local_file.txt")
    os.mkdir(os.path.join(file_finder.local_path, "subdir"))
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(
        file_finder.remote_path, "subdir", "test_remote_file.txt"
    )
    os.mkdir(os.path.join(file_finder.remote_path, "subdir"))
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "subdir", "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that file was created that points to same inode as moved path
    assert os.path.isfile(local_path)
    assert os.stat(local_path).st_ino == os.stat(moved_path).st_ino


def test_hardlink_only_remote_in_dir(ssh_server, file_finder):
    file_finder.symlink = False
    file_finder.hardlink = True
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(
        file_finder.remote_path, "subdir", "test_remote_file.txt"
    )
    os.mkdir(os.path.join(file_finder.remote_path, "subdir"))
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "subdir", "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that file was created that points to same inode as moved path
    assert os.path.isfile(local_path)
    assert os.stat(local_path).st_ino == os.stat(moved_path).st_ino


def test_hardlink_only_local_in_dir(ssh_server, file_finder):
    file_finder.symlink = False
    file_finder.hardlink = True
    local_path = os.path.join(file_finder.local_path, "subdir", "test_local_file.txt")
    os.mkdir(os.path.join(file_finder.local_path, "subdir"))
    true_hash = create_small_file(local_path)
    remote_path = os.path.join(file_finder.remote_path, "test_remote_file.txt")
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "test_remote_file.txt")
    file_finder.run()
    # File was matched and moved successfully
    assert len(os.listdir(file_finder.out_path)) == 1
    assert os.path.isfile(moved_path)
    # Correct file was moved
    assert file_sha1(moved_path) == true_hash
    # Check that file was created that points to same inode as moved path
    assert os.path.isfile(local_path)
    assert os.stat(local_path).st_ino == os.stat(moved_path).st_ino
