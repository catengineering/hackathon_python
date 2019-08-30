from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import *

# Storage account

def create_storage_account(
        resource_group_name: str,
        storage_management_client: StorageManagementClient
) -> str:
    """Create a storage account and return the account name and the key.

    - Resource group exists already
    - Storage mgmt client is authenticated and ready to use
    """

    # Create a storage account and return his primary key

    # Solution begin
    import random
    from string import ascii_letters, digits
    def _random_string(length, alphabet = ascii_letters + digits) -> str:
        return ''.join(random.choice(alphabet) for _ in range(length))  # nosec
    account_name = 'storage{}'.format(_random_string(20)).lower()[:24]

    storage_deployment = storage_management_client.storage_accounts.create(
        resource_group_name=resource_group_name,
        account_name=account_name,
        parameters=StorageAccountCreateParameters(
            sku=Sku(
                name='Standard_LRS',
            ),
            kind=Kind.storage,
            location='eastus',
        ),
    )
    storage_deployment.wait()

    account_key = storage_management_client.storage_accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=account_name,
    ).keys[0].value
    # Solution end

    return account_name, account_key
