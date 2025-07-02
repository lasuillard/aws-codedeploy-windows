import pulumi_aws as aws
import pulumi_random as random
from pulumi import Output

from . import metadata, vpc

security_group = aws.ec2.SecurityGroup(
    "app",
    name=f"{metadata.full_name}",
    vpc_id=vpc.vpc.vpc_id,
    ingress=[
        # Allow all inbound traffic
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    egress=[
        # Allow all outbound traffic
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
)
suffix = random.RandomString("alb-suffix", length=7, special=False, upper=False)
lb_name = Output.concat(f"{metadata.full_name}-", suffix.result)
load_balancer = aws.lb.LoadBalancer(
    "app",
    name=lb_name,
    load_balancer_type="application",
    subnets=vpc.vpc.public_subnet_ids,
    internal=False,
    security_groups=[security_group.id],
    idle_timeout=300,  # Scraping can take a while for complex sites
)

# * Not using HTTPS here to make this simple
listener_80 = aws.lb.Listener(
    "app-80",
    load_balancer_arn=load_balancer.arn,
    protocol="HTTP",
    port=80,
    default_actions=[
        {
            "type": "fixed-response",
            "fixed_response": {
                "status_code": "503",
                "content_type": "text/plain",
                "message_body": "Service Unavailable",
            },
        },
    ],
)

target_group = aws.lb.TargetGroup(
    "app-8000",
    name=f"{metadata.full_name}-8000",
    vpc_id=vpc.vpc.vpc_id,
    protocol="HTTP",
    port=8000,
    health_check={
        "enabled": True,
        "protocol": "HTTP",
        "path": "/",
        "matcher": "200-399",
        "interval": 30,
        "timeout": 10,
        "healthy_threshold": 2,
        "unhealthy_threshold": 5,
    },
    slow_start=60,
    deregistration_delay=60,
)
aws.lb.ListenerRule(
    "app-8000",
    listener_arn=listener_80.arn,
    priority=100,
    conditions=[
        {
            "path_pattern": {"values": ["*"]},
        },
    ],
    actions=[
        {
            "type": "forward",
            "forward": {"target_groups": [{"arn": target_group.arn}]},
        },
    ],
)
