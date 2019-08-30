# encoding: utf-8

from pathlib import Path
from collections import namedtuple

import os
import contextlib
import logging
import paramiko
import boto3
from tests.metrics import metrics

CWD = Path(__file__).resolve().parent

LOG = logging.getLogger("vendor")
LOG.setLevel(os.getenv("LOG_LEVEL", "WARNING"))
LOG.addHandler(logging.StreamHandler())

##############################################################################
# Global variables and type definitions
##############################################################################

ComputeHandle = namedtuple("ComputeHandle", ["host", "port", "username", "instanceid"])

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "us-west-2"
AWS_AVAILABILITY_ZONE = "us-west-2a"
VPC_NAME = "sample_vpc"
ADMIN_USERNAME = "ec2-user"


ec2 = boto3.resource(
    "ec2",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

ec2_client = boto3.client(
    "ec2",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


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

    def _deploy_vpc(vpc_name, availability_zone):
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        ec2_client.modify_vpc_attribute(
            VpcId=vpc.id, EnableDnsHostnames={"Value": True}
        )

        # Assign name to the vpc
        vpc.create_tags(Tags=[{"Key": "Name", "Value": vpc_name}])
        vpc.wait_until_available()

        # Create an Internet Gateway and attach it to the vpc
        internet_gateway = ec2.create_internet_gateway()
        internet_gateway.attach_to_vpc(VpcId=vpc.vpc_id)

        # Create Route Table (public route)
        route_table = vpc.create_route_table()
        route_table.create_route(
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=internet_gateway.internet_gateway_id,
        )

        # Create a subnet in our VPC
        subnet = vpc.create_subnet(
            CidrBlock="10.0.0.0/24", AvailabilityZone=availability_zone
        )

        # Associate the route table with subnet
        route_table.associate_with_subnet(SubnetId=subnet.id)

        # Create Security group
        security_group = vpc.create_security_group(
            GroupName="sample-name", Description="sample security group"
        )

        permission = [
            {
                "IpProtocol": "TCP",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ]

        security_group.authorize_ingress(IpPermissions=permission)

        return subnet.id, security_group.group_id

    def _deploy_vm(subnet_id, security_group_id, availability_zone):
        instances = ec2.create_instances(
            ImageId="ami-082b5a644766e0e6f",
            InstanceType="t2.micro",
            MaxCount=1,  # Required
            MinCount=1,  # Required
            KeyName="sample_hack",  # Key already uploaded to AWS
            Placement={"AvailabilityZone": availability_zone},
            NetworkInterfaces=[
                {
                    "SubnetId": subnet_id,
                    "DeviceIndex": 0,
                    "AssociatePublicIpAddress": True,
                    "Groups": [security_group_id],
                }
            ],
        )
        waiter = ec2_client.get_waiter("instance_status_ok")
        waiter.wait(InstanceIds=[instances[0].instance_id])
        instances[0].reload()

        instance_id = instances[0].instance_id
        public_ip = instances[0].public_ip_address

        return public_ip, instance_id

    subnet_id, security_group_id = _deploy_vpc(
        vpc_name=VPC_NAME, availability_zone=AWS_AVAILABILITY_ZONE
    )
    public_ip, instance_id = _deploy_vm(
        subnet_id=subnet_id,
        security_group_id=security_group_id,
        availability_zone=AWS_AVAILABILITY_ZONE,
    )

    yield ComputeHandle(
        host=public_ip, port=22, username=ADMIN_USERNAME, instanceid=instance_id
    )


def create_compute_ssh_client(compute):
    """
    Given the handle provided from `create_compute_instance`,
    create a `paramiko.client.SSHClient`

    be sure to `.connect()` to the machine before returning the SSHClient handle.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.load_system_host_keys()
    # Please change me to point me to env. variable
    file_loc = os.path.expanduser("~\Documents\keys\sample_hack.pem")
    privkey = paramiko.RSAKey.from_private_key_file(file_loc)
    client.connect(
        hostname=compute.host,
        port=compute.port,
        username=compute.username,
        pkey=privkey,
    )

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
    ebs_vol = ec2.create_volume(Size=20, AvailabilityZone=AWS_AVAILABILITY_ZONE)
    vol_id = ebs_vol.volume_id
    waiter = ec2_client.get_waiter("volume_available")
    waiter.wait(VolumeIds=[vol_id])

    yield vol_id


def attach_block_storage_to_compute(compute_handle, storage_handle):

    ec2_client.attach_volume(
        Device="/dev/sdf", InstanceId=compute_handle.instanceid, VolumeId=storage_handle
    )
    waiter = ec2_client.get_waiter("volume_in_use")
    waiter.wait(VolumeIds=[storage_handle])

    script_path = CWD / "resources" / "mount_data_disk.sh"

    with create_compute_ssh_client(compute_handle) as ssh:
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/mount_data_disk.sh", "wb") as remote:
            with open(script_path, "rb") as script:
                remote.write(script.read())

        stdin, stdout, stderr = ssh.exec_command("/bin/bash /tmp/mount_data_disk.sh")

    return "/datadisk/demo"


def remove_block_storage_from_compute(compute_handle, storage_handle):
    print("remove_block_storage_from_compute")
    with create_compute_ssh_client(compute_handle) as ssh:
        stdin, stdout, stderr = ssh.exec_command("sudo umount /dev/xvdf1")
        LOG.debug("%s %s", stdout.read(), stderr.read())

    ec2_client.detach_volume(
        Force=True,
        Device="/dev/sdf",
        InstanceId=compute_handle.instanceid,
        VolumeId=storage_handle,
    )
    waiter = ec2_client.get_waiter("volume_available")
    waiter.wait(VolumeIds=[storage_handle])


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
