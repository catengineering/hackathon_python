import boto3
import datetime
from botocore.exceptions import ClientError

# Setup env. variables
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "us-west-2"
AWS_AVAILABILITY_ZONE = "us-west-2a"

client = boto3.client(
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

ec2 = boto3.resource(
    "ec2",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


# Create the VPC
vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16", AmazonProvidedIpv6CidrBlock=True)
client.modify_vpc_attribute( VpcId = vpc.id , EnableDnsHostnames = { 'Value': True } )

# Assign name to the vpc
vpc.create_tags(Tags=[{"Key": "Name", "Value": "sample_vpc"}])
vpc.wait_until_available()
print(vpc.id)

# Create an Internet Gateway and attach it to the VPC
internet_gateway = ec2.create_internet_gateway()
internet_gateway.attach_to_vpc(VpcId=vpc.vpc_id)
print(internet_gateway.id)

# Create Route Table (public route)
route_table = vpc.create_route_table()

# Create both IPv4 & IPv6 route
route_ig_ipv4 = route_table.create_route(
    DestinationCidrBlock="0.0.0.0/0", GatewayId=internet_gateway.internet_gateway_id
)
##route_ig_ipv6 = route_table.create_route(DestinationIpv6CidrBlock='::/0', GatewayId=internet_gateway.internet_gateway_id)
print(route_table.id)

# Create a subnet in our VPC
##ipv6_subnet_cidr = vpc.ipv6_cidr_block_association_set[0]['Ipv6CidrBlock']
##ipv6_subnet_cidr = ipv6_subnet_cidr[:-2] + '64'
subnet = vpc.create_subnet(
    CidrBlock="10.0.0.0/24", AvailabilityZone=AWS_AVAILABILITY_ZONE
)  # Ipv6CidrBlock=ipv6_subnet_cidr)

# Associate the route table with subnet
route_table.associate_with_subnet(SubnetId=subnet.id)

# Create Security group
sg = vpc.create_security_group(
    GroupName="sample-name", Description="A sample description"
)

ip_ranges = [{"CidrIp": "0.0.0.0/0"}]

##ip_v6_ranges = [{
##'CidrIpv6': '::/0'
##}]

perms = [
    {
        "IpProtocol": "TCP",
        "FromPort": 80,
        "ToPort": 80,
        "IpRanges": ip_ranges,
        ##'Ipv6Ranges': ip_v6_ranges
    },
    {
        "IpProtocol": "TCP",
        "FromPort": 443,
        "ToPort": 443,
        "IpRanges": ip_ranges,
        ##'Ipv6Ranges': ip_v6_ranges
    },
    {
        "IpProtocol": "TCP",
        "FromPort": 22,
        "ToPort": 22,
        "IpRanges": ip_ranges,  # Remember to change this!
        ##'Ipv6Ranges': ip_v6_ranges # Remember to change this!
    },
]

sg.authorize_ingress(IpPermissions=perms)
print(sg.id)

# Create instance
instances = ec2.create_instances(
    ImageId="ami-835b4efa",
    InstanceType="t2.micro",
    MaxCount=1,
    MinCount=1,
    KeyName="sample",
    Placement={"AvailabilityZone": AWS_AVAILABILITY_ZONE},
    NetworkInterfaces=[
        {
            "SubnetId": subnet.id,
            "DeviceIndex": 0,
            "AssociatePublicIpAddress": True,
            "Groups": [sg.group_id],
        }
    ],
)
instances[0].wait_until_running()

print(instances[0].id)

# Create EBS
ebs_vol = ec2.create_volume(Size=20, AvailabilityZone=AWS_AVAILABILITY_ZONE)

# Wait for the volume to become available
waiter = client.get_waiter("volume_available")
waiter.wait(VolumeIds=[ebs_vol.volume_id])

print(ebs_vol.id)

# Attach EBS to Ec2
attach_response = client.attach_volume(
        Device="/dev/sdf", InstanceId='i-07a38670ce8345', VolumeId='vol-0ad988ab18d387456'
 )


# # Detach volume
# detach_response = client.detach_volume(
#     Device='/dev/sdf',
#     Force=False,
#     InstanceId='i-0fd344b2886c4791b',
#     VolumeId='vol-0ad988ab18d387418'
# )
# waiter = client.get_waiter("volume_available")
# waiter.wait(VolumeIds=["vol-0ad988ab18d387418"])

# # Run commands on Ec2 instance
# response = ssm_client.send_command(
#              InstanceIds=[
#                 "i-07a38670ce8f32116" 
#                      ],
#              DocumentName="AWS-RunShellScript",
#              Parameters={
#                 'commands':['mount /dev/xvdf /data']
#                    },
#              )
# command_id = response['Command']['CommandId']
# output = ssm_client.get_command_invocation(
#       CommandId=command_id,
#       InstanceId='i-07a38670ce8f32116',
#     )
