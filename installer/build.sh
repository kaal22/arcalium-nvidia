#!/usr/bin/bash
# Turns the Arcalium image into a live/installer payload that satisfies titanoboa's
# container-native ISO contract v0.1.0: /usr/lib/bootc-image-builder/iso.yaml, a
# live-capable initramfs, EFI binaries under /boot/efi, GRUB2 modules in /usr/lib/grub.
#
# Adapted from ublue-os/bazzite installer/build.sh, the upstream reference for this
# base image. Bootc Image Builder cannot produce an Anaconda ISO here — see
# docs/BUILDING.md.

set -exo pipefail

BASE_IMAGE=${BASE_IMAGE:?}
INSTALL_IMAGE_PAYLOAD=${INSTALL_IMAGE_PAYLOAD:?}
TARGET_IMAGE_REF=${TARGET_IMAGE_REF:?}
LIVE_SESSION=${LIVE_SESSION:-kde}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# /root is a symlink in this base and bwrap needs its target to exist
mkdir -p "$(realpath /root)"

# bwrap writes /proc/sys/user/max_user_namespaces, which is mounted read-only
mount -o remount,rw /proc/sys

# The live layer needs packages newer than Bazzite's version pins allow
dnf -qy versionlock clear || :

### The image Anaconda writes to disk
# Carried inside the ISO's own container store so installs need no network.
if mountpoint -q /usr/lib/containers/storage; then
    podman save --format oci-archive "$INSTALL_IMAGE_PAYLOAD" |
        podman load --storage-opt additionalimagestore=''
else
    podman pull "$INSTALL_IMAGE_PAYLOAD"
fi

### Secure Boot for the live media
# Bazzite's kernel is signed with the Universal Blue key, which firmware does not
# trust until the user enrols it, so the ISO would refuse to boot with Secure Boot
# enabled. Swap in the Fedora-signed kernel. This affects the live session only —
# the installed system uses the payload image's kernel, which still needs the
# upstream key enrolment described in PRODUCT_SPEC section 16.2.
kernel_pkgs=(
    kernel
    kernel-core
    kernel-devel
    kernel-devel-matched
    kernel-modules
    kernel-modules-core
    kernel-modules-extra
)
dnf -y versionlock delete "${kernel_pkgs[@]}" || :
dnf --setopt=protect_running_kernel=False -y remove "${kernel_pkgs[@]}"
(cd /usr/lib/modules && rm -rf -- ./*)
dnf -y --repo fedora,updates --setopt=tsflags=noscripts install kernel kernel-core
kernel=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%P\n' | head -1)
depmod "$kernel"

# Nouveau needs the GSP firmware to bring up a display on Turing and newer
dnf install -y nvidia-gpu-firmware || :

### Live environment
dnf install -y dracut-live
DRACUT_NO_XATTR=1 dracut -v --force --zstd --reproducible --no-hostonly \
    --add "dmsquash-live dmsquash-live-autooverlay" \
    "/usr/lib/modules/${kernel}/initramfs.img" "$kernel"

dnf install -y livesys-scripts
sed -i "s/^livesys_session=.*/livesys_session=${LIVE_SESSION}/" /etc/sysconfig/livesys
systemctl enable livesys.service livesys-late.service

### Installer
# Firefox is required at runtime by anaconda-webui (webui-desktop launches it).
# Soft RPM dep only applies with fedora-release-workstation, which this image lacks.
dnf install -y --enable-repo=fedora-cisco-openh264 --allowerasing \
    firefox anaconda-live libblockdev-{btrfs,lvm,dm} yad
mkdir -p /var/lib/rpm-state /usr/share/anaconda/post-scripts

# shellcheck source=/dev/null
source /etc/os-release
rm -f /etc/system-release
echo "Arcalium OS NVIDIA Edition ${VERSION_ID}" >/etc/system-release

# Anaconda profile, welcome dialog, visible Install launcher
cp -a "$SCRIPT_DIR/system_files"/. /
chmod 0755 /usr/bin/arcalium-live-welcome.sh

cat >>/usr/share/anaconda/interactive-defaults.ks <<EOF
ostreecontainer --url=${INSTALL_IMAGE_PAYLOAD} --transport=containers-storage --no-signature-verification
%include /usr/share/anaconda/post-scripts/arcalium-track-registry.ks
EOF

# Point the installed system at the published image so bootc upgrades work.
# Deliberately not --erroronfail: the GHCR package is private during the alpha, so
# this cannot reach the registry and must not abort a tester's install.
cat >/usr/share/anaconda/post-scripts/arcalium-track-registry.ks <<EOF
%post --log=/var/log/arcalium-track-registry.log
bootc switch --mutate-in-place --transport registry ${TARGET_IMAGE_REF}
%end
EOF

### Live session: installer-focused, not a gaming desktop
# Steam and Bazzite announcements belong on the installed system, not the live ISO.
rm -f /etc/skel/.config/autostart/steam.desktop
if [[ -f /etc/xdg/autostart/bazzite-announcement.desktop ]]; then
    sed -i \
        -e 's/^X-GNOME-Autostart-enabled=.*/X-GNOME-Autostart-enabled=false/' \
        -e '$a Hidden=true' \
        /etc/xdg/autostart/bazzite-announcement.desktop
fi

### ISO contract
dnf install -y grub2-efi-x64-cdboot # provides gcdx64.efi

# Fedora 44 ships the EFI payloads under /usr/lib/efi for bootupd; titanoboa reads /boot/efi
mkdir -p /boot/efi
cp -av /usr/lib/efi/*/*/EFI /boot/efi/
cp -v /boot/efi/EFI/fedora/grubx64.efi /boot/efi/EFI/BOOT/fbx64.efi

mkdir -p /usr/lib/bootc-image-builder
cp -v "$SCRIPT_DIR/iso.yaml" /usr/lib/bootc-image-builder/iso.yaml

### Live session housekeeping
rm -f /etc/localtime
systemd-firstboot --timezone UTC

# / on live media is an overlay backed by /run, a small tmpfs. ostree needs far more
# room in /var/tmp than that while installing, so give it its own larger tmpfs.
rm -rf /var/tmp
mkdir /var/tmp
cat >/etc/systemd/system/var-tmp.mount <<'EOF'
[Unit]
Description=Larger tmpfs for /var/tmp on the live system

[Mount]
What=tmpfs
Where=/var/tmp
Type=tmpfs
Options=size=50%%,nr_inodes=1m

[Install]
WantedBy=local-fs.target
EOF
systemctl enable var-tmp.mount

dnf clean all
