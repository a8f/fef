# fef: Find Existing Files
Copy existing files to a directory structure matching a remote server, (optionally) maintaining the original directory structure with symbolic (or hard) links. Originally created to be used before running `rsync -a`. Currently only UNIX servers are supported.

### Installation
Requires Python 3.5+ and the [Paramiko](http://www.paramiko.org/installing.html) module.

To install Paramiko, use `pip install paramiko`

Then `git clone https://github.com/a8f/fef && cd fef`

### Limitations
The following cases have undefined behaviour (which may include data loss) and will likely never be supported:
  - Multiple files or directories in the same directory with the same name
  - File names ending with a newline
  - File/directory names with a forward slash in them
  - File/directory names with a backslash in them when using a Windows client

The following cases are currently unsupported but may be supported in the future:
  - Different encoding on the client and server
  - Only Python 2 on the server (not Python 3)

### Usage
`./fef.py <user@host:port> <remote-dir> <local-dir>` where `<local-dir>` is the directory
to look for files in. To specify a directory to clone into (i.e. where you will rsync to after fef completes) use `-o <out-dir>`.

Other common flags are:

    -s, --no-symlinks     Don't create symbolic links when moving files
    -d, --hard            Create hard links instead of symbolic links when moving files
    -r, --recursive       Recursively copy directories in remote-dir
    -k <keyfile>          SSH key file to use for connecting to the host

Full usage instructions can be found by running `./fef.py --help`


### Contributing
~~Pull requests are welcome. Code should be formatted with [Black](https://github.com/psf/black).~~ fef is currently a WIP. Pull requests will be considered after basic functionality is complete.
