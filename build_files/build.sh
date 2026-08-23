#!/bin/bash

set -ouex pipefail

# Copy the contents of system_files/ of the git repo to /
cp -avf "/ctx/system_files"/. /

### Phase 0 / Phase 1 — minimal Arcalium identity
# Do not layer ordinary desktop apps into the immutable image.
# Do not replace the Bazzite kernel or NVIDIA stack.
# Control Centre Overview MVP is built in the Containerfile control-centre stage
# and installed below from /ctx/control-centre/.

mkdir -p /usr/share/arcalium /etc/arcalium
install -Dm0644 /ctx/assets/arcalium-wallpaper.png \
    /usr/share/wallpapers/arcalium-wallpaper.png

# Runtime WebKit for the Tauri Control Centre binary.
if ! rpm -q webkit2gtk4.1 >/dev/null 2>&1; then
    dnf5 -y install webkit2gtk4.1 || dnf -y install webkit2gtk4.1
fi

# Setup / Control Centre "Open disk utility" launches Partition Manager.
# bazzite-nvidia-open does not ship it; without this the UI fell back to System Settings.
if ! rpm -q kde-partitionmanager >/dev/null 2>&1; then
    dnf5 -y install kde-partitionmanager || dnf -y install kde-partitionmanager
fi

if [[ -x /ctx/control-centre/arcalium-control-centre ]]; then
    install -Dm0755 /ctx/control-centre/arcalium-control-centre \
        /usr/bin/arcalium-control-centre
    if [[ -f /ctx/control-centre/io.arcalium.ControlCentre.png ]]; then
        for size in 48 64 128 256; do
            install -d "/usr/share/icons/hicolor/${size}x${size}/apps"
            # Same master PNG for each size; Plasma scales as needed.
            install -Dm0644 /ctx/control-centre/io.arcalium.ControlCentre.png \
                "/usr/share/icons/hicolor/${size}x${size}/apps/io.arcalium.ControlCentre.png"
        done
    fi
else
    echo "WARNING: Control Centre binary missing from /ctx/control-centre/" >&2
fi

# Local AI Assistant icon — Space Invaders-style pixel face (assets/).
if [[ -f /ctx/assets/io.arcalium.Assistant.png ]]; then
    for size in 48 64 128 256; do
        install -d "/usr/share/icons/hicolor/${size}x${size}/apps"
        src="/ctx/assets/io.arcalium.Assistant-${size}.png"
        if [[ ! -f "${src}" ]]; then
            src="/ctx/assets/io.arcalium.Assistant.png"
        fi
        install -Dm0644 "${src}" \
            "/usr/share/icons/hicolor/${size}x${size}/apps/io.arcalium.Assistant.png"
    done
fi

# Primary mark (arccleanSVG) → application menu / distributor icons.
# Wordmark (ARG_fullSVG) → /usr/share/arcalium for splash and Plymouth.
# The ctx stage copies build_files/ to /, so siblings of this script are at /ctx.
python3 /ctx/install_logos.py /ctx/assets

# Raster Kickoff marks (some Plasma/icon themes resolve PNG before SVG).
if command -v magick >/dev/null 2>&1; then
    for size in 48 64 128 256; do
        install -d "/usr/share/icons/hicolor/${size}x${size}/places"
        magick -background none /usr/share/arcalium/logo-mark.svg \
            -resize "${size}x${size}" \
            "PNG32:/usr/share/icons/hicolor/${size}x${size}/places/start-here-kde.png"
        cp -f "/usr/share/icons/hicolor/${size}x${size}/places/start-here-kde.png" \
            "/usr/share/icons/hicolor/${size}x${size}/places/distributor-logo.png"
        cp -f "/usr/share/icons/hicolor/${size}x${size}/places/start-here-kde.png" \
            "/usr/share/icons/hicolor/${size}x${size}/places/start-here.png"
    done
fi

# Taskbar pins come from the panel layout template, not from an update script.
python3 /ctx/patch_panel_pins.py

