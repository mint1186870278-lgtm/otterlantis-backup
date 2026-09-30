#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-https://play.otterlantis.com}"
base_url="${base_url%/}"

check_header() {
  local path="$1"
  local header="$2"
  local expected="$3"
  local headers
  headers="$(mktemp)"
  curl -sSI "${base_url}${path}" > "$headers"
  if awk -v h="$header" -v e="$expected" '
    BEGIN { IGNORECASE = 1; ok = 0 }
    $0 ~ "^" h ":" && index(tolower($0), tolower(e)) > 0 { ok = 1 }
    END { exit ok ? 0 : 1 }
  ' "$headers"; then
    printf 'PASS\t%s\t%s contains %s\n' "$path" "$header" "$expected"
  else
    printf 'FAIL\t%s\t%s missing %s\n' "$path" "$header" "$expected"
    sed -n '1,30p' "$headers" | sed 's/^/  /'
    rm -f "$headers"
    return 1
  fi
  rm -f "$headers"
}

check_header "/index.html" "cache-control" "no-cache"
check_header "/assets/SectionParkour-Ba-Fk1Jk.js" "cache-control" "immutable"
check_header "/model-site/scene-terrain-opt.glb" "cache-control" "max-age=2592000"
check_header "/model-site/scene-terrain-opt.glb" "content-type" "model/gltf-binary"
check_header "/model-site/scene-terrain-opt.glb" "access-control-allow-origin" "*"

