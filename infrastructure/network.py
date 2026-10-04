import pulumi_awsx as awsx

vpc = awsx.ec2.Vpc(
    "vpc",
    cidr_block="172.31.0.0/16",
    number_of_availability_zones=2,  # >= 2 required for ALB
    enable_dns_hostnames=True,
    enable_dns_support=True,
    subnet_strategy=awsx.ec2.SubnetAllocationStrategy.AUTO,
    nat_gateways={
        "strategy": awsx.ec2.NatGatewayStrategy.SINGLE,  # For cost-saving
    },
)
