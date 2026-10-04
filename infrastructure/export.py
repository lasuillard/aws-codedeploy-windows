from pulumi import export

import app_lb
import app_server
import deployment
import deployment_artifact

# SSH Key to access the Windows instances via Fleet Manager
export("asg.ssh-key.private-key", app_server.ssh_key.private_key_pem)

# CodeDeploy configuration to deploy the application
export(
    "codedeploy.build-artifacts",
    deployment_artifact.build_artifacts.bucket,
)
export(
    "codedeploy.application-name",
    deployment.app.name,
)
export(
    "codedeploy.deployment-group-name",
    deployment.deployment_group.deployment_group_name,
)

# ALB domain name to access the application
export(
    "alb.dns-name",
    app_lb.load_balancer.dns_name,
)
