#!/usr/bin/env bash

: '
Simple Vagrant wrapper to inject additional functionalities.
'

set -o errexit
set -o nounset
set -o pipefail

cd "$(git rev-parse --show-toplevel)"
git archive HEAD --format zip --output lab/windows-server/app.zip
cd -

vagrant "$@"
