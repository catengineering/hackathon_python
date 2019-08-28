# encoding: utf-8

import contextlib
import paramiko
import sqlalchemy

from functools import lru_cache
from logging import FileHandler, Formatter, StreamHandler, getLogger
from os.path import expanduser
from pathlib import Path
from contextlib import contextmanager
from collections import namedtuple
from urllib.parse import urlparse
import random
from string import ascii_letters, digits

from azure.common.client_factory import get_client_from_auth_file, get_client_from_cli_profile
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService
from msrestazure.azure_exceptions import ClientException
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

PREFIX = ENV('RESOURCE_PREFIX', 'hackaton')
RESOURCE_GROUP_LOCATION = ENV('RESOURCE_GROUP_LOCATION', 'eastus')

ObjectStorageHandle = namedtuple('ObjectStorageHandle', ['blob_client', 'container_name'])
StorageHandle = namedtuple('StorageHandle', ['account_name', 'account_key'])

# Global configuration of the environment to run tests in.


def setup_environment():
    """
    Preform any initial configuring of the environment needed to preform any
    of the calls in this file.
    """



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
@contextmanager
def create_object_storage_instance():
    """Create a new object storage instance.

    :returns: a handle to the object storage instance in a format that other functions in this file can use.
    """
    resource_group_name = '{}storage{}'.format(PREFIX, _random_string(20))
    container_name = '{}container'.format(PREFIX)

    with _deploy_resource_group(resource_group_name, RESOURCE_GROUP_LOCATION):

        storage_account_name = '{}storage{}'.format(PREFIX, _random_string(20)).lower()[:24]

        try:
            storage = _deploy_storage(
                resource_group_name=resource_group_name,
                location=RESOURCE_GROUP_LOCATION,
                account_name=storage_account_name,
            )

            blob_client = BlockBlobService(
                account_name=storage.account_name,
                account_key=storage.account_key,
            )

            blob_client.create_container(container_name, fail_on_exist=False)
        except ClientException as ex:
            LOG.debug('Error in storage account %s or container %s: %s', storage_account_name, container_name, ex)
            raise
        else:
            LOG.debug('Storage account %s and container %s are available', storage_account_name, container_name)

        yield ObjectStorageHandle(
            blob_client=blob_client,
            container_name=container_name,
        )


def object_storage_list(handle):
    """List all objects contained inside the object store.

    :param handle: handle provided by :func:`~create_object_storage_instance`.
    :returns: a list of object names.
    """
    return [blob.name for blob in handle.blob_client.list_blobs(handle.container_name)]


def object_storage_delete(handle, path):
    """Delete an object on the storage.

    :param handle: handle provided by :func:`~create_object_storage_instance`.
    :param path: path of the object to delete.
    """
    handle.blob_client.delete_blob(handle.container_name, path)


def object_storage_write(handle, path, data):
    """Write the data held in memory to the object storage instance.

    :param handle: handle provided by :func:`~create_object_storage_instance`.
    :param path: path of the object to write.
    :param data: the bytes to write.
    """
    handle.blob_client.create_blob_from_bytes(handle.container_name, path, data)


def object_storage_read(handle, path):
    """Read data from the object storage instance.

    :param handle: handle provided by :func:`~create_object_storage_instance`.
    :param path: path of the object to read.
    :returns: the bytes read from the storage.
    """
    return handle.blob_client.get_blob_to_bytes(handle.container_name, path).content


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


def _random_string(length, alphabet = ascii_letters + digits) -> str:
    return ''.join(random.choice(alphabet) for _ in range(length))  # nosec


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


@contextlib.contextmanager
def _deploy_resource_group(
        resource_group_name: str,
        resource_group_location: str,
):
    client = _new_client(ResourceManagementClient)

    LOG.debug('Creating resource group %s', resource_group_name)
    client.resource_groups.create_or_update(
        resource_group_name=resource_group_name,
        parameters={'location': resource_group_location},
    )

    yield

    LOG.debug('Cleaning up resource group %s', resource_group_name)
    try:
        client.resource_groups.delete(resource_group_name, polling=False)
    except ClientException as ex:
        LOG.warning('Error deleting resource group %s: %s', resource_group_name, ex)



def _deploy_storage(
        resource_group_name: str,
        location: str,
        account_name: str,
        sku: str = ENV('STORAGE_SKU', 'Standard_LRS'),
):
    client = _new_client(StorageManagementClient)

    LOG.debug('Creating storage account %s', account_name)
    storage_deployment = client.storage_accounts.create(
        resource_group_name=resource_group_name,
        account_name=account_name,
        parameters=client.storage_accounts.models.StorageAccountCreateParameters(
            sku=client.storage_accounts.models.Sku(
                name=sku,
            ),
            kind=client.storage_accounts.models.Kind.storage,
            location=location,
        ),
    )
    storage = storage_deployment.result()

    LOG.debug('Done creating storage account %s', account_name)

    LOG.debug('Fetching access keys for storage account %s', account_name)
    account_key = client.storage_accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=account_name,
    ).keys[0].value
    LOG.debug('Done fetching access keys for storage account %s', account_name)

    return StorageHandle(
        account_name=account_name,
        account_key=account_key,
    )
