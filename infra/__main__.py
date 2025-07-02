from pulumi_extra.contrib.aws import register_auto_tagging

register_auto_tagging()

from infra import alb, asg, codedeploy, image_builder, vpc  # noqa: E402, F401
