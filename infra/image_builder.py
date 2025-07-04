from pathlib import Path

import pulumi_aws as aws

from . import asg, components, dynamic, metadata, vpc

partition = aws.get_partition().partition
region = aws.get_region().name
account_id = aws.get_caller_identity().account_id

# EC2 Image Builder Infrastructure
# ----------------------------------------------------------------------------
security_group = aws.ec2.SecurityGroup(
    "imagebuilder",
    name=f"{metadata.full_name}-imagebuilder",
    description="Security group for instances managed by EC2 Image Builder.",
    vpc_id=vpc.vpc.vpc_id,
    ingress=[],
    egress=[
        # Allow all outbound traffic
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
)
instance_role = (
    components.Role(
        "imagebuilder-instance-role",
        name=f"{metadata.full_name}-imagebuilder",
    )
    .assumable(services=["ec2.amazonaws.com"])
    .with_policies(
        arns=[
            aws.iam.ManagedPolicy.AMAZON_SSM_MANAGED_INSTANCE_CORE,
            aws.iam.ManagedPolicy.EC2_INSTANCE_PROFILE_FOR_IMAGE_BUILDER,
            aws.iam.ManagedPolicy.EC2_INSTANCE_PROFILE_FOR_IMAGE_BUILDER_ECR_CONTAINER_BUILDS,
        ],
    )
    .build()
)
instance_profile = aws.iam.InstanceProfile(
    "imagebuilder",
    name=f"{metadata.full_name}-imagebuilder",
    role=instance_role.name,
)
default_infra_config = aws.imagebuilder.InfrastructureConfiguration(
    "default",
    name=f"{metadata.full_name}-imagebuilder",
    description="Default image builder infrastructure configuration.",
    instance_profile_name=instance_profile.name,
    instance_types=["t3a.large", "t3.large", "t3a.medium", "t3.medium"],
    subnet_id=vpc.vpc.private_subnet_ids[0],
    security_group_ids=[security_group.id],
)

# Image Build Pipeline for Windows Server 2022 with CodeDeploy
# ----------------------------------------------------------------------------
# * AutoLogon configuration gets removed by the Image Builder service (SysPrep),
# * so each instance should do on their own user data script to enable it
install_kftcvan_security_program = aws.imagebuilder.Component(
    "install-kftcvan-security-program",
    name="Install-KFTCVAN-Security-Program",
    version="1.0.0",
    platform="Windows",
    supported_os_versions=["Microsoft Windows Server 2022"],
    data=(Path(__file__).parent / "install-kftcvan-security-program.yaml").read_text(),
    skip_destroy=False,
)
image_name = f"{metadata.full_name}-imagebuilder"
image_recipe = aws.imagebuilder.ImageRecipe(
    "windows-fleet",
    name=image_name,
    description="Build recipe for Windows Server 2022 with CodeDeploy and extra packages.",
    version="1.0.0",
    parent_image=f"arn:{partition}:imagebuilder:{region}:aws:image/windows-server-2022-english-full-base-x86/x.x.x",
    components=[
        {
            "component_arn": f"arn:{partition}:imagebuilder:{region}:aws:component/amazon-cloudwatch-agent-windows/x.x.x",
            "parameters": [],
        },
        {
            "component_arn": f"arn:{partition}:imagebuilder:{region}:aws:component/aws-codedeploy-agent-windows/x.x.x",
            "parameters": [
                {
                    "name": "SetAgentDisabled",
                    "value": "no",
                },
            ],
        },
        {
            "component_arn": f"arn:{partition}:imagebuilder:{region}:aws:component/chocolatey/x.x.x",
            "parameters": [],
        },
        {
            "component_arn": f"arn:{partition}:imagebuilder:{region}:aws:component/python-3-windows/3.12.0",
            "parameters": [],
        },
        {
            "component_arn": install_kftcvan_security_program.arn,
            "parameters": [],
        },
    ],
    working_directory="C:/",
)
# Currently it's not possible to set the log group name in the image recipe
# -- it is automatically created by the Image Builder service.
log_group = aws.cloudwatch.LogGroup(
    "imagebuilder",
    name=f"/aws/imagebuilder/{image_name}",
    retention_in_days=7,
)
distro_config = aws.imagebuilder.DistributionConfiguration(
    "windows-fleet",
    name=f"{metadata.full_name}-imagebuilder",
    description="Distribution configuration for Windows Server 2022 with CodeDeploy.",
    distributions=[
        {
            "region": region,
            "ami_distribution_configuration": {
                # BUG: AMI name format shown in console like: "aws-codedeploy-windows-{{" (but works OK)
                "name": metadata.full_name + "-{{ imagebuilder:buildDate }}",
            },
            "launch_template_configurations": [
                {
                    "account_id": account_id,
                    "launch_template_id": asg.launch_template.id,
                    "default": True,
                },
            ],
        },
    ],
)

image_pipeline = aws.imagebuilder.ImagePipeline(
    "windows-fleet",
    name=f"{metadata.full_name}-imagebuilder",
    description="Image build pipeline for Windows Server 2022 with CodeDeploy.",
    image_recipe_arn=image_recipe.arn,
    execution_role=aws.iam.get_role("AWSServiceRoleForImageBuilder").arn,
    infrastructure_configuration_arn=default_infra_config.arn,
    distribution_configuration_arn=distro_config.arn,
    workflows=[
        {
            "workflowArn": f"arn:{partition}:imagebuilder:{region}:aws:workflow/build/build-image/x.x.x",
        },
        # ! Skipping the test workflow for now, but recommended for production
    ],
)
dynamic.TriggerImagePipeline(
    "windows-fleet-initial-build",
    image_pipeline_arn=image_pipeline.arn,
    region=region,
)
dynamic.CleanupImagePipeline(
    "windows-fleet-cleanup",
    image_pipeline_name=image_pipeline.name,
    region=region,
)

# Output Resource Lifecycle
# ----------------------------------------------------------------------------
# Set up short-lived lifecycle policy to prevent being charged for unused AMIs
# * This lifecycle may not be helpful for deleting AMIs not managed by this IaC,
# * because the resources will be deleted on stack destroy, including this policy.
lifecycle_policy_role = (
    components.Role(
        "imagebuilder-lifecycle-role",
        name=f"{metadata.full_name}-imagebuilder",
    )
    .assumable(services=["imagebuilder.amazonaws.com"])
    .with_policies(
        arns=[
            aws.iam.ManagedPolicy.EC2_IMAGE_BUILDER_LIFECYCLE_EXECUTION_POLICY,
        ],
    )
    .build()
)
aws.imagebuilder.LifecyclePolicy(
    "imagebuilder-lifecycle",
    name=f"{metadata.full_name}-imagebuilder",
    execution_role=lifecycle_policy_role.arn,
    resource_type="AMI_IMAGE",
    policy_details=[
        {
            # Keep only latest 5 AMIs
            "action": {"type": "DELETE"},
            "filter": {
                "type": "AGE",
                "unit": "DAYS",
                "value": 1,
                "retain_at_least": 5,
            },
        },
    ],
    resource_selection={
        "recipes": [
            {
                "name": image_recipe.name,
                "semantic_version": image_recipe.version,
            },
        ],
    },
)