# Plasma splash loads images/*_logo.svgz from the active look-and-feel package.
# Replace Bazzite/Valve logos in place and point Splash.qml at arcalium_logo.svgz so
# upstream renames cannot silently leave a stock mark. Fail the build if nothing is patched.
#
# Splash.qml often pins both sourceSize.width and sourceSize.height (to `size` or a
# literal). That suits a square mark but squashes our ~2.1:1 wordmark. Qt derives the
# missing dimension from the source aspect ratio, so dropping the height line is enough.
splash_patched=0
wordmark_sum="$(sha256sum /usr/share/arcalium/logo-wordmark.svg | awk '{print $1}')"
mapfile -d '' -t splash_logos < <(
    find /usr/share/plasma/look-and-feel -type f \( \
        -name 'bazzite_logo.svgz' -o -name 'deck_logo.svgz' -o -name 'steamdeck_logo.svgz' \
    \) -print0 2>/dev/null || true
)
if [[ "${#splash_logos[@]}" -eq 0 ]]; then
    echo "ERROR: no Plasma splash logo (bazzite_logo/deck_logo) under look-and-feel — branding would silently revert." >&2
    find /usr/share/plasma/look-and-feel -type f -name '*logo*' 2>/dev/null | head -n 40 >&2 || true
    exit 1
fi
for splash_logo in "${splash_logos[@]}"; do
    [[ -n "${splash_logo}" ]] || continue
    splash_dir="$(dirname "${splash_logo}")"
    arcalium_logo="${splash_dir}/arcalium_logo.svgz"
    gzip -nc /usr/share/arcalium/logo-wordmark.svg >"${arcalium_logo}"
    # Keep upstream filename as a copy too (Splash.qml may still reference it until patched).
    cp -f "${arcalium_logo}" "${splash_logo}"

    replaced_sum="$(gzip -dc "${arcalium_logo}" | sha256sum | awk '{print $1}')"
    [[ "${replaced_sum}" == "${wordmark_sum}" ]] ||
        { echo "ERROR: ${arcalium_logo} does not match Arcalium wordmark" >&2; exit 1; }

    splash_qml="$(dirname "${splash_logo}")/../Splash.qml"
    [[ -f "${splash_qml}" ]] || continue

    # Point QML at our stable filename regardless of upstream logo name.
    sed -i -E 's#(source:[[:space:]]*")images/[^"]+_logo\.svgz(")#\1images/arcalium_logo.svgz\2#g' "${splash_qml}"
    grep -q 'images/arcalium_logo.svgz' "${splash_qml}" ||
        { echo "ERROR: ${splash_qml} was not patched to arcalium_logo.svgz" >&2; exit 1; }

    # Wordmark is wide: keep width, drop fixed height, force aspect-fit so the
    # logo cannot collapse to an empty/zero-height Image after re-pins.
    sed -i -E '/^[[:space:]]*sourceSize\.height:/d' "${splash_qml}"
    if ! grep -q 'fillMode:[[:space:]]*Image.PreserveAspectFit' "${splash_qml}"; then
        sed -i -E '/images\/arcalium_logo\.svgz/a\        fillMode: Image.PreserveAspectFit' "${splash_qml}"
    fi
    # Prefer a wider slot than a square `size` when upstream used sourceSize.width: size.
    sed -i -E 's#(sourceSize\.width:[[:space:]]*)size\b#\1Math.round(size * 2.2)#g' "${splash_qml}"

    grep -qE 'sourceSize\.width:[[:space:]]*(Math\.round\(size \* 2\.2\)|size|[0-9]+)' "${splash_qml}" ||
        { echo "ERROR: ${splash_qml} no longer sets sourceSize.width" >&2; exit 1; }
    if grep -nE 'sourceSize\.height' "${splash_qml}"; then
        echo "ERROR: ${splash_qml} still forces a fixed height on the logo" >&2
        exit 1
    fi
    splash_patched=$((splash_patched + 1))
done
[[ "${splash_patched}" -ge 1 ]] ||
    { echo "ERROR: Plasma splash logos found but no Splash.qml was patched" >&2; exit 1; }
echo "Plasma splash: patched ${splash_patched} look-and-feel logo(s)"

# Login greeter wallpaper — assert Arcalium defaults survived the base image.
[[ -f /usr/share/wallpapers/arcalium-wallpaper.png ]] ||
    { echo "ERROR: missing /usr/share/wallpapers/arcalium-wallpaper.png" >&2; exit 1; }
