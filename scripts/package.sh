#!/bin/sh
# Build the delivery zip. Excludes the third-party SDK copy used once to derive the API inventory, and caches.
# Usage: sh scripts/package.sh <catalog_root> <out.zip>
set -e
root="$1"; out="$2"
cd "$root"
# refuse to package anything that holds a credential or a personal identifier (set SCAN_DENY_FILE to a file outside the repo that lists the real ones)
python3 -I scripts/scan_secrets.py .
# regenerate everything from the sources, then validate and compile; the compiled files must not depend on what was left on disk
python3 -I scripts/gen_api_actions.py . >/dev/null
python3 -I scripts/gen_automation_actions.py . >/dev/null
python3 -I scripts/build_catalog.py .
rm -f "$out"
zip -qr "$out" . -x 'sources/*' -x '*/__pycache__/*' -x '*.pyc' -x 'deliver/*'
unzip -l "$out" | tail -1
# the files the blind evaluation agents were given must be the ones in the zip
echo "sha256 of the evaluated files now (compare with eval/results/run4_*/sandbox_files.sha256):"
sha256sum catalog.json index.md AGENT_GUIDE.md eval/tasks.json
for r in eval/results/run4_sonnet_a eval/results/run4_sonnet_b eval/results/run4_haiku; do
  if [ "$(sha256sum catalog.json index.md AGENT_GUIDE.md eval/tasks.json | cut -d' ' -f1)" = "$(cut -d' ' -f1 $r/sandbox_files.sha256)" ]; then echo "$r: same files as delivered"; else echo "$r: DIFFERENT from delivered files, rerun the evaluation"; fi
done
