from typing import Tuple

from azure.mgmt.rdbms.mysql import MySQLManagementClient
from azure.mgmt.rdbms.mysql.models import *


def create_mysql_database(
    resource_group_name: str,
    administrator_login: str,
    administrator_login_password: str,
    mysql_mgmt_client: MySQLManagementClient
) -> Tuple[str, str, str]:
    """Create a MySQL server, database and necessary config to connect to it.

    Return your chosen server name, database name, and attributed host

    - Resource group exists already
    - MySQL mgmt client is authenticated and ready to use
    """

    # TODO Create server, database and configure as necessary
    raise NotImplementedError("Create server, database and configure as necessary")

    return server_name, database_name, host
