import hashlib
import os
import shutil

from .util import LARGE_LINE_COUNT, SMALL_LINE_COUNT, file_sha1, random_lines


def test_small_sha1_move(ssh_server, file_finder):
    """Single small matching file"""
    text = random_lines(SMALL_LINE_COUNT)
    hasher = hashlib.sha1()
    hasher.update(text.encode())
    true_hash = hasher.hexdigest()
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    with open(local_path, "w") as file:
        file.write(text)
    remote_path = os.path.join(file_finder.remote_path, "test_remote_file.txt")
    shutil.copyfile(local_path, remote_path)
    moved_path = os.path.join(file_finder.out_path, "test_remote_file.txt")
    print(moved_path)
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


def test_large_sha1_move(ssh_server, file_finder):
    """Single large matching file"""
    text = random_lines(LARGE_LINE_COUNT)
    hasher = hashlib.sha1()
    hasher.update(text.encode())
    true_hash = hasher.hexdigest()
    local_path = os.path.join(file_finder.local_path, "test_local_file.txt")
    with open(local_path, "w") as file:
        file.write(text)
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
    """Multiple small matching files"""
    num_files = 10
    text = [random_lines(SMALL_LINE_COUNT) for i in range(num_files)]
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    hashes = []
    for i in range(num_files):
        hasher = hashlib.sha1()
        hasher.update(text[i].encode())
        hashes.append(hasher.hexdigest())
        with open(local_paths[i], "w") as file:
            file.write(text[i])
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
    """Multiple small matching files and some files which are only on remote"""
    num_files = 10
    text = [random_lines(SMALL_LINE_COUNT) for i in range(num_files * 2)]
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]
    hashes = []
    for i in range(num_files):
        hasher = hashlib.sha1()
        hasher.update(text[i].encode())
        hashes.append(hasher.hexdigest())
        with open(local_paths[i], "w") as file:
            file.write(text[i])
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
        with open(remote_paths[i], "w") as file:
            file.write(text[i])
    file_finder.run()
    assert len(os.listdir(file_finder.out_path)) == num_files
    for i in range(num_files):
        assert os.path.isfile(moved_paths[i])
        assert file_sha1(moved_paths[i]) == hashes[i]
    for i in range(num_files, num_files * 2):
        assert not os.path.exists(moved_paths[i])


def test_extra_local_files_sha1(ssh_server, file_finder):
    """Multiple small matching files and some files which are only on local"""
    num_files = 10
    text = [random_lines(SMALL_LINE_COUNT) for i in range(num_files * 2)]
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files * 2)
    ]
    hashes = []
    for i in range(num_files):
        hasher = hashlib.sha1()
        hasher.update(text[i].encode())
        hashes.append(hasher.hexdigest())
        with open(local_paths[i], "w") as file:
            file.write(text[i])
    for i in range(num_files, num_files * 2):
        with open(local_paths[i], "w") as file:
            file.write(text[i])
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
    """Multiple small matching files in different subdirectories on local"""
    num_files = 10
    text = [random_lines(SMALL_LINE_COUNT) for i in range(num_files)]
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
    hashes = []
    for i in range(num_files):
        hasher = hashlib.sha1()
        hasher.update(text[i].encode())
        hashes.append(hasher.hexdigest())
        with open(local_paths[i], "w") as file:
            file.write(text[i])
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
    """Multiple small matching files in different subdirectories on remote"""
    num_files = 10
    text = [random_lines(SMALL_LINE_COUNT) for i in range(num_files)]
    local_paths = [
        os.path.join(file_finder.local_path, "test_local_file" + str(i) + ".txt")
        for i in range(num_files)
    ]

    hashes = []
    for i in range(num_files):
        hasher = hashlib.sha1()
        hasher.update(text[i].encode())
        hashes.append(hasher.hexdigest())
        with open(local_paths[i], "w") as file:
            file.write(text[i])

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
    text = [random_lines(SMALL_LINE_COUNT) for i in range(num_files)]
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

    hashes = []
    for i in range(num_files):
        hasher = hashlib.sha1()
        hasher.update(text[i].encode())
        hashes.append(hasher.hexdigest())
        with open(local_paths[i], "w") as file:
            file.write(text[i])

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
