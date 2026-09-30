#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template="$script_dir/nginx-dry-run.conf"
include_file="$script_dir/play-otterlantis-static-cache.include.conf"
rendered_config="${TMPDIR:-/tmp}/otter-nginx-dry-run.conf"

if ! command -v nginx >/dev/null 2>&1; then
  echo "nginx binary not found on this machine."
  echo "Copy this folder to a machine with Nginx and run:"
  echo "  $script_dir/validate-nginx-config.sh"
  exit 2
fi

sed "s#__PLAY_STATIC_CACHE_INCLUDE__#$include_file#g" "$template" > "$rendered_config"
nginx -t -c "$rendered_config"
