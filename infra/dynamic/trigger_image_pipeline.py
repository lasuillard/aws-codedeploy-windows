from typing import Any

import boto3
from pulumi import Input, ResourceOptions
from pulumi.dynamic import CreateResult, Resource, ResourceProvider


class _Provider(ResourceProvider):
    def create(self, props: Any) -> CreateResult:
        client_token = props["client_token"]

        session = boto3.Session(region_name=props.get("region", None))
        imagebuilder = session.client("imagebuilder")
        response = imagebuilder.start_image_pipeline_execution(
            imagePipelineArn=props["image_pipeline_arn"],
            clientToken=client_token,
        )

        return CreateResult(
            id_=client_token,
            outs={"image_build_version_arn": response["imageBuildVersionArn"], **props},
        )


class TriggerImagePipeline(Resource):
    """Trigger an AWS Image Builder pipeline to build an image."""

    def __init__(  # noqa: D107
        self,
        resource_name: str,
        opts: ResourceOptions | None = None,
        *,
        image_pipeline_arn: Input[str],
        client_token: Input[str] | None = None,
        region: Input[str] | None = None,
    ) -> None:
        super().__init__(
            _Provider(),
            resource_name,
            {
                "image_pipeline_arn": image_pipeline_arn,
                "client_token": client_token or resource_name,
                "region": region,
            },
            opts,
        )