[[ -f /usr/lib/plasmalogin/defaults.conf ]] ||
    { echo "ERROR: missing /usr/lib/plasmalogin/defaults.conf" >&2; exit 1; }
grep -q 'arcalium-wallpaper.png' /usr/lib/plasmalogin/defaults.conf ||
    { echo "ERROR: plasmalogin defaults.conf does not reference arcalium-wallpaper.png" >&2; exit 1; }
grep -q 'file:///usr/share/wallpapers/arcalium-wallpaper.png' /usr/lib/plasmalogin/defaults.conf ||
    { echo "ERROR: plasmalogin defaults.conf must use file:// Image URIs" >&2; exit 1; }
grep -q 'WallpaperPlugin=org.kde.image' /usr/lib/plasmalogin/defaults.conf ||
    { echo "ERROR: plasmalogin defaults.conf missing WallpaperPlugin=org.kde.image" >&2; exit 1; }
[[ -f /usr/lib/plasmalogin/plasmalogin.conf.d/10-arcalium-wallpaper.conf ]] ||
    { echo "ERROR: missing plasmalogin.conf.d/10-arcalium-wallpaper.conf" >&2; exit 1; }

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
grep -qx 'NAME="Arcalium OS"' /usr/lib/os-release ||
    { echo "ERROR: /usr/lib/os-release NAME was not rewritten to Arcalium OS" >&2; exit 1; }
grep -qx 'PRETTY_NAME="Arcalium OS NVIDIA Edition"' /usr/lib/os-release ||
    { echo "ERROR: /usr/lib/os-release PRETTY_NAME was not rewritten" >&2; exit 1; }

# Konsole / shell banner: Bazzite dropped profile.d/user-motd.sh and points
# fastfetch aliases + ublue-motd at /usr/share/ublue-os/bazzite/*. Overwrite those
# targets so stock hooks cannot show Bazzite tips/logo after a re-pin.
#
# IMPORTANT: force-rewrite via heredoc (do not trust a prior /etc merge of the
# stock Bazzite file). Truncated stock aliases cause:
#   unexpected EOF while looking for matching `''
_arcalium_neofetch_profile='# Arcalium: fastfetch aliases (filename kept so we replace Bazzite stock).
# Real /usr/bin/neofetch + neowofetch wrappers also exist for non-alias callers.
alias neofetch='\''/usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc'\''
alias neowofetch='\''/usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc'\''
alias fastfetch='\''/usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc'\''
'
printf '%s\n' "${_arcalium_neofetch_profile}" >/etc/profile.d/bazzite-neofetch.sh
printf '%s\n' "${_arcalium_neofetch_profile}" >/etc/profile.d/zz-arcalium-fastfetch.sh
bash -n /etc/profile.d/bazzite-neofetch.sh
bash -n /etc/profile.d/zz-arcalium-fastfetch.sh

# Always replace ublue-motd with a tiny wrapper (stock script uses } / glow tips).
cat >/usr/libexec/ublue-motd <<'EOF'
#!/usr/bin/bash
# Arcalium: replace Bazzite tip/glow MOTD with our Konsole banner.
exec /usr/libexec/arcalium-motd
EOF
chmod 0755 /usr/libexec/ublue-motd
bash -n /usr/libexec/ublue-motd
bash -n /usr/libexec/arcalium-motd

[[ -f /etc/profile.d/user-motd.sh ]] ||
    { echo "ERROR: missing /etc/profile.d/user-motd.sh" >&2; exit 1; }
grep -q 'arcalium-motd' /etc/profile.d/user-motd.sh ||
    { echo "ERROR: user-motd.sh does not call arcalium-motd" >&2; exit 1; }
grep -q 'case $-' /etc/profile.d/user-motd.sh ||
    { echo "ERROR: user-motd.sh must guard for interactive shells" >&2; exit 1; }
[[ -f /etc/profile.d/bazzite-neofetch.sh ]] ||
    { echo "ERROR: missing /etc/profile.d/bazzite-neofetch.sh" >&2; exit 1; }
