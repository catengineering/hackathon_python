# encoding: utf-8

import contextlib
import paramiko
import sqlalchemy

from functools import lru_cache
from logging import FileHandler, Formatter, StreamHandler, getLogger
from os.path import expanduser
from pathlib import Path

from azure.common.client_factory import get_client_from_auth_file, get_client_from_cli_profile
from azure.mgmt.resource import ResourceManagementClient
from environs import Env

from tests.metrics import metrics


##############################################################################
# Global variables and type definitions
##############################################################################

ENV = Env()
ENV.read_env()

LOG = getLogger(__name__)
LOG_FORMATTER = Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

LOG_STREAM_HANDLER = StreamHandler()
LOG_STREAM_HANDLER.setFormatter(LOG_FORMATTER)
LOG_STREAM_HANDLER.setLevel(ENV('LOG_LEVEL', 'FATAL'))
LOG.addHandler(LOG_STREAM_HANDLER)


# Global configuration of the environment to run tests in.


def setup_environment():
    """
    Preform any initial configuring of the environment needed to preform any
    of the calls in this file.
    """
    client = _new_client(ResourceManagementClient)


def teardown_environment():
    """
    Preform any teardown required after running any of the actions in this file.

    This should completley shut down or destroy any running resources that were
    spun up as a result of running the functions in this file.
    """


# Compute-specficic helpers to create, destroy and access resources.


@metrics
@contextlib.contextmanager
def create_compute_instance():
    """
    Create a new compute instance from a Linux VM Image. It should be completely
    new, and created dynamically at call time.

    This context manager should yield a handle to the new image, in a format
    that other functions in this file can use (such as
    `create_object_storage_instance`).
    """
    raise NotImplementedError("create_compute_instance is not implemented")


def create_compute_ssh_client(compute):
    """
    Given the handle provided from `create_compute_instance`,
    create a `paramiko.client.SSHClient`

    be sure to `.connect()` to the machine before returning the SSHClient handle.
    """
    raise NotImplementedError("create_compute_ssh_client is not implemented")

    client = paramiko.SSHClient()
    return client


# Object storage specific helpers to create, destroy and access resources.


@metrics
@contextlib.contextmanager
def create_object_storage_instance():
    """
    Create a new object storage instance.

    This context manager should yield a handle to the object storage instance,
    in a format that other functions in this file can use.
    """
    raise NotImplementedError("create_object_storage_instance is not implemented")
    yield None


def object_storage_list(handle):
    """
    Given the object yielded by the `create_object_storage_instance` context
    manager (`handle)`, list all objects contained inside the object store.
    """
    raise NotImplementedError("object_storage_list is not implemented")


def object_storage_delete(handle, path):
    """
    Given the object yielded by the `create_object_storage_instance` context
    manager (`handle)`, delete the object at `path`.
    """
    raise NotImplementedError("object_storage_delete is not implemented")


def object_storage_write(handle, path, data):
    """
    Given the object yielded by the `create_object_storage_instance` context
    manager (`handle)`, write the data held in memory as `data` to `path` inside the
    object storage instance.

    Calls to read that path must return the data bytes as held in memory here.
    """
    raise NotImplementedError("object_storage_write is not implemented")


def object_storage_read(handle, path):
    """
    Given the object yielded by the `create_object_storage_instance` context
    manager (`handle`), read the data present in the remote object storage instance
    stored at `path`, and return that data completely read into memory.
    """
    raise NotImplementedError("object_storage_read is not implemented")


# Block storage specific helpers to create, destroy and attach resources.


@metrics
@contextlib.contextmanager
def create_block_storage_instance():
    """
    Create a new block storage instance, which can be attached to a specific
    compute instance.

    This context manager should yield a handle to the block storage instance,
    in a format that other functions in this file can use.
    """
    raise NotImplementedError("create_block_storage_instance is not implemented")
    yield None


def attach_block_storage_to_compute(compute_handle, storage_handle):
    raise NotImplementedError("attach_block_storage_to_compute is not implemented")


def remove_block_storage_from_compute(compute_handle, storage_handle):
    raise NotImplementedError("remove_block_storage_from_compute is not implemented")


# Relational database specific helpers to create, destroy and access resources.


@metrics
@contextlib.contextmanager
def create_relational_database_instance():
    """
    Create a new relational database instance.

    This context manager should yield a handle to the relational database
    instance, in a format that other functions in this file can use.
    """
    raise NotImplementedError("create_relational_database_instance is not implemented")
    yield None


def create_relational_database_client(database):
    """
    Given a handle to the database created in `create_relational_database_instance`,
    return a sqlalchemy engine to connect to that database.

    This function is not expected to call `engine.connect()`, the test
    suite will do that on the value returned by this function.
    """
    raise NotImplementedError("create_relational_database_client is not implemented")
    return engine


@lru_cache(maxsize=32)
def _new_client(client_type):
    client_args = {}

    base_url = ENV('ARM_BASE_URL', '')
    if base_url:
        client_args['base_url'] = base_url
        LOG.debug('Using custom ARM endpoint %s for %s', base_url, client_type.__name__)
    else:
        LOG.debug('Using default ARM endpoint for %s', client_type.__name__)

    auth_path = expanduser(ENV('AZURE_AUTH_LOCATION', ''))
    if auth_path and Path(auth_path).is_file():
        LOG.debug('Using auth file %s for %s', auth_path, client_type.__name__)
        client_args['auth_path'] = auth_path

    try:
        client = get_client_from_auth_file(client_type, **client_args)
    except FileNotFoundError:
        client = get_client_from_cli_profile(client_type, **client_args)
        LOG.warning('Auth file not found, falling back to CLI profile for %s', client_type.__name__)

    return client
