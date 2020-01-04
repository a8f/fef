def test_connection_with_keyfile(ssh_server, file_finder):
    assert file_finder.ssh is not None