grep -q '/usr/share/arcalium/fastfetch.jsonc' /etc/profile.d/bazzite-neofetch.sh ||
    { echo "ERROR: bazzite-neofetch.sh aliases do not point at Arcalium fastfetch" >&2; exit 1; }
grep -q 'bazzite-bling-fastfetch' /etc/profile.d/bazzite-neofetch.sh &&
    { echo "ERROR: bazzite-neofetch.sh still references Bazzite bling helper" >&2; exit 1; }
[[ -f /usr/share/arcalium/fastfetch.jsonc && -f /usr/share/arcalium/logo.txt ]] ||
    { echo "ERROR: missing /usr/share/arcalium/fastfetch.jsonc or logo.txt" >&2; exit 1; }
[[ -f /usr/share/arcalium/motd-tips.txt ]] ||
    { echo "ERROR: missing /usr/share/arcalium/motd-tips.txt" >&2; exit 1; }
grep -q 'arcaliumctl ai launch' /usr/share/arcalium/motd-tips.txt ||
    { echo "ERROR: motd-tips.txt missing Local AI command" >&2; exit 1; }
grep -q 'arcaliumctl updates' /usr/share/arcalium/motd-tips.txt ||
    { echo "ERROR: motd-tips.txt missing updates commands" >&2; exit 1; }
[[ -x /usr/libexec/arcalium-motd ]] || chmod 0755 /usr/libexec/arcalium-motd
grep -q 'motd-tips.txt' /usr/libexec/arcalium-motd ||
    { echo "ERROR: arcalium-motd does not print motd-tips.txt" >&2; exit 1; }
grep -q 'exec /usr/libexec/arcalium-motd' /usr/libexec/ublue-motd ||
    { echo "ERROR: ublue-motd is not the Arcalium wrapper" >&2; exit 1; }
[[ -f /usr/share/fish/vendor_conf.d/arcalium-motd.fish ]] ||
    { echo "ERROR: missing fish arcalium-motd.fish" >&2; exit 1; }
[[ -f /usr/share/konsole/Arcalium.profile ]] ||
    { echo "ERROR: missing Konsole Arcalium.profile" >&2; exit 1; }
grep -q 'LoginShell=true' /usr/share/konsole/Arcalium.profile ||
    { echo "ERROR: Konsole Arcalium.profile must enable LoginShell" >&2; exit 1; }
[[ -f /etc/xdg/konsolerc ]] ||
    { echo "ERROR: missing /etc/xdg/konsolerc" >&2; exit 1; }
grep -q 'DefaultProfile=Arcalium.profile' /etc/xdg/konsolerc ||
    { echo "ERROR: konsolerc must default to Arcalium.profile" >&2; exit 1; }

if [[ -d /usr/share/ublue-os/bazzite ]]; then
    install -Dm0644 /usr/share/arcalium/fastfetch.jsonc \
        /usr/share/ublue-os/bazzite/fastfetch.jsonc
    install -Dm0644 /usr/share/arcalium/logo.txt \
        /usr/share/ublue-os/bazzite/logo.txt
fi
if [[ -x /usr/libexec/bazzite-fetch-image || -e /usr/libexec/bazzite-fetch-image ]]; then
    cat >/usr/libexec/bazzite-fetch-image <<'EOF'
#!/usr/bin/bash
# Arcalium: stock Bazzite image-line helper → live Arcalium image label.
exec /usr/libexec/arcalium-image-label
EOF
    chmod 0755 /usr/libexec/bazzite-fetch-image
fi
if [[ -x /usr/libexec/ublue-motd || -e /usr/libexec/ublue-motd ]]; then
    cat >/usr/libexec/ublue-motd <<'EOF'
#!/usr/bin/bash
# Arcalium: replace Bazzite tip/glow MOTD with our Konsole banner.
exec /usr/libexec/arcalium-motd
EOF
    chmod 0755 /usr/libexec/ublue-motd
