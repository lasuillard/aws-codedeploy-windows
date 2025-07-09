#!/usr/bin/env bash

: '
Script to create archive and upload the application (build artifacts) to S3.
'

set -o nounset
set -o errexit
set -o pipefail

bucket="$1"
bucket_key="$2"
echo "Uploading build artifacts to S3 bucket: ${bucket}, key: ${bucket_key}"

commit_sha="$(git rev-parse --short HEAD)"
filename="app-${commit_sha}.zip"
echo "Commit SHA: ${commit_sha}"

git archive --format zip --output "$filename" "$commit_sha" .
echo "Created archive: ${filename}"

aws s3 cp "$filename" "s3://${bucket}/${bucket_key}"
echo "Uploaded ${filename} to s3://${bucket}/${bucket_key}"
