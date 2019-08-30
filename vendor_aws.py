# encoding: utf-8

import contextlib
import paramiko

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
import socket
from datetime import timedelta, datetime, timezone

from environs import Env

from tests.metrics import metrics

# AWS
import os
import boto3
import datetime
from botocore.exceptions import ClientError
from base64 import b64encode

################
##############################################################################
# Global variables and type definitions
##############################################################################


ComputeHandle = namedtuple('ComputeHandle', ['host', 'port', 'username'])

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "us-west-2"
AWS_AVAILABILITY_ZONE = "us-west-2a"
VPC_NAME = "sample_VPC"
ADMIN_USERNAME= "ubuntu"


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
ssm_client = boto3.client(
    "ssm",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Global configuration of the environment to run tests in.
#############

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
        ec2_client.modify_vpc_attribute( VpcId = vpc.id , EnableDnsHostnames = { 'Value': True } )

        # Assign name to the vpc
        vpc.create_tags(Tags=[{"Key": "Name", "Value": vpc_name}])
        vpc.wait_until_available()

        # Create an Internet Gateway and attach it to the vpc
        internet_gateway = ec2.create_internet_gateway()
        internet_gateway.attach_to_vpc(VpcId=vpc.vpc_id)

        # Create Route Table (public route)
        route_table = vpc.create_route_table()
        route_ig_ipv4 = route_table.create_route(
            DestinationCidrBlock="0.0.0.0/0", GatewayId=internet_gateway.internet_gateway_id
        )

        # Create a subnet in our VPC
        subnet = vpc.create_subnet(
        CidrBlock="10.0.0.0/24", AvailabilityZone=availability_zone
        )

        # Associate the route table with subnet
        route_table.associate_with_subnet(SubnetId=subnet.id)

        # Create Security group
        security_group = vpc.create_security_group(
            GroupName="sample-name", Description="A sample description"
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
            ImageId="ami-835b4efa",
            InstanceType="t2.micro",
            MaxCount=1, #Required
            MinCount=1, #Required
            KeyName="sample_hack",
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
        instances[0].wait_until_running()
        # For some reason, public IP is not present in the instance object. reload() method loads the public IP.
        instances[0].reload()
        public_ip = instances[0].public_ip_address
        return public_ip

    subnet_id, security_group_id = _deploy_vpc(vpc_name=VPC_NAME, availability_zone=AWS_AVAILABILITY_ZONE)
    public_ip_addr = _deploy_vm(subnet_id=subnet_id, security_group_id=security_group_id, availability_zone=AWS_AVAILABILITY_ZONE)
    
    yield ComputeHandle(host=public_ip_addr, port=22, username=ADMIN_USERNAME)


def create_compute_ssh_client(compute):
    """
    Given the handle provided from `create_compute_instance`,
    create a `paramiko.client.SSHClient`

    be sure to `.connect()` to the machine before returning the SSHClient handle.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #client.load_system_host_keys()
    file_loc = os.path.expanduser("~\Documents\keys\sample_hack.pem")
    privkey = paramiko.RSAKey.from_private_key_file(file_loc)
    import pdb;
    client.connect(hostname=compute.host, port=compute.port, username=compute.username, pkey=privkey)
    pdb.set_trace()

    return client
