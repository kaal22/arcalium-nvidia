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

### Default applications for the installed system
# PRODUCT_SPEC section 7.3 wants graphical applications as Flatpaks rather than RPMs
# layered into the immutable image. Anaconda copies this live installation onto the
# target, so anything listed here lands on the installed system without needing a
# network during the install. Omitting this step is why early builds shipped with no
# browser at all: Bazzite's own default apps arrive through exactly this mechanism.
mkdir -p /etc/flatpak/remotes.d
curl --retry 5 --retry-delay 3 -Lo /etc/flatpak/remotes.d/flathub.flatpakrepo \
    https://dl.flathub.org/repo/flathub.flatpakrepo

# Flathub downloads inside the payload build fail intermittently (TLS / peer reset).
# Retry the whole app set before giving up so public ISO cuts are not flaky.
apps_ok=0
for attempt in 1 2 3 4 5; do
    echo "Installing bundled Flatpaks from installer/flatpaks (attempt ${attempt}/5)…"
    if xargs -r flatpak install -y --noninteractive <"$SCRIPT_DIR/flatpaks"; then
        apps_ok=1
        break
    fi
    echo "WARN: bundled Flatpak install failed — retrying in $((attempt * 10))s…"
    sleep $((attempt * 10))
done
if [[ "${apps_ok}" -ne 1 ]]; then
    echo "ERROR: could not install bundled Flatpaks after retries." >&2
    exit 1
fi

# Matching NVIDIA Flatpak GL runtimes (version-locked to the image driver).
# Without these, bundled Heroic / Firefox and later Steam installs hit
# "no OpenGL" / ~1 FPS. Tag comes from the payload image stamp, else RPM/`nvidia-smi`.
GL_TAG=""
if [[ -f /usr/share/arcalium/flatpak-nvidia-gl.tag ]]; then
    GL_TAG="$(tr -d '[:space:]' </usr/share/arcalium/flatpak-nvidia-gl.tag || true)"
fi
if [[ -z "${GL_TAG}" && -x /usr/lib/arcalium/flatpak/nvidia-gl-tag.sh ]]; then
    GL_TAG="$(/usr/lib/arcalium/flatpak/nvidia-gl-tag.sh)"
fi
if [[ -z "${GL_TAG}" ]]; then
    echo "ERROR: could not resolve Flatpak NVIDIA GL tag for ISO bundle." >&2
    exit 1
fi
echo "Installing Flatpak NVIDIA GL extensions for tag nvidia-${GL_TAG}"
# Flathub pulls occasionally hit transient TLS errors inside the payload build;
# retry each extension rather than failing the whole ISO.
for EXT in \
    "org.freedesktop.Platform.GL.nvidia-${GL_TAG}" \
    "org.freedesktop.Platform.GL32.nvidia-${GL_TAG}"
do
    ok=0
    for attempt in 1 2 3 4 5; do
        echo "Ensuring ${EXT} (attempt ${attempt}/5)…"
        if flatpak install -y --noninteractive flathub "${EXT}"; then
            ok=1
            break
        fi
        echo "WARN: ${EXT} install failed — retrying in $((attempt * 5))s…"
        sleep $((attempt * 5))
    done
    if [[ "${ok}" -ne 1 ]]; then
        echo "ERROR: could not install ${EXT} after retries." >&2
        exit 1
    fi
done

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

# Anaconda profile + desktop Install launcher (no autostart welcome dialog)
cp -a "$SCRIPT_DIR/system_files"/. /
chmod 0755 /usr/bin/arcalium-install.sh

cat >>/usr/share/anaconda/interactive-defaults.ks <<EOF
network --hostname=arcalium
ostreecontainer --url=${INSTALL_IMAGE_PAYLOAD} --transport=containers-storage --no-signature-verification
%include /usr/share/anaconda/post-scripts/arcalium-install-flatpaks.ks
%include /usr/share/anaconda/post-scripts/arcalium-track-registry.ks
EOF