fi
# Keep /usr/etc in sync when present (some rebases seed /etc from here).
if [[ -d /usr/etc/profile.d ]]; then
    install -Dm0644 /etc/profile.d/user-motd.sh /usr/etc/profile.d/user-motd.sh
    install -Dm0644 /etc/profile.d/bazzite-neofetch.sh /usr/etc/profile.d/bazzite-neofetch.sh
    install -Dm0644 /etc/profile.d/zz-arcalium-fastfetch.sh /usr/etc/profile.d/zz-arcalium-fastfetch.sh
    install -Dm0644 /etc/profile.d/zz-arcalium-motd.sh /usr/etc/profile.d/zz-arcalium-motd.sh
fi
grep -q '\*i\*)' /etc/profile.d/user-motd.sh ||
    { echo "ERROR: user-motd.sh interactive guard must use *i*) not bare i)" >&2; exit 1; }
[[ -f /etc/profile.d/zz-arcalium-motd.sh ]] ||
    { echo "ERROR: missing zz-arcalium-motd.sh safety-net MOTD" >&2; exit 1; }
[[ -f /usr/share/fish/vendor_conf.d/bazzite-neofetch.fish ]] ||
    { echo "ERROR: missing fish fastfetch alias override" >&2; exit 1; }
grep -q '/usr/share/arcalium/fastfetch.jsonc' /usr/share/fish/vendor_conf.d/bazzite-neofetch.fish ||
    { echo "ERROR: fish fastfetch aliases do not point at Arcalium" >&2; exit 1; }

# Channel baked at image build time (CI DEFAULT_TAG=dev). Promote :stable retags the
# same digest and does not rewrite this file — fastfetch / Control Centre prefer the
# live bootc image tag via /usr/libexec/arcalium-image-label and system.summarize().
ARCALIUM_CHANNEL="${ARCALIUM_CHANNEL:-dev}"

cat >/usr/share/arcalium/os-release.snippet <<EOF
NAME="Arcalium OS"
PRETTY_NAME="Arcalium OS NVIDIA Edition"
ID_LIKE="fedora bazzite"
VARIANT="NVIDIA Edition"
VARIANT_ID="nvidia"
ARCALIUM_EDITION="nvidia"
ARCALIUM_CHANNEL="${ARCALIUM_CHANNEL}"
EOF

cat >/etc/arcalium/image-info.json <<EOF
{
  "schemaVersion": 1,
  "product": "Arcalium OS",
  "edition": "NVIDIA Edition",
  "imageName": "arcalium-os-nvidia",
  "channel": "${ARCALIUM_CHANNEL}",
  "website": "https://getarcalium.com",
  "baseImage": "ghcr.io/ublue-os/bazzite-nvidia-open:stable",
  "independentProjectNotice": "Arcalium OS is an independent project built on Bazzite and is not affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project."
}
EOF

# Hostname migration for machines that still carry the stock "bazzite" name
# after rebasing. New installs already get DEFAULT_HOSTNAME=arcalium and
# /etc/hostname from system_files.
chmod 0755 /usr/libexec/arcalium-migrate-hostname
chmod 0755 /usr/libexec/arcalium-cleanup-bazzite-user
chmod 0755 /usr/libexec/arcalium-image-label
chmod 0755 /usr/libexec/arcalium-motd
chmod 0755 /usr/bin/neofetch
chmod 0755 /usr/bin/neowofetch
chmod 0755 /usr/bin/arcaliumctl
# Binary wrappers beat broken / missing aliases when something execs `neofetch`.
grep -q 'arcalium/fastfetch.jsonc' /usr/bin/neofetch ||
    { echo "ERROR: /usr/bin/neofetch is not the Arcalium fastfetch wrapper" >&2; exit 1; }
grep -q 'arcalium/fastfetch.jsonc' /usr/bin/neowofetch ||
    { echo "ERROR: /usr/bin/neowofetch is not the Arcalium fastfetch wrapper" >&2; exit 1; }
# Kickoff mark must exist in hicolor (install_logos also mirrors into Breeze).
[[ -f /usr/share/icons/hicolor/scalable/places/start-here-kde.svg ]] ||
    { echo "ERROR: missing Kickoff start-here-kde.svg" >&2; exit 1; }
[[ -f /usr/share/icons/hicolor/scalable/places/distributor-logo.svg ]] ||
    { echo "ERROR: missing distributor-logo.svg" >&2; exit 1; }
