#!/usr/bin/env bash
# Builds a Toskar release for this computer from a toskar-core checkout:
# the headless archive, SHA256SUMS.txt, and install.sh, as a GitHub release
# has them, so the action can install it with release-url.
#
#   scripts/local-release.sh <toskar-core checkout> <release folder>
set -euo pipefail
core="$(cd "${1:?usage: local-release.sh <toskar-core checkout> <release folder>}" && pwd)"
out="${2:?usage: local-release.sh <toskar-core checkout> <release folder>}"
mkdir -p "$out"
out="$(cd "$out" && pwd)"
os="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$(uname -m)" in x86_64 | amd64) arch=amd64 ;; aarch64 | arm64) arch=arm64 ;; *) echo "unknown processor" >&2; exit 1 ;; esac
name="toskar-0.0.0-ci-${os}-${arch}-headless"
stage="$(mktemp -d)/$name"
mkdir -p "$stage/web"
# No web UI: a CI job only asks.
printf '<!doctype html><title>Toskar</title>\n' >"$stage/web/index.html"
(cd "$core" && CGO_ENABLED=0 go build -trimpath -o "$stage/toskar" ./cmd/daemon && CGO_ENABLED=0 go build -trimpath -o "$stage/toskarctl" ./cmd/devctl)
tar -C "$(dirname "$stage")" -czf "$out/$name.tar.gz" "$name"
cp "$core/scripts/install.sh" "$out/install.sh"
(cd "$out" && if command -v sha256sum >/dev/null; then sha256sum "$name.tar.gz"; else shasum -a 256 "$name.tar.gz"; fi >SHA256SUMS.txt)
echo "A release for ${os}/${arch} is in $out"
