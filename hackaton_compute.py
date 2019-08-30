from typing import List, Tuple

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import *
from azure.mgmt.network import NetworkManagementClient

def deploy_shared_network(
    resource_group_name: str,
    location: str,
    network_management_client: NetworkManagementClient,
) -> str:
    """Create a subnet that a VM can be deployed into

    - Resource group already exists
    - Network mgmt client is authenticated and ready to use
    """
    # TODO Create a subnet
    raise NotImplementedError("Create a Subnet")

    return subnet_id


def deploy_vm_networking(
    resource_group_name: str,
    location: str,
    vm_name: str,
    subnet_id: str,
    network_management_client: NetworkManagementClient
) -> Tuple[str, str]:
    """Create the network components necessary to create a publicly accessible VM

    - Resource group already exists
    - Network mgmt client is authenticated and ready to use
    """
    # TODO Create network components for a VM
    raise NotImplementedError("Create network components for a VM")

    return nic_id, public_ip_address


def deploy_vm(
    resource_group_name: str,
    location: str,
    vm_name: str,
    admin_user_name: str,
    nic_id: str,
    public_key: str,
    compute_management_client: ComputeManagementClient
) -> VirtualMachine:
    """Create a virtual machine that you can SSH into
    
    - Resource group already exists
    - Compute mgmt client is authenticated and ready to use
    """
    # TODO Create a VM that you can SSH into
    raise NotImplementedError("Create a VM that you can SSH into")

    return vm


def create_disk(
    resource_group_name: str,
    location: str,
    compute_management_client: ComputeManagementClient
) -> str:
    """Create a new managed disk

    - Resource group already exists
    - Compute mgmt client is authenticated and ready to use
    """
    # TODO Create a managed disk
    raise NotImplementedError("Create a managed disk")

    return disk_id


def attach_disk(
    resource_group_name: str,
    virtual_machine_name: str,
    disk_id: str,
    compute_management_client: ComputeManagementClient
) -> None:
    """Attach the given disk to the given VM

    - Resource group, VM and disk exist already
    - Compute mgmt client is authenticated and ready to use
    """
    # TODO Attach the given disk to the given VM
    raise NotImplementedError("Attach the given disk to the given VM")

def detach_disk(
    resource_group_name: str,
    virtual_machine_name: str,
    disk_id: str,
    compute_management_client: ComputeManagementClient
) -> None:
    """Detach the given disk from the given VM

    - Resource group, VM and disk exist already
    - Compute mgmt client is authenticated and ready to use
    """
    # TODO Detach the given disk from the given VM
    raise NotImplementedError("Detach the given disk from the given VM")


def execute_script(
    resource_group_name: str,
    virtual_machine_name: str,
    script: List[str],
    compute_management_client: ComputeManagementClient
) -> str:
    """
    Execute the given script on the machine.

    OPTIONALLY: return the stdout/stderr of the script. If you don't want to, return None.

    - Resource group and VM exist already
    - Compute mgmt client is authenticated and ready to use
    - The "script" is the array of lines. Most of the solution will directly takes this format
      and do not require any encoding or changes.
    """
    stdout_msg = None

    # TODO Execute this shell script on the givem VM
    raise NotImplementedError("Execute this shell script on the givem VM")

    return stdout_msg