chmod 0755 /usr/bin/arcalium-heroic
chmod 0755 /usr/bin/arcalium-setup
chmod 0755 /usr/bin/arcalium-control-centre-launch
chmod 0755 /usr/bin/arcalium-assistant
# Plasma treats executable .desktop files on ~/Desktop as trusted launchers.
if [[ -f /etc/skel/Desktop/arcalium-control-centre.desktop ]]; then
    chmod 0755 /etc/skel/Desktop/arcalium-control-centre.desktop
fi
if [[ -f /usr/share/applications/io.arcalium.Assistant.desktop ]]; then
    chmod 0644 /usr/share/applications/io.arcalium.Assistant.desktop
fi
chmod 0755 /usr/bin/bazzite-steam
chmod 0755 /usr/bin/bazzite-steam-firstrun
chmod 0755 /usr/bin/bazzite-steam-bpm
chmod 0755 /usr/lib/arcalium/ai/assistant-session.sh
chmod 0755 /usr/lib/arcalium/ai/ensure-session.sh
chmod 0755 /usr/lib/arcalium/ai/install-session.sh
chmod 0755 /usr/lib/arcalium/apps/install-session.sh
chmod 0755 /usr/lib/arcalium/steam/harden-flatpak.sh
chmod 0755 /usr/lib/arcalium/flatpak/harden-nvidia.sh
chmod 0755 /usr/lib/arcalium/flatpak/nvidia-gl-tag.sh

# Stamp expected Flatpak GL.nvidia tag from the image's NVIDIA RPMs (no GPU needed).
# ISO payload build and runtime harden both consume this.
install -d /usr/share/arcalium
if ! /usr/lib/arcalium/flatpak/nvidia-gl-tag.sh >/usr/share/arcalium/flatpak-nvidia-gl.tag; then
    echo "ERROR: could not resolve Flatpak NVIDIA GL tag for this image." >&2
    exit 1
fi
echo "Flatpak NVIDIA GL tag: $(tr -d '[:space:]' </usr/share/arcalium/flatpak-nvidia-gl.tag)"

# Enable per-user cleanup of leftover Bazzite Portal autostart after rebase.
mkdir -p /etc/systemd/user/default.target.wants
ln -sfn /usr/lib/systemd/user/arcalium-cleanup-bazzite.service \
    /etc/systemd/user/default.target.wants/arcalium-cleanup-bazzite.service
chmod 0755 /usr/lib/arcalium/ai/assistant-agent.py
chmod 0755 /usr/lib/arcalium/apps/install-session.sh
chmod 0755 /usr/lib/arcalium/proton/install-session.sh
chmod 0755 /usr/lib/arcalium/updates/session.sh
systemctl enable arcalium-migrate-hostname.service
systemctl enable arcalium-flatpak-nvidia.service

# Phase 2 diagnostics JSON schemas (PRODUCT_SPEC §10.2).
install -d /usr/share/arcalium/schemas
if [[ -d /ctx/config/schemas ]]; then
    cp -av /ctx/config/schemas/. /usr/share/arcalium/schemas/
fi
# Declarative application catalogue for Control Centre / arcaliumctl apps.
install -d /usr/share/arcalium/catalogue
if [[ -d /ctx/config/catalogue ]]; then
    cp -av /ctx/config/catalogue/. /usr/share/arcalium/catalogue/
fi
test -f /usr/share/arcalium/catalogue/apps.v1.json

# Phase 9 Steam gate (PRODUCT_SPEC §17.2): do not redistribute Valve's Steam
# client in the image. Users open Valve's official download page from Control
# Centre (`arcaliumctl steam open-download`) and accept Steam's agreement there.
echo "Steam-related RPMs before removal:"
rpm -qa '*steam*' || true
STEAM_REMOVE=()
for pkg in steam steam-devices; do
    if rpm -q "${pkg}" >/dev/null 2>&1; then
        STEAM_REMOVE+=("${pkg}")
    fi
