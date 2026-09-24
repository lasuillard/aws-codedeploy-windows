from pulumi_extra.contrib.aws import register_auto_tagging

register_auto_tagging()

from infrastructure import (  # noqa: F401, E402
    alb,
    asg,
    codedeploy,
    codedeploy_application,
    export,
    github,
    image_builder,
    vpc,
)
