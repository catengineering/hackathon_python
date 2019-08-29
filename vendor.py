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
from ipaddress import ip_address
from string import ascii_letters, digits
from time import sleep
import socket
from datetime import timedelta, datetime, timezone

from azure.common.client_factory import get_client_from_auth_file, get_client_from_cli_profile
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.rdbms.mysql import MySQLManagementClient
from azure.storage.blob import BlockBlobService
from msrestazure.azure_exceptions import ClientException
from environs import Env

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError

from tests.metrics import metrics


##############################################################################
# Global variables and type definitions
##############################################################################

ENV = Env()
ENV.read_env()

CWD = Path(__file__).resolve().parent

LOG = getLogger(__name__)
LOG_FORMATTER = Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

LOG_STREAM_HANDLER = StreamHandler()
LOG_STREAM_HANDLER.setFormatter(LOG_FORMATTER)
LOG_STREAM_HANDLER.setLevel(ENV('LOG_LEVEL', 'DEBUG'))
LOG.addHandler(LOG_STREAM_HANDLER)
LOG.setLevel('DEBUG')

PREFIX = ENV('RESOURCE_PREFIX', 'hackaton')
RESOURCE_GROUP_LOCATION = ENV('RESOURCE_GROUP_LOCATION', 'eastus')
MYSQL_PORT = 3306

ObjectStorageHandle = namedtuple('ObjectStorageHandle', ['blob_client', 'container_name'])
StorageHandle = namedtuple('StorageHandle', ['account_name', 'account_key'])
MysqlHandle = namedtuple('MysqlHandle', ['user', 'password', 'host', 'port', 'database', 'connect_args', 'connector'])

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
    resource_group_name = '{}mysql{}'.format(PREFIX, _random_string(20))
    administrator_login = ENV('MYSQL_ADMIN_LOGIN', 'hackaton')
    administrator_login_password = ENV('MYSQL_ADMIN_PASSWORD', "Don't_hardCode-this!12345!")
    server_name = '{}{}'.format(PREFIX, _random_string(20)).lower()
    database_name = '{}db'.format(PREFIX)

    with _deploy_resource_group(resource_group_name, RESOURCE_GROUP_LOCATION):
        mysql = _deploy_mysql(
            resource_group_name=resource_group_name,
            location=RESOURCE_GROUP_LOCATION,
            administrator_login=administrator_login,
            administrator_login_password=administrator_login_password,
            server_name=server_name,
            database_name=database_name,
        )
        yield mysql


def create_relational_database_client(handle):
    """
    Given a handle to the database created in `create_relational_database_instance`,
    return a sqlalchemy engine to connect to that database.

    This function is not expected to call `engine.connect()`, the test
    suite will do that on the value returned by this function.
    """
    _wait_for_port(
        host=handle.host,
        port=handle.port,
        max_wait_time=timedelta(seconds=ENV.int('MAX_WAIT_TIME_DATABASE_SECONDS', 120)),
    )

    LOG.debug('Creating sqlalchemy engine for %s:%s', handle.host, handle.port)
    engine = create_engine(
        '{connector}://{user}:{password}@{host}:{port}/{database}'.format(
            connector=handle.connector,
            user=handle.user,
            password=handle.password,
            host=handle.host,
            port=handle.port,
            database=handle.database,
        ),
        implicit_returning=False,
        connect_args=handle.connect_args,
    )

    _wait_for_sqlalchemy(engine)

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


def _deploy_mysql(
        resource_group_name,
        location,
        administrator_login,
        administrator_login_password,
        server_name,
        database_name,
):
    client = _new_client(MySQLManagementClient)

    LOG.debug('Creating database server %s', server_name)

    # Here creates a server, and database you can connect to
    # Populate the "host" variable correctly from what you get from azure

    host = "update this value"

    mysql_deployment = client.servers.create(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters=client.servers.models.ServerForCreate(
            properties=client.servers.models.ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
            ),
            location=location,
        ),
    )
    mysql = mysql_deployment.result()

    if not mysql.fully_qualified_domain_name:
        mysql = client.servers.get(
            resource_group_name=resource_group_name,
            server_name=server_name,
        )
    host = mysql.fully_qualified_domain_name
    LOG.debug('Done creating database server %s at %s', server_name, host)

    LOG.debug('Creating database and firewall rule in server %s', server_name)
    database_deployment = client.databases.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        database_name=database_name,
        charset=ENV('MYSQL_DATABASE_CHARSET', 'utf8'),
        collation=ENV('MYSQL_DATABASE_COLLATION', 'utf8_general_ci'),
    )

    firewall_deployment = client.firewall_rules.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name=ENV('MYSQL_FIREWALL_RULE_NAME', 'AllowAll'),
        start_ip_address=ENV('MYSQL_FIREWALL_START_IP_ADDRESS', '0.0.0.0'),
        end_ip_address=ENV('MYSQL_FIREWALL_END_IP_ADDRESS', '255.255.255.255'),
    )

    database_deployment.wait()
    firewall_deployment.wait()

    # Don't touch after this point

    LOG.debug('Done creating database and firewall rule in server %s', server_name)

    if _is_ip_address(host):
        user = administrator_login
    else:
        user = '{}@{}'.format(administrator_login, server_name)

    return MysqlHandle(
        user=user,
        password=administrator_login_password,
        host=host,
        port=MYSQL_PORT,
        database=database_name,
        connect_args={
            'ssl': {
                'ca_cert': CWD / "BaltimoreCyberTrustRoot.crt.pem"
            }
        },
        connector='mysql+pymysql',
    )

##############################################################################
# Utility functions
##############################################################################

def _is_ip_address(ip_or_fqdn: str) -> bool:
    try:
        ip_address(ip_or_fqdn)
    except ValueError:
        return False
    else:
        return True


def _wait_for_sqlalchemy(engine, polling_interval_seconds=3):

    while True:
        try:
            with engine.connect() as connection:
                for _ in connection.execute('select 1'):
                    pass
        except SQLAlchemyError as ex:
            LOG.debug('Unable to connect to database: %s', ex)
        else:
            LOG.debug('Database connection is available')
            break

        LOG.debug('Waiting for database connection')
        sleep(polling_interval_seconds)


def _wait_for_port(
        host: str,
        port: int,
        max_wait_time,
        polling_interval_seconds: float = ENV.float('PORT_CHECK_POLLING_INTERVAL', 1),
) -> None:
    start_time = _utcnow()

    while True:
        if _is_port_open(host, port):
            break

        if _utcnow() - start_time > max_wait_time:
            raise ValueError('{}:{} was not available in time'.format(host, port))

        LOG.debug('Waiting for %s:%d', host, port)
        sleep(polling_interval_seconds)

def _utcnow():
    now = datetime.utcnow()
    now = now.replace(tzinfo=timezone.utc)
    return now

def _is_port_open(
        host,
        port,
        socket_timeout_seconds = ENV.float('PORT_CHECK_TIMEOUT_SECONDS', 1),
):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(socket_timeout_seconds)
        result = sock.connect_ex((host, port))
    except socket.error as ex:
        LOG.debug('Unable to open socket %s:%d, reason: %s', host, port, ex)
        return False
    finally:
        sock.close()

    port_is_open = result == 0
    if port_is_open:
        LOG.debug('Socket %s:%d is open', host, port)
    else:
        LOG.debug('Socket %s:%d is not open, reason: %s', host, port, result)

    return port_is_open
