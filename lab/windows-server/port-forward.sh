#!/usr/bin/env bash

: '
Open port forwarding from host to Windows VM for RDP access using socat.

Usage: ./port-forward.sh <host_port> <vm_port>
'

set -o nounset
set -o errexit
set -o pipefail

host_port="${1:-3389}"
vm_port="${2:-3389}"

# Get VM IP: e.g. 192.168.121.59
vm_ip="$(sudo vagrant ssh-config windows | sed -nr 's/HostName (.+)/\1/p' | xargs echo -n)"

exec socat "tcp-listen:${host_port},reuseaddr,fork" "tcp:${vm_ip}:${vm_port}"
