from typing import Any

import boto3
from pulumi import Input, ResourceOptions, log
from pulumi.dynamic import CreateResult, Resource, ResourceProvider


class _Provider(ResourceProvider):
    def create(self, props: Any) -> CreateResult:
        return CreateResult(id_=props["image_pipeline_name"], outs=props)

    def delete(self, _id: str, props: Any) -> None:
        session = boto3.Session(region_name=props.get("region", None))
        ec2, imagebuilder = session.client("ec2"), session.client("imagebuilder")

        # Lookup Image Builder images to find AMIs and snapshots to delete
        images = imagebuilder.list_images(
            filters=[{"name": "name", "values": [_id]}],
        )
        image_arns = [v["arn"] for v in images["imageVersionList"]]
        image_arn_patterns = [f"{arn}/*" for arn in image_arns]
        log.info(f"Image ARNs to delete: {image_arns}")

        # AMIs to delete
        amis = ec2.describe_images(
            Filters=[
                {"Name": "tag:CreatedBy", "Values": ["EC2 Image Builder"]},
                {"Name": "tag:Ec2ImageBuilderArn", "Values": image_arn_patterns},
            ],
        )
        ami_ids = [img["ImageId"] for img in amis["Images"]]
        log.info(f"AMIs to delete: {ami_ids}")

        # Snapshots to delete
        snapshots = ec2.describe_snapshots(
            Filters=[
                {"Name": "tag:CreatedBy", "Values": ["EC2 Image Builder"]},
                {"Name": "tag:Ec2ImageBuilderArn", "Values": image_arn_patterns},
            ],
        )
        snapshot_ids = [snap["SnapshotId"] for snap in snapshots["Snapshots"]]
        log.info(f"Snapshots to delete: {snapshot_ids}")

        # Delete resources
        for ami_id in ami_ids:
            log.info(f"Deregistering AMI: {ami_id}")
            ec2.deregister_image(ImageId=ami_id)

        for snapshot_id in snapshot_ids:
            log.info(f"Deleting snapshot: {snapshot_id}")
            ec2.delete_snapshot(SnapshotId=snapshot_id)

        # * Delete images at last for cases of partial failures; if image is deleted,
        # * we can't find AMIs and snapshots to delete
        for image_arn in image_arns:
            log.info(f"Deleting image builder image: {image_arn}")
            image_build_versions = imagebuilder.list_image_build_versions(
                imageVersionArn=image_arn,
            )
            image_build_version_arns = [
                v["arn"] for v in image_build_versions["imageSummaryList"]
            ]
            for image_build_version_arn in image_build_version_arns:
                log.info(f"Deleting image build version: {image_build_version_arn}")
                imagebuilder.delete_image(imageBuildVersionArn=image_build_version_arn)

        log.info("Resources deleted successfully.")


class CleanupImagePipeline(Resource):
    """Cleanup outputs of an AWS Image Builder pipeline on resource destruction."""

    def __init__(  # noqa: D107
        self,
        name: str,
        opts: ResourceOptions | None = None,
        *,
        image_pipeline_name: Input[str],
        region: Input[str] | None = None,
    ) -> None:
        super().__init__(
            _Provider(),
            name,
            {
                "image_pipeline_name": image_pipeline_name,
                "region": region,
            },
            opts,
        )
