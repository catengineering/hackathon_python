from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import *

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

    # Solution begin
    vm_definition = compute_management_client.virtual_machines.get(
        resource_group_name,
        virtual_machine_name
    )

    disk_name = disk_id.split('/')[-1]

    vm_definition.storage_profile.data_disks.append({
        'lun': 13,
        'name': disk_name,
        'create_option': "Attach",
        'managed_disk': {
            'id': disk_id
        }
    })
    compute_management_client.virtual_machines.create_or_update(
        resource_group_name,
        virtual_machine_name,
        vm_definition
    ).wait()
    # Solution end

def detach_disk(
    resource_group_name: str,
    virtual_machine_name: str,
    disk_id: str,
    compute_management_client: ComputeManagementClient
) -> None:
    """Detach the given disk to the given VM

    - Resource group, VM and disk exist already
    - Compute mgmt client is authenticated and ready to use
    """
    # Solution begin
    vm_definition = compute_management_client.virtual_machines.get(
        resource_group_name,
        virtual_machine_name
    )

    disk_name = disk_id.split('/')[-1]

    vm_definition.storage_profile.data_disks = [
        d for d in vm_definition.storage_profile.data_disks if not d.name == disk_name
    ]    
    compute_management_client.virtual_machines.create_or_update(
        resource_group_name,
        virtual_machine_name,
        vm_definition
    ).wait()
    # Solution end
