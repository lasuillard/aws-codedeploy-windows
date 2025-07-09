#!/usr/bin/env bash

: '
Script to deploy the application (uploaded to S3) using AWS CodeDeploy.
'

set -o nounset
set -o errexit
set -o pipefail

application_name="$1"
deployment_group_name="$2"
echo "Deploying application: ${application_name}, deployment group: ${deployment_group_name}"

bucket="$3"
bucket_key="$4"
echo "Using S3 bucket: ${bucket}, key: ${bucket_key}"

aws deploy create-deployment \
    --application-name "$application_name" \
    --deployment-group-name "$deployment_group_name" \
    --deployment-config-name CodeDeployDefault.AllAtOnce \
    --s3-location "bucket=${bucket},bundleType=zip,key=${bucket_key}" \
    --ignore-application-stop-failures
