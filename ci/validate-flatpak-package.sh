#!/usr/bin/env bash
# Runs only in the disposable ARM64 validation runner; no steering hardware.
set -euo pipefail
exec > >(tee evidence/import-test.log) 2>&1
flatpak run --command=sh org.opencpn.OpenCPN -c 'ls /app/bin; uname -m'
flatpak run --command=opencpn-cmd org.opencpn.OpenCPN print-abi
package=$(realpath build/*aarch64_flatpak-25.08.tar.gz)
flatpak run --filesystem="$PWD:ro" --command=opencpn-cmd org.opencpn.OpenCPN -v import-plugin "$package"
echo 'Matching package import exit status: 0'
test -s "$HOME/.var/app/org.opencpn.OpenCPN/lib/opencpn/libpypilot_pi.so"
find "$HOME/.var/app/org.opencpn.OpenCPN" -name '*pypilot*' -print
echo 'Matching package import finished successfully.'
