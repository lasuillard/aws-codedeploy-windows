from pulumi_extra.contrib.aws import register_auto_tagging

register_auto_tagging()

import app_lb  # noqa: F401, E402
import app_server  # noqa: F401, E402
import common  # noqa: F401, E402
import deployment  # noqa: F401, E402
import export  # noqa: F401, E402
import github  # noqa: F401, E402
import imagebuilder  # noqa: F401, E402
import imagebuilder_components  # noqa: F401, E402
import network  # noqa: F401, E402
