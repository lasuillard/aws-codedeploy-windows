from pathlib import Path

import pulumi_aws as aws

components_dir = Path(__file__).parent / "imagebuilder-components"
install_kftcvan_security_program = aws.imagebuilder.Component(
    "install-kftcvan-security-program",
    name="Install-KFTCVAN-Security-Program",
    version="1.0.0",
    platform="Windows",
    supported_os_versions=["Microsoft Windows Server 2022"],
    data=(components_dir / "install-kftcvan-security-program.yaml").read_text(),
    skip_destroy=False,
)
