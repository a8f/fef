import hashlib
import os
import shutil

from .util import create_large_file, create_small_file, file_sha1


def test_small_sha1_move(ssh_server, file_finder):
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
    os.remove(moved_path)
    assert hasher.hexdigest() == true_hash


def test_force_newer(ssh_server, file_finder):
    file_finder.force_newer = True
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
    moved_stat = os.stat(moved_path)
    remote_stat = os.stat(remote_path)
    assert moved_stat.st_atime >= remote_stat.st_atime
    assert moved_stat.st_mtime >= remote_stat.st_mtime
    os.remove(moved_path)


def test_large_sha1_move(ssh_server, file_finder):
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    true_hash = create_large_file(local_path)
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
    os.remove(moved_path)
    assert hasher.hexdigest() == true_hash


def test_multiple_files_sha1(ssh_server, file_finder):
    num_files = 10
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]


def test_extra_remote_files_sha1(ssh_server, file_finder):
    num_files = 10
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files * 2)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files * 2)
    ]
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])
    for i in range(num_files, num_files * 2):
        create_small_file(remote_paths[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]
    for i in range(num_files, num_files * 2):
        assert not os.path.exists(moved_paths[i])


def test_extra_local_files_sha1(ssh_server, file_finder):
    num_files = 10
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files * 2)
    ]
    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]
    for i in range(num_files, num_files * 2):
        create_small_file(local_paths[i])
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])
        if os.path.exists(moved_paths[i]):
            os.remove(moved_paths[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]


def test_local_files_in_subdir_sha1(ssh_server, file_finder):
    """Test for multiple small matching files in different subdirectories on local"""
    num_files = 10
    # Not in subdir for 1/3 of the files
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files // 3)
    ]
    # Single subdirectory for 1/3 of the files
    for i in range(num_files // 3, (num_files * 2) // 3):
        subdir = os.path.join(file_finder.local_path, "subdir" + str(i))
        os.mkdir(subdir)
        local_paths.append(os.path.join(subdir, "test_local_file" + str(i) + ".txt"))
    # Subsubdirectory for 1/3 of the files
    for i in range((num_files * 2) // 3, num_files):
        subdir = os.path.join(file_finder.local_path, "subdir" + str(i))
        os.mkdir(subdir)
        subdir = os.path.join(subdir, "subsubdir" + str(i))
        os.mkdir(subdir)
        local_paths.append(os.path.join(subdir, "test_local_file" + str(i) + ".txt"))
    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]


def test_remote_files_in_subdir_sha1(ssh_server, file_finder):
    num_files = 10
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]

    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]

    # 1/3 in root
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files // 3)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files // 3)
    ]
    # Single subdirectory for 1/3 of the files
    for i in range(num_files // 3, (num_files * 2) // 3):
        subdir = os.path.join(file_finder.remote_path, "subdir" + str(i))
        os.mkdir(subdir)
        remote_paths.append(os.path.join(subdir, "test_remote_file" + str(i) + ".txt"))
        moved_paths.append(
            os.path.join(
                file_finder.out_path,
                "subdir" + str(i),
                "test_remote_file" + str(i) + ".txt",
            )
        )
    # Subsubdirectory for 1/3 of the files
    for i in range((num_files * 2) // 3, num_files):
        subdir = os.path.join(file_finder.remote_path, "subdir" + str(i))
        os.mkdir(subdir)
        subdir = os.path.join(subdir, "subsubdir" + str(i))
        os.mkdir(subdir)
        remote_paths.append(os.path.join(subdir, "test_remote_file" + str(i) + ".txt"))
        moved_paths.append(
            os.path.join(
                file_finder.out_path,
                "subdir" + str(i),
                "subsubdir" + str(i),
                "test_remote_file" + str(i) + ".txt",
            )
        )
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]


def test_files_in_subdir_sha1(ssh_server, file_finder):
    """Multiple small matching files in different subdirectories on remote and local"""
    num_files = 10
    # Not in subdir for 1/3 of the files
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files // 3)
    ]
    # Single subdirectory for 1/3 of the files
    for i in range(num_files // 3, (num_files * 2) // 3):
        subdir = os.path.join(file_finder.local_path, "subdir" + str(i))
        os.mkdir(subdir)
        local_paths.append(os.path.join(subdir, "test_local_file" + str(i) + ".txt"))
    # Subsubdirectory for 1/3 of the files
    for i in range((num_files * 2) // 3, num_files):
        subdir = os.path.join(file_finder.local_path, "subdir" + str(i))
        os.mkdir(subdir)
        subdir = os.path.join(subdir, "subsubdir" + str(i))
        os.mkdir(subdir)
        local_paths.append(os.path.join(subdir, "test_local_file" + str(i) + ".txt"))

    hashes = [create_small_file(local_paths[i]) for i in range(num_files)]
    remote_paths = [
        os.path.join(file_finder.remote_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files // 3)
    ]
    moved_paths = [
        os.path.join(file_finder.out_path, "test_remote_file" + str(i) + ".txt")
        for i in range(num_files // 3)
    ]
    # Single subdirectory for 1/3 of the files
    for i in range(num_files // 3, (num_files * 2) // 3):
        subdir = os.path.join(file_finder.remote_path, "subdir" + str(i))
        os.mkdir(subdir)
        remote_paths.append(os.path.join(subdir, "test_remote_file" + str(i) + ".txt"))
        moved_paths.append(
            os.path.join(
                file_finder.out_path,
                "subdir" + str(i),
                "test_remote_file" + str(i) + ".txt",
            )
        )
    # Subsubdirectory for 1/3 of the files
    for i in range((num_files * 2) // 3, num_files):
        subdir = os.path.join(file_finder.remote_path, "subdir" + str(i))
        os.mkdir(subdir)
        subdir = os.path.join(subdir, "subsubdir" + str(i))
        os.mkdir(subdir)
        remote_paths.append(os.path.join(subdir, "test_remote_file" + str(i) + ".txt"))
        moved_paths.append(
            os.path.join(
                file_finder.out_path,
                "subdir" + str(i),
                "subsubdir" + str(i),
                "test_remote_file" + str(i) + ".txt",
            )
        )
    for i in range(num_files):
        shutil.copyfile(local_paths[i], remote_paths[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]
