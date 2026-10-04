import base64
from pathlib import Path

import pulumi_aws as aws
from pulumi import Output, ResourceOptions
from pulumi_extra import render_template

import app_lb
import common
import deployment_artifact
import network
from components.iam import Role

# NOTE: AMI built from image builder is not available at the provisioning time,
#       so we need to trigger a new build to get the latest AMI and distribute it
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[{"name": "name", "values": ["Windows_Server-2022-English-Full-Base-*"]}],
)
security_group = aws.ec2.SecurityGroup(
    "windows-fleet",
    name=f"{common.full_name}-windows-fleet",
    vpc_id=network.vpc.vpc_id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "security_groups": [app_lb.sg.id],
        },
    ],
    egress=[
        # Allow all outbound traffic
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
)
instance_role = (
    Role(
        "windows-fleet",
        name=f"{common.full_name}-windows-fleet",
    )
    .with_policies(
        arns=[
            aws.iam.ManagedPolicy.AMAZON_SSM_MANAGED_INSTANCE_CORE,
            aws.iam.ManagedPolicy.AMAZON_SSM_PATCH_ASSOCIATION,
            aws.iam.ManagedPolicy.CLOUD_WATCH_AGENT_SERVER_POLICY,
        ],
        documents=[
            {
                "statements": [
                    {
                        "sid": "GetBuildArtifactsForCodeDeploy",
                        "effect": "Allow",
                        "actions": ["s3:Get*", "s3:List*"],
                        "resources": [
                            deployment_artifact.build_artifacts.arn,
                            Output.concat(
                                deployment_artifact.build_artifacts.arn, "/*"
                            ),
                        ],
                    },
                ],
            },
        ],
    )
    .build()
)
instance_profile = aws.iam.InstanceProfile(
    "windows-fleet",
    name=f"{common.full_name}-windows-fleet",
    role=instance_role.name,
)
launch_template = aws.ec2.LaunchTemplate(
    "windows-fleet",
    opts=ResourceOptions(
        ignore_changes=[
            # Only provide initial default; managed by EC2 Image Builder
            "description",
            "image_id",
        ],
    ),
    name=f"{common.full_name}-windows-fleet",
    update_default_version=True,
    image_id=ami.id,
    instance_requirements={
        "vcpu_count": {"min": 2, "max": 4},
        "memory_mib": {"min": 4_096, "max": 8_192},
        "instance_generations": ["current"],
        "burstable_performance": "included",
        "spot_max_price_percentage_over_lowest_price": 100,
    },
    iam_instance_profile={"arn": instance_profile.arn},
    user_data=render_template(  # ty: ignore[missing-argument]
        Path(__file__).parent / "Bootstrap.userdata.jinja",
        inputs={},
    ).apply(
        lambda text: base64.b64encode(text.encode()).decode("utf-8")  # ty: ignore[invalid-argument-type]
    ),
    vpc_security_group_ids=[security_group.id],
    monitoring={"enabled": True},
)

asg = aws.autoscaling.Group(
    "windows-fleet",
    opts=ResourceOptions(
        ignore_changes=["desired_capacity", "min_size", "max_size"],
    ),
    name=f"{common.full_name}-windows-fleet",
    vpc_zone_identifiers=network.vpc.private_subnet_ids,
    desired_capacity=1,
    min_size=1,
    max_size=3,
    health_check_type="EC2",
    target_group_arns=[app_lb.target_group.arn],
    mixed_instances_policy={
        "launch_template": {
            "launch_template_specification": {
                "launch_template_id": launch_template.id,
                "version": "$Latest",
            },
        },
        "instances_distribution": {
            "on_demand_base_capacity": 0,
            "on_demand_percentage_above_base_capacity": 0,
            "on_demand_allocation_strategy": "lowest-price",
            "spot_allocation_strategy": "price-capacity-optimized",
        },
    },
    instance_refresh={
        "strategy": "Rolling",
    },
    enabled_metrics=[
        aws.autoscaling.Metric.GROUP_MIN_SIZE,
        aws.autoscaling.Metric.GROUP_MAX_SIZE,
        aws.autoscaling.Metric.GROUP_DESIRED_CAPACITY,
        aws.autoscaling.Metric.GROUP_IN_SERVICE_INSTANCES,
        aws.autoscaling.Metric.GROUP_PENDING_INSTANCES,
        aws.autoscaling.Metric.GROUP_STANDBY_INSTANCES,
        aws.autoscaling.Metric.GROUP_TERMINATING_INSTANCES,
        aws.autoscaling.Metric.GROUP_TOTAL_INSTANCES,
    ],
    tags=[
        {
            "key": "Name",
            "value": f"{common.full_name}-windows-fleet",
            "propagate_at_launch": True,
        },
    ],
)
