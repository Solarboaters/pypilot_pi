#!/usr/bin/env bash
set -euo pipefail
exec > >(tee evidence/runtime-test.log) 2>&1
flatpak info org.opencpn.OpenCPN
flatpak run --command=opencpn-cmd org.opencpn.OpenCPN print-abi | tee evidence/host-abi.txt
curl --fail --location --silent --show-error 'https://dl.cloudsmith.io/public/opencpn/pypilot-prod/raw/names/pypilot_pi-0.53.4.0-flatpak-aarch64-24.08-flatpak-tarball/versions/v0.53.4.0/pypilot_pi-0.53.4.0-aarch64_flatpak-24.08.tar.gz' -o evidence/original-24.08.tar.gz
sha256sum evidence/original-24.08.tar.gz > evidence/original-SHA256SUMS
set +e
flatpak run --filesystem="$PWD:ro" --command=opencpn-cmd org.opencpn.OpenCPN -v import-plugin "$PWD/evidence/original-24.08.tar.gz" > evidence/baseline-import.log 2>&1
baseline_rc=$?
set -e
echo "$baseline_rc" > evidence/baseline-exit.txt
if test "$baseline_rc" -ne 2; then
  flatpak run --devel --filesystem="$PWD:ro" --command=gdb org.opencpn.OpenCPN --batch -ex 'catch throw' -ex run -ex 'bt 25' --args /app/bin/opencpn-cmd -v import-plugin "$PWD/evidence/original-24.08.tar.gz" > evidence/baseline-backtrace.log 2>&1 || true
  exit 1
fi
grep -F 'Incompatible plugin detected' evidence/baseline-import.log
python3 ci/finalize-test-package.py
package=$(realpath package/*aarch64_flatpak-25.08.tar.gz)
sha256sum "$package" > evidence/tested-package-SHA256SUMS
if ! flatpak run --filesystem="$PWD:ro" --command=opencpn-cmd org.opencpn.OpenCPN -v import-plugin "$package" > evidence/fixed-import.log 2>&1; then
  flatpak run --devel --filesystem="$PWD:ro" --command=gdb org.opencpn.OpenCPN --batch -ex 'catch throw' -ex run -ex 'bt 25' --args /app/bin/opencpn-cmd -v import-plugin "$package" > evidence/fixed-backtrace.log 2>&1 || true
  exit 1
fi
echo 0 > evidence/fixed-import-exit.txt
# Test loading in the GUI; CLI listing aborts and leaves a failed-load stamp.
find "$HOME/.var/app/org.opencpn.OpenCPN" -name '*pypilot*' -print > evidence/installed-files.txt
test -s "$HOME/.var/app/org.opencpn.OpenCPN/lib/opencpn/libpypilot_pi.so"
/usr/bin/python3 ci/runtime-probe.py
