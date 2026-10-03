import pulumi_aws as aws

build_artifacts = aws.s3.Bucket(
    "codedeploy-build-artifacts",
    force_destroy=True,
)
