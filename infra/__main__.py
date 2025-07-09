from pulumi_extra.contrib.aws import register_auto_tagging

register_auto_tagging()

from infra import (  # noqa: E402, F401
    alb,
    asg,
    codedeploy,
    codedeploy_application,
    export,
    github,
    image_builder,
    vpc,
)
