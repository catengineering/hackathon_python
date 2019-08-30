from typing import Tuple

from azure.mgmt.rdbms.mysql import MySQLManagementClient
from azure.mgmt.rdbms.mysql.models import *


def create_mysql_database(
    resource_group_name: str,
    administrator_login: str,
    administrator_login_password: str,
    mysql_mgmt_client: MySQLManagementClient
) -> Tuple[str, str, str]:

    # Solution begin
    import random
    from string import ascii_letters, digits
    def _random_string(length, alphabet = ascii_letters + digits) -> str:
        return ''.join(random.choice(alphabet) for _ in range(length))  # nosec
    server_name = 'mysql{}'.format(_random_string(20)).lower()
    database_name = 'database'

    mysql_deployment = mysql_mgmt_client.servers.create(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters=ServerForCreate(
            properties=ServerPropertiesForDefaultCreate(
                administrator_login=administrator_login,
                administrator_login_password=administrator_login_password,
            ),
            location="eastus",
        ),
    )
    mysql = mysql_deployment.result()

    if not mysql.fully_qualified_domain_name:
        mysql = mysql_mgmt_client.servers.get(
            resource_group_name=resource_group_name,
            server_name=server_name,
        )
    host = mysql.fully_qualified_domain_name

    database_deployment = mysql_mgmt_client.databases.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        database_name=database_name,
        charset='utf8',
        collation='utf8_general_ci',
    )

    firewall_deployment = mysql_mgmt_client.firewall_rules.create_or_update(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name='AllowAll',
        start_ip_address='0.0.0.0',
        end_ip_address='255.255.255.255',
    )

    database_deployment.wait()
    firewall_deployment.wait()
    # Solution end

    return server_name, database_name, host
