from pulumi import export

from . import alb, codedeploy, codedeploy_application

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

# TODO(lasuillard): Configure Route53 and ACM for HTTPS
export(
    "alb.dns-name",
    alb.load_balancer.dns_name,
)
