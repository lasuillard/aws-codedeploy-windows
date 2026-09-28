import pulumi_aws as aws

from . import asg, common
from .components.iam import Role

app = aws.codedeploy.Application(
    "app",
    name=common.full_name,
    compute_platform="Server",
)
role = (
    Role(
        "codedeploy",
        name=f"{common.full_name}-codedeploy",
    )
    .assumable(services=["codedeploy.amazonaws.com"])
    .with_policies(arns=[aws.iam.ManagedPolicy.AWS_CODE_DEPLOY_ROLE])
    .build()
)
deployment_group = aws.codedeploy.DeploymentGroup(
    "app",
    app_name=app.name,
    deployment_group_name=f"{common.full_name}-windows-fleet",
    service_role_arn=role.arn,
    autoscaling_groups=[asg.asg.name],
    deployment_config_name="CodeDeployDefault.AllAtOnce",  # * For testing only
    auto_rollback_configuration={
        "enabled": True,
        "events": ["DEPLOYMENT_FAILURE"],
    },
)
