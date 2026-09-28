from pulumi_extra.contrib.aws import register_auto_tagging

register_auto_tagging()

from infrastructure import (  # noqa: F401, E402
    app_lb,
    app_server,
    common,
    deployment,
    export,
    github,
    imagebuilder,
    imagebuilder_components,
    network,
)
