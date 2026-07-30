#!/bin/bash

set -ouex pipefail

# Copy the contents of system_files/ of the git repo to /
cp -avf "/ctx/system_files"/. /

### Phase 0 / Phase 1 — minimal Arcalium identity
# Do not layer ordinary desktop apps into the immutable image.
# Do not replace the Bazzite kernel or NVIDIA stack.
# Control Centre and first-boot wizard come after the base image + ISO workflow is proven.

mkdir -p /usr/share/arcalium /etc/arcalium
install -Dm0644 /ctx/assets/arcalium-wallpaper.png \
    /usr/share/wallpapers/arcalium-wallpaper.png

# Primary mark (arccleanSVG) → application menu / distributor icons.
# Wordmark (ARG_fullSVG) → /usr/share/arcalium for splash and Plymouth.
# The ctx stage copies build_files/ to /, so siblings of this script are at /ctx.
python3 /ctx/install_logos.py /ctx/assets

# Plasma splash currently loads images/bazzite_logo.svgz from the active
# look-and-feel package. Replace that file in place wherever it exists so the
# wordmark appears on the boot-to-desktop splash without rewriting Splash.qml.
while IFS= read -r -d '' splash_logo; do
    gzip -nc /usr/share/arcalium/logo-wordmark.svg >"${splash_logo}"
done < <(find /usr/share/plasma/look-and-feel -type f -name 'bazzite_logo.svgz' -print0 2>/dev/null || true)

# Plymouth boot splash (post-GRUB) uses the spinner theme's watermark.png —
# including via the default bgrt theme, whose ImageDir points here. Bazzite's
# file is 149×43; our wordmark is taller, so render at ~256×121 to keep text
# readable. The initramfs also carries a copy; it is rebuilt at the end of this
# script.
magick -background none -density 300 \
    /usr/share/arcalium/logo-wordmark.svg \
    -resize 256x121 \
    PNG32:/usr/share/plymouth/themes/spinner/watermark.png
install -Dm0644 /usr/share/plymouth/themes/spinner/watermark.png \
    /usr/share/arcalium/plymouth-watermark.png

# Replace the Bazzite identity strings Plymouth shows as the loading title.
# Keep ID=bazzite so the live Anaconda profile (os_id=bazzite) and any tooling
# that keys off ID keep working; NAME/PRETTY_NAME are what users see.
sed -i \
    -e 's/^NAME=.*/NAME="Arcalium OS"/' \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="Arcalium OS NVIDIA Edition"/' \
    -e 's/^ID_LIKE=.*/ID_LIKE="fedora bazzite"/' \
    -e 's/^VARIANT=.*/VARIANT="NVIDIA Edition"/' \
    -e 's/^VARIANT_ID=.*/VARIANT_ID=nvidia/' \
    -e 's/^LOGO=.*/LOGO=arcalium-logo/' \
    -e 's/^DEFAULT_HOSTNAME=.*/DEFAULT_HOSTNAME="arcalium"/' \
    -e 's/^HOME_URL=.*/HOME_URL="https:\/\/github.com\/kaal22\/arcalium-nvidia"/' \
    -e 's/^DOCUMENTATION_URL=.*/DOCUMENTATION_URL="https:\/\/github.com\/kaal22\/arcalium-nvidia"/' \
    -e 's/^SUPPORT_URL=.*/SUPPORT_URL="https:\/\/github.com\/kaal22\/arcalium-nvidia"/' \
    -e 's/^BUG_REPORT_URL=.*/BUG_REPORT_URL="https:\/\/github.com\/kaal22\/arcalium-nvidia\/issues"/' \
    -e 's/^BOOTLOADER_NAME=.*/BOOTLOADER_NAME="Arcalium OS"/' \
    /usr/lib/os-release
# /etc/os-release is a symlink to ../usr/lib/os-release on this base.
grep -E '^(NAME|PRETTY_NAME|ID|ID_LIKE|VARIANT)=' /usr/lib/os-release

cat >/usr/share/arcalium/os-release.snippet <<'EOF'
NAME="Arcalium OS"
PRETTY_NAME="Arcalium OS NVIDIA Edition"
ID_LIKE="fedora bazzite"
VARIANT="NVIDIA Edition"
VARIANT_ID="nvidia"
ARCALIUM_EDITION="nvidia"
ARCALIUM_CHANNEL="dev"
EOF

cat >/etc/arcalium/image-info.json <<'EOF'
{
  "schemaVersion": 1,
  "product": "Arcalium OS",
  "edition": "NVIDIA Edition",
  "imageName": "arcalium-os-nvidia",
  "channel": "dev",
  "baseImage": "ghcr.io/ublue-os/bazzite-nvidia-open:stable",
  "independentProjectNotice": "Arcalium OS is an independent project built on Bazzite and is not affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project."
}
EOF

# Hostname migration for machines that still carry the stock "bazzite" name
# after rebasing. New installs already get DEFAULT_HOSTNAME=arcalium and
# /etc/hostname from system_files.
chmod 0755 /usr/libexec/arcalium-migrate-hostname
systemctl enable arcalium-migrate-hostname.service

# Keep podman.socket available (inherited template default; idempotent).
systemctl enable podman.socket

# Plymouth draws the boot splash from the initramfs but the shutdown splash from
# /usr, so branding applied only to /usr shows Arcalium on shutdown and stock
# Bazzite on boot. The initramfs in the base image was generated before this
# layer, so rebuild it with the arguments dracut recorded in the original
# (visible via `lsinitrd`) and confirm our watermark and os-release land inside.
for moddir in /usr/lib/modules/*/; do
    [[ -f "${moddir}initramfs.img" ]] || continue
    kver="$(basename "${moddir}")"
    dracut --no-hostonly --kver "${kver}" --reproducible --zstd -v \
        --add ostree --add fido2 --force "${moddir}initramfs.img"
    chmod 0600 "${moddir}initramfs.img"

    lsinitrd "${moddir}initramfs.img" -f usr/share/plymouth/themes/spinner/watermark.png |
        cmp - /usr/share/plymouth/themes/spinner/watermark.png
    # os-release inside the initramfs is a symlink to initrd-release, which
    # dracut derives from /usr/lib/os-release and Plymouth reads for its title.
    lsinitrd "${moddir}initramfs.img" -f usr/lib/initrd-release |
        grep -q '^NAME="Arcalium OS"$'
done
