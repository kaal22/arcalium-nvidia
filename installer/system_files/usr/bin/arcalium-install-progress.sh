#!/usr/bin/bash
# Live-session progress window for the Anaconda deployment step.
#
# Anaconda shows one undifferentiated step while ostree unpacks the entire OS image,
# which on a slow disk looks identical to a hang for twenty minutes or more. This
# window reports bytes actually landing on the target so a tester can tell the
# difference between slow and stuck. It is read-only and never touches the install.

set -uo pipefail

# Anaconda mounts the physical root at /mnt/sysroot for ostree installs and
# /mnt/sysimage for package installs; accept whichever appears.
target=""
deadline=$((SECONDS + 900))
while ((SECONDS < deadline)); do
    for candidate in /mnt/sysroot /mnt/sysimage; do
        if mountpoint -q "$candidate"; then
            target="$candidate"
            break
        fi
    done
    [[ -n "$target" ]] && break
    sleep 2
done
[[ -n "$target" ]] || exit 0

used_at_start=$(df -B1 --output=used "$target" | tail -n1)
started=$SECONDS

report() {
    while mountpoint -q "$target"; do
        pgrep -f anaconda >/dev/null || break

        used=$(df -B1 --output=used "$target" | tail -n1)
        written=$((used - used_at_start))
        ((written < 0)) && written=0
        elapsed=$((SECONDS - started))
        ((elapsed < 1)) && elapsed=1

        awk -v b="$written" -v e="$elapsed" 'BEGIN {
            printf "# %.1f GiB written  -  %d:%02d elapsed  -  %d MiB/s\n",
                b / 1073741824, e / 60, e % 60, (b / e) / 1048576
        }'
        sleep 3
    done
    echo "100"
}

# --pulsate because there is no trustworthy total: the target uses btrfs zstd
# compression, so bytes on disk are always well below the image size.
report | yad \
    --progress \
    --pulsate \
    --auto-close \
    --on-top \
    --center \
    --width=460 \
    --title='Installing Arcalium OS' \
    --text='Unpacking the OS image onto the disk. This takes 15-40 minutes and is slowest in a virtual machine. The installer window may look frozen while this runs.' \
    --button='Hide:0' ||
    true
