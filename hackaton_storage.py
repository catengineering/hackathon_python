from typing import Tuple

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import *

# Storage account

def create_storage_account(
        resource_group_name: str,
        storage_management_client: StorageManagementClient
) -> Tuple[str, str]:
    """Create a storage account and return the account name and the key.

    - Resource group exists already
    - Storage mgmt client is authenticated and ready to use
    """

    # TODO Create a storage account
    raise NotImplementedError("You need to create a storage account")

    return account_name, account_key
