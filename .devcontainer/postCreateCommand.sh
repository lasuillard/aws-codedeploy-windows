#!/usr/bin/env bash

sudo chown --recursive "$(id --user):$(id --group)" ~
sudo chmod --recursive 600 ~/.aws
sudo chmod --recursive u=rwX,g=,o= ~/.aws
