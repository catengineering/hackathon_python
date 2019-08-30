# encoding: utf-8

import contextlib

from .common import file_exists, must_run, test
from vendor import create_compute_ssh_client, create_compute_instance


@contextlib.contextmanager
def new_compute_instance(resource_group_name):
    # vendor import moved inside call to break circular import. This function
    # ought to be moved into vendor, but it also should not be modified by the
    # vendor.
    with create_compute_instance(resource_group_name) as node:
        yield create_compute_ssh_client(node)


@test
def test_multiple_compute(resource_group_name):
    with new_compute_instance(resource_group_name) as compute1, new_compute_instance(resource_group_name) as compute2:
        compute1.open_sftp().file("seen", 'wb').close()
        try:
            compute2.open_sftp().file("seen", 'rb').close()
        except FileNotFoundError:
            return
        assert False, "Compute nodes appear to share a filesystem"


@test
def test_linux_userland(resource_group_name):
    with new_compute_instance(resource_group_name) as client:
        assert file_exists(client, "testing") == False, \
            "test file already exists on the target sytem"

        must_run(client, "touch testing")

        assert file_exists(client, "testing") == True, \
            "test file was not created on the target system"

        must_run(client, "rm testing")

        assert file_exists(client, "testing") == False, \
            "test file was not removed on the target sytem"
