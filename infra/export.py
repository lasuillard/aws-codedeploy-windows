from pulumi import export

from . import codedeploy, codedeploy_application

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
