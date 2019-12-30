#!/usr/bin/python3

"""
fef: find and move existing files to match remote server's file structure
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

import argparse
from sys import version_info
from textwrap import wrap

from file_finder import FileFinder


class RawFormatter(argparse.HelpFormatter):
    """
    Argparse help formatter which maintains newlines and tabs if the help string
    starts with raw'
    """

    def _split_lines(self, text, width):
        if text.startswith("raw'"):
            out = ["\n".join(wrap(l, width)) for l in text[4:].split("\n")]
            return out
        return argparse.HelpFormatter._split_lines(self, text, width)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Move existing files to match the directory structure of a"
        "remote server",
        formatter_class=RawFormatter,
    )
    parser.add_argument(
        "host",
        type=str,
        help="Hostname to connect to via SSH, optionally prefixed by a username (e.g."
        "user@host). May also include a port (e.g. user@host:1234)",
    )
    parser.add_argument(
        "remote_dir", type=str, help="Directory to clone from remote server",
    )
    parser.add_argument(
        "local_dir", type=str, help="Directory to search for existing files in",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        metavar="<username>",
        help="Username to use when connecting to the host."
        "Overrides the username specified in host",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        metavar="<port>",
        help="Port to connect to on the host. Overrides the port specified in host.",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        type=str,
        metavar="<out-dir>",
        help="Local directory to clone into",
    )
    link_group = parser.add_mutually_exclusive_group()
    link_group.add_argument(
        "-l",
        "--no-symlinks",
        action="store_false",
        help="Don't create symbolic links when moving files",
    )
    link_group.add_argument(
        "-d",
        "--hard",
        action="store_true",
        help="Create hard links instead of symbolic links when moving files",
    )
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        "-k",
        "--keyfile",
        type=str,
        metavar="<keyfile>",
        help="SSH key file to use for connecting to the host",
    )
    auth_group.add_argument(
        "--password",
        type=str,
        metavar="<password>",
        help="Password to use to connect to the remote server. "
        "This is insecure and should be avoided! "
        "Your password will be visible to anybody who can access your shell history. "
        "If possible you should instead use -k or enter a password interactively",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively copy directories in remote-dir",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        action="store",
        type=int,
        metavar="level",
        default=1,
        nargs="?",
        choices=[0, 1, 2],
        const=2,
        help="raw'Verbosity level. One of:\n"
        "\t0: Output only critical errors and success messages\n"
        "\t1 (default): Output warnings and file transfer information\n"
        "\t2: Output verbose information about every action\n"
        "If no level is specified then 2 is assumed",
    )
    parser.add_argument(
        "-x",
        "--clean",
        action="store_true",
        help="Remove empty directories after moving files out of them"
        " (this will not modify directories that are not copied from)",
    )
    parser.add_argument(
        "-c",
        "--copy",
        action="store_true",
        help="Copy files from local-files-dir instead of moving them."
        " This causes no links to be created regardless of other flags",
    )
    parser.add_argument(
        "-f",
        "--hash-function",
        default="sha1",
        help="Function for hashing files on the remote server (default SHA1)",
        metavar="<algorithm>",
    )
    parser.add_argument(
        "-n",
        "--no-file-attributes",
        action="store_true",
        help="Don't update file permissions and access time to match remote server."
        "This will cause rsync to download files that have an older modification date"
        " or different file permissions on the local machine",
    )
    parser.add_argument(
        "--req-existing-hostkey",
        action="store_true",
        help="Only connect if the host is already in the system's host keys "
        "(as opposed to the default of adding the new key to the system)",
    )
    parser.add_argument(
        "--no-local-keys",
        action="store_true",
        help="Don't use keys in ~/.ssh or from the ssh agent when connecting",
    )
    return parser


def run():
    parser = get_parser()
    if version_info[1] < 7:
        args = parser.parse_args()
    else:
        args = parser.parse_intermixed_args()
    try:
        file_finder = FileFinder(**vars(args))
    except ValueError as e:
        print("Error: {}".format(e))
        return
    if file_finder.run():
        print("Done")
    else:
        print("An error occurred. No files have been modfied")


if __name__ == "__main__":
    run()
