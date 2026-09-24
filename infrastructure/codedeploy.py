import pulumi_aws as aws

build_artifacts = aws.s3.BucketV2(
    "codedeploy-build-artifacts",
    force_destroy=True,
)
