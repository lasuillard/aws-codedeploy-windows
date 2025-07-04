from pulumi import export

from . import alb, asg, codedeploy, codedeploy_application

# SSH Key to access the Windows instances in the ASG
export("asg.ssh-key.private-key", asg.ssh_key.private_key_pem)

# CodeDeploy configuration to deploy the application
export(
    "codedeploy.build-artifacts",
    codedeploy.build_artifacts.bucket,
)
export(
    "codedeploy.application-name",
    codedeploy_application.app.name,
)
export(
    "codedeploy.deployment-group-name",
    codedeploy_application.deployment_group.deployment_group_name,
)

# ALB domain name to access the application
# TODO(lasuillard): Configure Route53 and ACM for HTTPS
export(
    "alb.dns-name",
    alb.load_balancer.dns_name,
)