# Copy the bundled Flatpak store onto the target. ostreecontainer deploys the
# container image only; without this the live session's /var/lib/flatpak is
# discarded and the installed system ships with none of the bundled apps, which
# also leaves the taskbar pins pointing at desktop entries that do not resolve.
#
# The copy target is the deployment's own var/lib, which ostree-prepare-root
# bind-mounts as /var on boot. Verified on hardware: an install using this path
# came up with all bundled Flatpaks present. Note the ostree deployment docs
# describe a shared per-stateroot /var instead; do not "fix" this to
# /ostree/deploy/$stateroot/var on the strength of that doc alone.
#
# The relabel must happen here, in --nochroot, against the path just written.
# Anaconda's chroot does not see the deployment's /var, so a chroot %post
# running `chcon /var/lib/flatpak` operates on a directory that does not exist.
#
# Deliberately never fatal. An earlier revision used --erroronfail (copied from
# ublue-os/bazzite) on a separate chroot relabel script, and its failure aborted
# an otherwise complete install with "critical error running post installation
# scripts". Missing bundled apps are recoverable with `flatpak install`; a dead
# install is not. Failures leave a marker at /var/log/arcalium-flatpaks-failed.
cat >/usr/share/anaconda/post-scripts/arcalium-install-flatpaks.ks <<'EOF'
%post --nochroot --log=/tmp/arcalium-install-flatpaks.log
set -x

sysroot=""
for candidate in /mnt/sysimage /mnt/sysroot; do
    if [ -d "$candidate/ostree/deploy" ]; then
        sysroot="$candidate"
        break
    fi
done
if [ -z "$sysroot" ]; then
    echo "ARCALIUM: no ostree sysroot under /mnt/sysimage or /mnt/sysroot"
    exit 0
fi
echo "ARCALIUM: sysroot=$sysroot"

if [ ! -d /var/lib/flatpak ]; then
    echo "ARCALIUM: live session has no /var/lib/flatpak to copy"
    exit 0
fi

copied=0
for deployment in "$sysroot"/ostree/deploy/*/deploy/*.[0-9]; do
    [ -d "$deployment" ] || continue
    echo "ARCALIUM: copying Flatpaks into $deployment/var/lib"
    mkdir -p "$deployment/var/lib"
    if rsync -aAXUHK --open-noatime /var/lib/flatpak "$deployment/var/lib/"; then
        chcon -R -t var_lib_t "$deployment/var/lib/flatpak" || true
        copied=1
    else
        echo "ARCALIUM: rsync into $deployment/var/lib failed"
    fi
done
sync

if [ "$copied" != 1 ]; then
    echo "ARCALIUM: bundled Flatpaks were NOT installed"
    for deployment in "$sysroot"/ostree/deploy/*/deploy/*.[0-9]; do
        [ -d "$deployment/var" ] || continue
        mkdir -p "$deployment/var/log"
        echo "flatpak copy failed during install" \
            > "$deployment/var/log/arcalium-flatpaks-failed"
    done
fi
exit 0
%end
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
# Control Centre Desktop shortcut is for installed users (skel in the bootc
# image). Drop it from the live payload so the live desktop only shows Install.
rm -f /etc/skel/Desktop/arcalium-control-centre.desktop
rm -f /home/liveuser/Desktop/arcalium-control-centre.desktop
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

# Keep the bundled Flatpaks pristine while Anaconda copies them onto the target.
cat >/etc/systemd/system/var-lib-flatpak.mount <<'EOF'
[Unit]
Description=Read-only bundled Flatpak store on the live system

[Mount]
Type=none
What=/var/lib/flatpak
Where=/var/lib/flatpak
Options=bind,ro

[Install]
WantedBy=multi-user.target
EOF
systemctl enable var-lib-flatpak.mount

dnf clean all
