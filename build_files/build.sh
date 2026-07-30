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
# Wordmark (ARG_fullSVG) → /usr/share/arcalium for splash and later Plymouth.
python3 /ctx/build_files/install_logos.py /ctx/assets

# Plasma splash currently loads images/bazzite_logo.svgz from the active
# look-and-feel package. Replace that file in place wherever it exists so the
# wordmark appears on the boot-to-desktop splash without rewriting Splash.qml.
while IFS= read -r -d '' splash_logo; do
    gzip -nc /usr/share/arcalium/logo-wordmark.svg >"${splash_logo}"
done < <(find /usr/share/plasma/look-and-feel -type f -name 'bazzite_logo.svgz' -print0 2>/dev/null || true)

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

# Keep podman.socket available (inherited template default; idempotent).
systemctl enable podman.socket