done
if [[ ${#STEAM_REMOVE[@]} -gt 0 ]]; then
    dnf5 -y remove "${STEAM_REMOVE[@]}" || dnf -y remove "${STEAM_REMOVE[@]}"
fi
if rpm -q steam >/dev/null 2>&1; then
    echo "ERROR: steam RPM is still present after removal (Steam redistribution gate)" >&2
    exit 1
fi
if [[ -e /usr/share/applications/steam.desktop ]]; then
    echo "ERROR: /usr/share/applications/steam.desktop still present after Steam removal" >&2
    exit 1
fi
# Bazzite still ships a skel autostart that runs bazzite-steam -silent and a
# firstrun kdialog ("downloading the Steam client…") even with no /usr/bin/steam.
# Remove those entry points; our /usr/bin/bazzite-steam* wrappers prefer Flatpak
# Steam, then native /usr/bin/steam, else open Control Centre's Flathub install.
rm -f /etc/skel/.config/autostart/steam.desktop
rm -f /usr/share/applications/bazzite-steam-bpm.desktop
rm -f /usr/share/applications/steam.desktop
if [[ -e /etc/skel/.config/autostart/steam.desktop ]]; then
    echo "ERROR: skel steam.desktop autostart still present" >&2
    exit 1
fi
# Our overrides must win over any remaining Bazzite scripts.
test -x /usr/bin/bazzite-steam
test -x /usr/bin/bazzite-steam-firstrun
grep -q 'Arcalium override' /usr/bin/bazzite-steam-firstrun
grep -q 'not shipped in the image' /usr/bin/bazzite-steam
echo "Steam client removed from image (not redistributed)."

# Hide inherited Bazzite marketing / maintenance launchers. Arcalium users update
# via Control Centre (bootc) — not Bazzite Updater / Portal / docs / Bold Brew CLI UI.
echo "Removing Bazzite Portal / Documentation / Updater / CLI menu entries..."
# Newer bases ship the GUI as RPM bazzite-updater (io.github.rfrench3.bazzite-updater),
# replacing the old system-update.desktop tip launcher.
if rpm -q bazzite-updater >/dev/null 2>&1; then
    dnf5 -y remove bazzite-updater || dnf -y remove bazzite-updater
fi
if rpm -q bazzite-updater >/dev/null 2>&1; then
    echo "ERROR: bazzite-updater RPM still present after removal" >&2
    exit 1
fi
# Portal / yafti may be an RPM; remove if present so it cannot reappear.
for pkg in yafti yafti-gtk python3-yafti; do
    if rpm -q "${pkg}" >/dev/null 2>&1; then
        dnf5 -y remove "${pkg}" || dnf -y remove "${pkg}" || true
    fi
done

# Skel + system autostart (Portal / announcements copy into ~/.config on first login).
rm -f /etc/skel/.config/autostart/bazzite-portal.desktop
rm -f /etc/skel/.config/autostart/bazzite-*.desktop
rm -f /etc/xdg/autostart/bazzite-portal.desktop
rm -f /etc/xdg/autostart/bazzite-announcement.desktop
rm -f /etc/xdg/autostart/bazzite-*.desktop
find /etc/skel/.config/autostart /etc/xdg/autostart -maxdepth 1 -type f \( \
    -iname '*bazzite*' -o -iname '*yafti*' \
  \) -print -delete 2>/dev/null || true

rm -f /usr/share/applications/bazzite-documentation.desktop
rm -f /usr/share/applications/system-update.desktop
rm -f /usr/share/applications/discourse.desktop
rm -f /usr/share/applications/bbrew.desktop
rm -f /usr/share/applications/io.github.rfrench3.bazzite-updater.desktop
rm -f /usr/share/applications/bazzite-updater.desktop
rm -f /usr/share/applications/io.github.ublue_os.yafti_gtk.desktop
rm -f /usr/share/applications/yafti_gtk.desktop
rm -f /usr/share/applications/yafti.desktop

# Portal / updater / CLI / docs / forums — wipe by filename under applications trees.
find /usr/share/applications /usr/local/share/applications -type f \( \
    -iname '*yafti*' -o \
    -iname '*bazzite-portal*' -o \
    -iname '*bazzite*portal*' -o \
    -iname 'bazzite-documentation.desktop' -o \
    -iname 'system-update.desktop' -o \
    -iname '*bazzite-updater*' -o \
    -iname '*bazzite*cli*' -o \
    -iname 'bbrew.desktop' -o \
    -iname 'discourse.desktop' -o \
    -iname '*ublue*yafti*' \
  \) -print -delete 2>/dev/null || true

# Catch renamed launchers by Name= / Comment= / Exec= (Kickoff label).
while IFS= read -r -d '' desktop; do
    if grep -E '^(Name|Name\[en(_[A-Z]+)?\]|Comment|Comment\[en(_[A-Z]+)?\]|Exec)=' "${desktop}" 2>/dev/null \
        | grep -qiE 'Bazzite Updater|Bazzite CLI|Bold Brew|Bazzite Portal|Bazzite Documentation|Bazzite Announcements|yafti|ujust update|Universal Blue Forums|^Name=Discourse$|^Name=Documentation$'; then
        echo "Removing launcher by metadata: ${desktop}"
        rm -f "${desktop}"
    fi
done < <(find /usr/share/applications /usr/local/share/applications -type f -name '*.desktop' -print0 2>/dev/null)

# Autostart for existing profiles is under ~/.config; skel covers new users.
# User unit arcalium-cleanup-bazzite also clears ~/.local leftovers after upgrade.
if [[ -e /etc/skel/.config/autostart/bazzite-portal.desktop ]]; then
    echo "ERROR: skel bazzite-portal.desktop autostart still present" >&2
    exit 1
fi
if compgen -G '/etc/xdg/autostart/*bazzite*' >/dev/null 2>&1; then
    echo "ERROR: Bazzite autostart still present under /etc/xdg/autostart" >&2
    ls -la /etc/xdg/autostart/*bazzite* >&2 || true
    exit 1
fi
if [[ -e /usr/share/applications/bazzite-documentation.desktop ]]; then
    echo "ERROR: bazzite-documentation.desktop still present" >&2
    exit 1
fi
if [[ -e /usr/share/applications/system-update.desktop ]]; then
    echo "ERROR: system-update.desktop still present" >&2
    exit 1
fi
if [[ -e /usr/share/applications/discourse.desktop ]]; then
    echo "ERROR: discourse.desktop still present" >&2
    exit 1
fi
if compgen -G '/usr/share/applications/*bazzite-updater*' >/dev/null 2>&1; then
    echo "ERROR: bazzite-updater launcher still present under /usr/share/applications" >&2
    ls -la /usr/share/applications/*bazzite-updater* >&2 || true
    exit 1
fi
if compgen -G '/usr/share/applications/*yafti*' >/dev/null 2>&1; then
    echo "ERROR: yafti/Portal launcher still present under /usr/share/applications" >&2
    ls -la /usr/share/applications/*yafti* >&2 || true
    exit 1
fi
if [[ -e /usr/share/applications/bbrew.desktop ]]; then
    echo "ERROR: bbrew.desktop (Bold Brew / Bazzite CLI UI) still present" >&2
    exit 1
fi
# Fail if any remaining app menu entry is clearly Bazzite Portal/Updater branded.
if find /usr/share/applications -type f -name '*.desktop' -print0 2>/dev/null \
    | xargs -0 grep -l -E '^Name=.*Bazzite (Portal|Updater|CLI|Announcements)' 2>/dev/null \
    | grep -q .; then
    echo "ERROR: Bazzite-branded Kickoff entries still present:" >&2
    find /usr/share/applications -type f -name '*.desktop' -print0 2>/dev/null \
        | xargs -0 grep -l -E '^Name=.*Bazzite (Portal|Updater|CLI|Announcements)' >&2 || true
    exit 1
fi
echo "Bazzite Portal / Documentation / Updater / CLI menu entries removed."

# An import-time error in any ctl module breaks every arcaliumctl command, and
# therefore the whole Control Centre, so prove the CLI imports and that the
# catalogue parses before the image ships. --help exercises every import.
arcaliumctl --help >/dev/null
arcaliumctl setup status --json >/dev/null
arcaliumctl ai status --json >/dev/null
arcaliumctl steam status --json >/dev/null
python3 -c 'import json,sys; json.load(open("/usr/share/arcalium/catalogue/apps.v1.json"))'

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
