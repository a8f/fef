"""
fef: move existing files to match remote server's file structure
Copyright (C) 2019 Alexander French (http://github.com/a8f)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from ast import literal_eval
from getpass import getpass
import hashlib
from io import BytesIO
import os.path
import subprocess
from socket import gaierror
import sys
from types import MethodType
from typing import Optional, Dict, List, Tuple, Callable, Set

import paramiko


class FileFinder:
    def __init__(
        self,
        host: str,
        remote_dir: str,
        local_dir: str,
        port: int,
        username: str,
        out_dir: str,
        no_symlinks: bool,
        hard: bool,
        keyfile: str,
        password: str,
        verbosity: bool,
        clean: bool,
        hash_function: str,
        copy: bool,
        req_existing_hostkey: bool,
        no_local_keys: bool,
        no_file_attributes: bool,
    ):
        """
        Initialize class attributes, prompting the user for a password if required,
        and connect to the provided host
        :raises ValueError if one of the arguments is invalid
        """

        """Parse username and host/port if provided"""
        split_at = host.split("@")
        if len(split_at) == 1:
            split_colon = split_at[0].split(":")
            # Windows whoami is of the form DOMAIN\USER so get just the username
            if sys.platform.startswith("win"):
                self.username = subprocess.getoutput("whoami").split("\\")[1]
            else:
                self.username = subprocess.getoutput("whoami")
        elif len(split_at) == 2:
            split_colon = split_at[1].split(":")
            self.username = split_at[0]
        else:
            raise ValueError("Invalid host " + host)
        # Get port from hostname and actual hostname
        if len(split_colon) == 1:
            self.hostname = split_colon[0]
        elif len(split_colon) == 2:
            self.hostname = split_colon[0]
            self.port = int(split_colon[1])
        else:
            raise ValueError("Invalid host " + host)

        """Handle legacy-style username and port, overwriting values parsed from host"""
        if port:
            self.port = port
        if username:
            self.username = username

        if not hasattr(self, "port"):
            self.port = 22

        if not os.path.isdir(local_dir):
            raise ValueError("Local directory " + local_dir + " doesn't exist")
        self.local_path = os.path.abspath(local_dir)

        """Remote directory (to be validated on connecting)"""
        self.remote_path = remote_dir

        """Out dir"""
        # TODO allow continuing even if output directory already exists
        if out_dir:
            if os.path.isdir(out_dir):
                raise ValueError(
                    "Directory " + os.path.abspath(out_dir) + " already exists."
                    " Move it or specify an output path with -o"
                )
            self.out_path = os.path.abspath(out_dir)
        else:
            split_remote_dir = remote_dir.split("/")
            if len(split_remote_dir) < 2:
                raise ValueError("Invalid remote file path " + remote_dir)
            remote_top_dir = split_remote_dir[-2]
            if os.path.exists(os.path.join(os.path.curdir, remote_top_dir)):
                raise ValueError(
                    "Directory "
                    + os.path.join(os.path.curdir, remote_top_dir)
                    + " already exists."
                    " Move it or specify an output path with -o"
                )
            self.out_path = os.path.abspath(
                os.path.join(os.path.curdir, remote_top_dir)
            )

        """Link options (hard/soft)"""
        self.symlink = not (hard or no_symlinks)
        self.hardlink = hard

        """Authentication"""
        if keyfile:
            if not os.path.isfile(keyfile):
                raise ValueError("Keyfile " + keyfile + " doesn't exist")
            self.keyfile = os.path.abspath(keyfile)
            self.password = None
        else:
            self.keyfile = None
            self.password = password

        """Hashing"""
        self.hash_method = hash_function.lower()
        try:
            self.set_local_hash_func(getattr(hashlib, hash_function))
        except AttributeError:
            raise ValueError("Unsupported hash function " + hash_function)

        """Remaining options"""
        self.verbosity = verbosity
        self.clean = clean
        self.use_local_keys = not no_local_keys
        self.existing_hostkey = req_existing_hostkey
        self.copy_file_attributes = not no_file_attributes
        # TODO add option to set these
        # Max #bytes of file to read into memory at once
        self.read_size = 2 ** 16  # 64k
        self.remote_read_size = 2 ** 16  # 64k

        """Connect to the remote server"""
        connect_result = self.connect()
        if connect_result:
            raise ValueError(connect_result)
        try:
            self.sftp.chdir(self.remote_path)
        except IOError:
            raise ValueError(
                'Directory "' + self.remote_path + "\" doesn't exist on the server"
            )
        # Check that both machines support the hash function
        supported = self.remote_supported_hash_functions()
        if self.hash_method not in supported:
            raise ValueError(
                "Remote server does not support {}. Hash methods supported by both\
                machines are: {}".format(
                    self.hash_method,
                    ", ".join(
                        [m for m in hashlib.algorithms_available if m in supported]
                    ),
                )
            )

        # Make hashing script if possible
        script = self.create_hash_script()
        if script is None:
            self.remote_hash = self.remote_hash_command_line
        else:
            self.set_remote_hash_function_to_script(script)

        """Dicts for tracking local file hashes"""
        # First is a dict of filesize->paths for all files of a certain size
        # so that we only compute hashes of files that may actually be a match
        # (since they should have the same size if they hash to the same value)
        self.file_sizes = self.generate_filesize_map()
        # Then a dict of path->hash which stores the actual hashes for each file
        # (computed ad hoc during self.run())
        self.file_hashes = {}

    def generate_filesize_map(self) -> Dict[int, List[str]]:
        sizes = {}
        for root, _, files in os.walk(self.local_path):
            for file in files:
                size = os.path.getsize(os.path.join(root, file))
                if size in sizes:
                    sizes[size].append(os.path.join(root, file))
                else:
                    sizes[size] = [os.path.join(root, file)]
        return sizes

    def set_local_hash_func(self, hash_function: Callable) -> None:
        """
        Sets self.local_hash to a unary function that opens a file and
        hashes its contents with hash_function
        """
        # Create hash function
        def local_hash(self, filename: str) -> str:
            hasher = hash_function()
            with open(filename, "rb") as file:
                while True:
                    data = file.read(self.read_size)
                    if not data:
                        return hasher.hexdigest()
                    hasher.update(data)

        # Bind function to this self.local_hash
        self.local_hash = MethodType(local_hash, self)

    def remote_path_join(*parts) -> str:
        """Joins parts using the remote's path separator"""
        # TODO support Windows servers by getting correct separator in init
        if len(parts) == 1:
            return parts
        path = ""
        for p in parts[:-1]:
            path += "/" + p.lstrip("/")
        return path

    def remote_supported_hash_functions(self) -> Set[str]:
        """
        Returns hashlib.algorithms_available on the remote server
        """
        _, result, _ = self.ssh.exec_command(
            """python3 -c "from hashlib import algorithms_available
print(algorithms_available)" """
        )
        return literal_eval(result.read().decode())

    def log(self, msg, **kwargs) -> None:
        """
        Log a message to stdout if verbosity > 1
        """
        # TODO support log files
        if self.verbosity > 1:
            print(msg, **kwargs)

    def create_hash_script(self) -> Optional[str]:
        """
        Creates hash script in remote_path which takes a filename as an argument
        Returns the name of the hash script in remote_dir or None if unable to
        create the script
        """
        # Find filename that doesn't exist
        # TODO handle not having read permissions
        exists = True
        try:
            self.sftp.stat(self.remote_path_join(self.remote_path, "/hash.py"))
        except IOError:
            exists = False
        suffix = 0
        while exists:
            try:
                self.sftp.stat(
                    self.remote_path_join(self.remote_path, "/hash", str(suffix), ".py")
                )
            except IOError:
                exists = False
        filename = self.remote_path_join(self.remote_path, "/hash", str(suffix), ".py")
        # TODO handle not having write permissions
        self.sftp.putfo(BytesIO(self.get_hash_script_body().encode()), filename)
        return filename

    def get_hash_script_body(self) -> str:
        """
        Returns a string of the contents of the hash script file to put
        on the remote server
        """
        return """from hashlib import {}
from sys import argv
hasher = {}()
with open(argv[1], 'rb') as file:
    while True:
        data = file.read({})
        if not data:
            print(hasher.hexdigest())
            break
        hasher.update(data)""".format(
            self.hash_method, self.hash_method, self.remote_read_size,
        )

    def connect(self) -> Optional[str]:
        """
        Connect to self.host using self.username and self.keyfile/password
        If self.keyfile and self.password are None and there is no key found through
        the SSH agent or in ~/.ssh then prompts the user for a password to
        save to self.password and connect with
        :return error message on connection failure or None on success
        """
        self.log(
            "Connecting to %s:%d as %s" % (self.hostname, self.port, self.username),
            end=" ",
        )
        self.ssh = paramiko.SSHClient()
        if self.existing_hostkey:
            self.log("(rejecting servers whose keys are not known)", end=" ")
        self.ssh.set_missing_host_key_policy(
            paramiko.RejectPolicy if self.existing_hostkey else paramiko.AutoAddPolicy
        )
        # TODO prompt user for passphrase if key is encrypted with one
        try:
            if self.keyfile:
                self.log("using keyfile " + self.keyfile)
                self.ssh.connect(
                    self.hostname, self.port, self.username, key_filename=self.keyfile
                )
            elif self.password:
                self.log("using password passed with --password")
                self.ssh.connect(
                    self.hostname, self.port, self.username, password=self.password
                )
            else:
                # If no password then first try connecting using existing keyfiles
                if self.use_local_keys:
                    try:
                        self.ssh.connect(
                            self.hostname,
                            self.port,
                            self.username,
                            allow_agent=True,
                            look_for_keys=True,
                        )
                        self.log("using machine's stored keys")
                    except paramiko.ssh_exception.SSHException:
                        pass
                    except gaierror as e:
                        return str(e) + " (" + self.hostname + ")"
                # Failed to authenticate with keyfiles so prompt for password
                self.log("using password from prompt")
                self.password = getpass(
                    "Password for {}@{}:{}: ".format(
                        self.username, self.hostname, self.port
                    )
                )
                self.ssh.connect(
                    self.hostname, self.port, self.username, password=self.password
                )
        except (
            paramiko.ssh_exception.AuthenticationException,
            paramiko.ssh_exception.SSHException,
        ) as e:
            return str(e)
        except gaierror as e:
            return str(e) + " (" + self.hostname + ")"
        self.sftp = self.ssh.open_sftp()

    def set_remote_hash_function_to_script(self, script_remote_path: str) -> None:
        # Create hash function
        def remote_hash(self, filename: str) -> str:
            _, result, _ = self.ssh.exec_command(
                "python3 " + script_remote_path + " " + filename
            )
            return result.read().decode().lstrip().rstrip()

        # Bind function to self.remote_hash
        self.remote_hash = MethodType(remote_hash, self)

    def run(self) -> bool:
        """
        Do the file finding/moving
        Returns True on success
        On failure, prints error messages and returns False
        """
        remote_files = self.get_remote_filenames()
        # Dict of (new file path -> (current file path, remote file stat))
        # (computed in entirety before actually modifying any data)
        # This is a dict instead of a list of tuples so we can validate in O(n) later
        files_to_move = {}

        if not os.path.isdir(self.out_path):
            os.mkdir(self.out_path)

        for rpath, rfile in remote_files:
            stat = self.sftp.stat(os.path.join(rpath, rfile))
            same_size = self.file_sizes.get(stat.st_size)
            if same_size is None:
                continue
            rhash = self.remote_hash(rpath, rfile)
            # TODO handle duplicate files
            for f in same_size:
                if self.local_hash(f) == rhash:
                    self.log(
                        "Matched file " + f + " with remote file " + rpath + "/" + rfile
                    )
                    files_to_move[self.local_path_from_remote(rpath)] = (f, stat)

        # TODO Check for case where a file will be moved to a location that is actually
        # a directory before modifying any data. This can only happen if the remote
        # has a directory and a file in the same location with the same name
        for new_path, (old_path, stat) in files_to_move.items():
            cur = ""
            # TODO make sure this works with windows paths (drive letter)
            for d in new_path.split(os.path.sep):
                cur = os.path.join(cur, d)
                if cur in files_to_move:
                    print(
                        "Consistency error. Cannot have a file and directory with the"
                        " same name and location ("
                        " {} should become {} but {} should become {})".format(
                            files_to_move[cur][0], cur, old_path, new_path
                        )
                    )

        # Actually move the files
        for new_path, (old_path, stat) in files_to_move:
            self.move_file(old_path, new_path)
            # TODO add an option to specify what parts of stat to copy
            # TODO copy whatever parts of stat are specified (e.g. perms)
        return True

    def local_hash(self, file_path: str) -> str:
        """
        Get the hash for local file at file_path
        Adds the hash to self.file_hashes if it isn't already there
        """
        existing_hash = self.file_hashes.get(file_path)
        if existing_hash is not None:
            return existing_hash
        # TODO handle duplicate files
        new_hash = self.local_hash(file_path)
        self.file_hashes[new_hash] = file_path
        return new_hash

    def remote_hash_command_line(self, path: str, file: str) -> str:
        """
        Hash the file at path/file on the remote server using python3 -c
        """
        hash_command = """python3 -c "from hashlib import {}
hasher = {}()
with open('{}', 'rb') as file:
    while True:
        data = file.read({})
        if not data:
            print(hasher.hexdigest())
            break
        hasher.update(data)" """.format(
            self.hash_method,
            self.hash_method,
            self.remote_path_join(path, file),
            self.remote_read_size,
        )
        _, result, _ = self.ssh.exec_command(hash_command)
        return result.read().decode()

    def local_path_from_remote(self, path: str) -> None:
        """
        Creates the equivalent of path on the remote server as a directory
        in the local server
        Returns the equivalent local path
        """
        assert path.startswith(self.remote_path)
        split = path[len(self.remote_path) :].split("/")[1:]
        cur = self.out_path
        for part in split:
            cur = os.path.join(cur, part)
            if not os.path.isdir(cur):
                if os.path.exists(cur):
                    raise FileExistsError("Directory " + cur + " is a file")
        return cur

    def create_local_path(self, path: str) -> None:
        """
        Create all the parts of path
        """
        dirs = path.split(os.path.sep)
        # TODO handle Windows-style paths (where dirs[0]/dirs[1] will be messed up
        # using this method since the drive letter is root)
        cur = ""
        for d in dirs:
            cur = os.path.join(cur, d)
            if not os.path.isdir(cur):
                os.mkdir(cur)

    def get_remote_filenames(self) -> List[Tuple[str]]:
        """
        Returns a list of absolute file paths and filenames in self.remote_path and
        its subdirectories sorted by path length ascending
        """
        # TODO handle symlinks (`find -type l`)
        _, files, _ = self.ssh.exec_command("find " + self.remote_path + " -type f")
        return sorted(
            [f.rstrip().rsplit("/", 1) for f in files], key=lambda x: len(x[0])
        )

    def move_file(self, local_file_path: str, new_file_path: str) -> None:
        """
        Moves (or copies if self.copy) the file at local_file_path to new_file_path,
        leaving a symbolic or hard link as specified by self.symlink and self.hardlink
        Removes the directory of local_file_path if self.clean
        """
        # TODO
        print("move local file {} to {}".format(local_file_path, new_file_path))
