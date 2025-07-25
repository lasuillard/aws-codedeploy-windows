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

wait="${5:-"1"}"
echo "Wait for deployment to complete: ${wait}"

deployment_id="$(
    aws deploy create-deployment \
        --application-name "$application_name" \
        --deployment-group-name "$deployment_group_name" \
        --deployment-config-name CodeDeployDefault.AllAtOnce \
        --s3-location "bucket=${bucket},bundleType=zip,key=${bucket_key}" \
        --ignore-application-stop-failures \
    | jq -r '.deploymentId'
)"
echo "Deployment started with ID: ${deployment_id}"

# Wait for the deployment to succeed
if [ -n "$wait" ]; then
    echo "Waiting for deployment to complete..."
    aws deploy wait deployment-successful --deployment-id "$deployment_id"
else
    echo "Skipping wait for deployment completion."
fi
