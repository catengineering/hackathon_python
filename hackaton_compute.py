from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import *
from azure.mgmt.network import NetworkManagementClient

def deploy_shared_network(
    resource_group_name: str,
    location: str,
    network_management_client: NetworkManagementClient,
    vnet_name='virtualNetwork'
) -> str:
    """Create a subnet that a VM can be deployed into

    - Resource group already exists
    - Network mgmt client is authenticated and ready to use
    """

    # Solution begin
    vnet = network_management_client.virtual_networks.create_or_update(
        resource_group_name,
        vnet_name,
        parameters = {
            'location': location,
            'addressSpace': {
                'addressPrefixes': [ "10.1.0.0/24"]
            },
            'subnets': [
                {
                    'name': 'default',
                    'properties': {
                        "addressPrefix": "10.1.0.0/24"
                    }
                }
            ] 
        }
    )
    vnet.wait()
    subnet_id = next(network_management_client.subnets.list(resource_group_name, vnet_name)).id
    # Solution end

    return subnet_id


def deploy_vm_networking(
    resource_group_name: str,
    location: str,
    vm_name: str,
    subnet_id: str,
    network_management_client: NetworkManagementClient
) -> (str, str):
    """Create the network components necessary to create a publicly accessible VM

    - Resource group already exists
    - Network mgmt client is authenticated and ready to use
    """

    # Solution begin
    import random
    from string import ascii_letters, digits
    def _random_string(length, alphabet = ascii_letters + digits) -> str:
        return ''.join(random.choice(alphabet) for _ in range(length))  # nosec

    network_security_group = network_management_client.network_security_groups.create_or_update(
        resource_group_name,
        f'{vm_name}NSG',
        parameters={
            'location': location,
            'securityRules':[
                {
                    "name": "SSH",
                    "properties": {
                        "priority": 300,
                        "protocol": "TCP",
                        "access": "Allow",
                        "direction": "Inbound",
                        "sourceAddressPrefix": "*",
                        "sourcePortRange": "*",
                        "destinationAddressPrefix": "*",
                        "destinationPortRange": "22"
                    }
                }
            ]
        }
    )
    
    public_ip = network_management_client.public_ip_addresses.create_or_update(
        resource_group_name,
        f'{vm_name}PublicIp',
        parameters={
            'location': location,
            "publicIpAllocationMethod": "Dynamic",
            "dnsSettings": {
                "domainNameLabel": 'hack-' + _random_string(8).lower()
            }
        }
    ).result()

    public_ip_address_id = public_ip.id
    public_ip_address = public_ip.dns_settings.fqdn
    network_security_group_id = network_security_group.result().id

    nic = network_management_client.network_interfaces.create_or_update(
        resource_group_name,
        f'{vm_name}Nic',
        parameters= {
            "location": location,
            "ipConfigurations": [
                    {
                        "name": "ipconfig1",
                        "properties": {
                            "subnet": {
                                "id": subnet_id
                            },
                            "privateIPAllocationMethod": "Dynamic",
                            "publicIpAddress": {
                                "id": public_ip_address_id
                            }
                        }
                    }
                ],
                "networkSecurityGroup": {
                    "id": network_security_group_id
                }
            }
    )
    nic_id = nic.result().id
    # Solution end

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
    """Create a virtual machine
    
    - Resource group already exists
    - Compute mgmt client is authenticated and ready to use
    """

    # Solution begin
    virtual_machine = compute_management_client.virtual_machines.create_or_update(
        resource_group_name = resource_group_name,
        vm_name=vm_name,
        parameters= {
            'location': location,
            'os_profile': {
                'computer_name': vm_name,
                'admin_username': admin_user_name,
                'linuxConfiguration': {
                    'disablePasswordAuthentication': True,
                    'ssh': {
                        'publicKeys': [
                            {
                                'path': f'/home/{admin_user_name}/.ssh/authorized_keys',
                                'keyData': public_key
                            }
                        ]
                    }
                }
            },
            'hardware_profile': {
                'vm_size': 'Standard_DS1_v2'
            },
            'storage_profile': {
                'image_reference': {
                    'publisher': 'Canonical',
                    'offer': 'UbuntuServer',
                    'sku': '16.04.0-LTS',
                    'version': 'latest'
                },
                "dataDisks": [
                ]
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': nic_id,
                }]
            },
        }
    )
    vm = virtual_machine.result()
    # Solution end

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

    # Solution start
    disk_name = 'disk'
    disk = compute_management_client.disks.create_or_update(
        resource_group_name,
        disk_name,
        disk={
            "location": location,
            "sku":{
                "name": "Standard_LRS"
            },
            "creationData": {
                "createOption": "Empty"
            },
            "diskSizeGB": 1
        }
    )
    disk_definition = disk.result()
    disk_id = disk_definition.id
    # Solution end

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
