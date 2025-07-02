import pulumi_awsx as awsx

from . import metadata

vpc = awsx.ec2.Vpc(
    metadata.full_name,
    cidr_block="172.31.0.0/16",
    number_of_availability_zones=3,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    subnet_strategy=awsx.ec2.SubnetAllocationStrategy.AUTO,
    nat_gateways={
        "strategy": awsx.ec2.NatGatewayStrategy.SINGLE,
    },
)
