#!/usr/bin/env bash
# One-shot ISO watch tick — exit 0 if still running, 2 if done OK, 3 if failed/idle
cd /home/kaal/arcalium-nvidia
LOG=output/iso-build.log

if grep -q '^==== DONE ' "${LOG}" 2>/dev/null; then
  echo STATE=DONE
  tail -n 25 "${LOG}"
  ls -lah output/Arcalium-Live.iso /mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso 2>/dev/null || true
  exit 2
fi

if pgrep -f 'just build-iso-live' >/dev/null || pgrep -f 'podman build' >/dev/null || pgrep -f 'titanoboa|mksquashfs|main.sh' >/dev/null; then
  echo STATE=RUNNING
  # last interesting line
  tail -n 8 "${LOG}" | sed 's/\r$//'
  exit 0
fi

# Process gone — check for failure
if grep -q 'error: recipe `build-iso-live` failed' "${LOG}" 2>/dev/null; then
  # Only fail if the *last* just attempt failed (after last CONTINUE/START)
  echo STATE=FAILED
  tail -n 40 "${LOG}"
  exit 3
fi

echo STATE=IDLE_UNKNOWN
tail -n 20 "${LOG}"
exit 3
