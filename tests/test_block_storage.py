# encoding: utf-8

import contextlib

from .common import test

from vendor import (
    create_compute_instance,
    create_block_storage_instance,
    create_compute_ssh_client,

    attach_block_storage_to_compute,
    remove_block_storage_from_compute,
)


@test
def test_block_storage():
    with create_block_storage_instance() as block, \
            create_compute_instance() as compute1, \
            create_compute_instance() as compute2:
        phrase = b"Nobody inspects the spammish repetition"

        ssh = create_compute_ssh_client(compute1)
        path = attach_block_storage_to_compute(compute1, block)
        sftp = ssh.open_sftp()
        fo = sftp.file(path, 'wb')
        fo.seek(1337)
        fo.write(phrase)
        fo.flush()
        fo.close()
        remove_block_storage_from_compute(compute1, block)
        ssh = create_compute_ssh_client(compute2)
        path = attach_block_storage_to_compute(compute2, block)
        sftp = ssh.open_sftp()
        fo = sftp.file(path, 'rb')
        fo.seek(1337)
        read_back = fo.read(len(phrase))
        remove_block_storage_from_compute(compute2, block)

        assert read_back == phrase, \
            "Data node 1 wrote to block storage didn't read on node 2."
