# Building Arcalium OS NVIDIA Edition

Arcalium derives from Universal Blue’s [image-template](https://github.com/ublue-os/image-template) and the Bazzite NVIDIA-open desktop image.

## Standard ISO build workflow

This is the established loop. Git is the transfer mechanism between the Windows workstation and the Linux build host — never copy the working tree across manually, and never build from `/mnt/c`.

1. **Edit** on the Windows workstation (`Arcalium NVIDIA` folder).
2. **Commit and push** to `main` on GitHub.
3. **Pull** in the WSL clone at `~/arcalium-nvidia`.
4. **Build** there with `just build` then `just build-iso-live`.
5. **Copy** the finished ISO back to Windows.

```bash
# 1-2. On Windows
git add -A && git commit -m "..." && git push origin main

# 3-5. In WSL (as root: wsl -d Ubuntu -u root)
cd /home/kaal/arcalium-nvidia
git pull
just build
just build-iso-live
cp output/Arcalium-Live.iso /mnt/c/Users/Kaal/Desktop/
```

Use `build-iso-live` (Titanoboa), not `build-iso`. Bootc Image Builder cannot resolve Bazzite's Terra GPG keys and fails the depsolve — details under “ISO builds” below.

Two reasons this order matters: the WSL clone and the Windows folder are separate checkouts that silently drift if you skip the pull, and pushing first means the CI-built image and the local ISO come from the same commit.

Setup for the WSL host is under [Building from a Windows workstation via WSL2](#building-from-a-windows-workstation-via-wsl2).

## Prerequisites

- GitHub repository with Actions enabled
- Cosign keypair (`cosign.pub` in repo; private key only as `SIGNING_SECRET`)
- For local builds: a Linux host with Podman. Bootc Image Builder needs a privileged Linux container with working loop devices, so this runs in WSL2 (Ubuntu 24.04) or on a bootc machine, never on Windows directly.

## One-time Cosign setup

Keys were generated with Cosign **v2.6.3** (empty password, as required by the template workflow):

```bash
COSIGN_PASSWORD="" cosign generate-key-pair
```

1. Commit **only** `cosign.pub`.
2. Add the contents of `cosign.key` as the Actions secret `SIGNING_SECRET`.
3. Delete or securely store `cosign.key` outside the repo.

Verify a published image:

```bash
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:dev
```

## Configure identity

Edit `image-template.env` if needed:

| Variable | Value |
|---|---|
| `IMAGE_NAME` | `arcalium-os-nvidia` |
| `REPO_ORGANIZATION` | GitHub owner (currently `kaal22`) |
| `DEFAULT_TAG` | `dev` |

Keep `disk_config/iso.toml` and `.github/workflows/build-disk.yml` in sync with those values.

## Build OCI image (GitHub Actions)

1. Push to the default branch (`main`).
2. Workflow: **Build container image** (`.github/workflows/build.yml`).
3. Image publishes to `ghcr.io/<owner>/arcalium-os-nvidia` with `dev` and date/SHA alias tags.
4. The workflow signs the digest with Cosign.

## Visibility model

| Surface | Setting | Reason |
|---|---|---|
| GitHub repository | public | Free Actions minutes and artifact storage; spec principle 9 (open maintenance) |
| GHCR image package | private | Spec §17.2 — the built image carries the inherited Steam client |
| Disk images (ISO/QCOW2) | private artifacts | Downloaded by the maintainer, or built locally |

Making a GHCR package public is irreversible. Do not change the package to public until the Steam licensing gate is resolved.

## Build disk images (QCOW2 / ISO) — local, preferred

Local builds run against the image in local container storage, so they never pull from GHCR and need no registry credentials.

Requires a Linux host with Podman, `sudo`, privileged containers, and plenty of free disk. A machine already running Bazzite or Arcalium is ideal. A WSL2 distro also works — see below.

```bash
just build                # builds localhost/arcalium-os-nvidia:dev
just build-qcow2          # QCOW2 for VM boot tests
just build-iso-live       # live/installer ISO via titanoboa (see below)
```

Output lands in `output/`. `build-qcow2` uses `disk_config/disk.toml`. `build-iso-live` writes `output/Arcalium-Live.iso`.

### ISO builds — use `just build-iso-live`, not `just build-iso`

The template's Bootc Image Builder ISO path (`just build-iso`) fails during manifest generation:

```text
Failed to retrieve GPG key for repo 'terra-mesa': Curl error (37):
Could not read a file:// file for file:///etc/pki/rpm-gpg/RPM-GPG-KEY-terra44-mesa
```

The key **is** present in the image. The cause is [osbuild/bootc-image-builder#1188](https://github.com/osbuild/bootc-image-builder/issues/1188). Only `anaconda-iso` depsolves, which is why QCOW2 builds are unaffected.

Arcalium follows Bazzite's path instead: an `installer/` payload image satisfies [titanoboa's container-native ISO contract](https://github.com/ublue-os/titanoboa), then `just build-iso-live` wraps it into bootable media.

```bash
just build              # prerequisite: localhost/arcalium-os-nvidia:dev
just build-iso-live     # builds payload + ISO → output/Arcalium-Live.iso
```

The recipe clones upstream titanoboa into `.cache/titanoboa` on first run and runs its `main.sh` inside `quay.io/fedora/fedora:latest`. The `ghcr.io/ublue-os/titanoboa` image is not publicly pullable (403), so local builds do not use it.

The payload image (`localhost/arcalium-os-nvidia-payload:dev`, ~27 GB) layers live media on top of the base image: Fedora-signed kernel for Secure Boot on the live ISO, `dracut-live`, `anaconda-live`, EFI binaries under `/boot/efi`, and `/usr/lib/bootc-image-builder/iso.yaml`. See `installer/build.sh`.

Live-session extras under `installer/system_files/`:

- Anaconda profile matching Bazzite's `os_id` (without it, Install exits silently)
- Welcome dialog that launches `liveinst`
- Visible **Install Arcalium OS** launcher
- Steam and Bazzite announcement autostart disabled for the live session only
- `arcalium-install-progress.sh`, a progress window covering the deploy step

Both the welcome dialog and the desktop launcher go through `arcalium-install.sh`, so the progress window and error reporting apply however the installer is started.

### Install time and the deploy step

An install writes the whole OS image to disk, so it takes 15–40 minutes and spends nearly all of that inside one Anaconda step with no visible progress. Anaconda reports nothing during `ostree container deploy`, `hwclock` is the last line in the log before it starts, and testers reasonably read that as a hang. `arcalium-install-progress.sh` exists to disprove that: it polls the target mount and reports bytes written, elapsed time, and throughput.

The bar pulsates rather than showing a percentage because the target is btrfs with `zstd:1`, so bytes on disk never approach the image size and any percentage would stall short of 100.

To confirm progress by hand from a live-session terminal:

```bash
watch -n5 'df -h /mnt/sysroot /mnt/sysimage 2>/dev/null; pgrep -a ostree'
```

### Upstream: titanoboa silently builds gzip squashfs

`build_iso.sh` invokes:

```bash
mksquashfs /rootfs … -e sysroot -e ostree -comp zstd -Xcompression-level 19
```

`mksquashfs` treats every argument after `-e` as an exclude path, so `-comp zstd -Xcompression-level 19` becomes four exclude patterns and the compressor falls back to gzip. Build logs confirm it: `Exportable Squashfs 4.0 filesystem, gzip compressed`. The entire live root, including the embedded container store the installer reads from, is then decompressed with gzip for the whole install.

`build-iso-live` patches the clone with `sed` before running it and asserts the result, so a silent upstream reordering cannot reintroduce the fallback unnoticed. Fixing it upstream is worth a pull request.

### Building from a Windows workstation via WSL2

Verified working on WSL2 2.6.3 (kernel 6.6.87) with Ubuntu 24.04.

```bash
# In the WSL distro, as root:
apt-get update && apt-get install -y podman git uidmap
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
```

Install `just` from the upstream script, not from apt. Ubuntu packages `just` 1.21, which is too old for the `[group(...)]` attributes this Justfile uses and fails with `Unknown attribute group`.

Clone inside the WSL filesystem rather than building from `/mnt/c`. The recipes `chown` output, create temp directories in the working tree, and move multi-gigabyte files, which is slow and permission-prone across the Windows filesystem bridge.

```bash
git clone https://github.com/kaal22/arcalium-nvidia.git ~/arcalium-nvidia
cd ~/arcalium-nvidia
just build
just build-iso-live
cp output/Arcalium-Live.iso /mnt/c/Users/<you>/Desktop/
```

If `sudo` prompts for a password, enter the distro as root instead: `wsl -d Ubuntu -u root`. The `_rootful_load_image` recipe detects it is already root and skips the image copy into rootful storage.

Building as root against a clone owned by your normal user makes git refuse to read the repository, and the `build` recipe needs `git status` and `git rev-parse` for its image labels. Allow it once:

```bash
git config --global --add safe.directory /home/<user>/arcalium-nvidia
```

Verified on this workstation:

| Check | Result |
|---|---|
| `/dev/loop-control` inside a privileged container | present, `losetup -f` returns `/dev/loop0` |
| `--security-opt label=type:unconfined_t` on a non-SELinux host | accepted by Podman, no Justfile change needed |
| `just --evaluate image_name` / `default_tag` | `arcalium-os-nvidia` / `dev` |

Expect the first `just build` to pull roughly 15–20 GB of Bazzite NVIDIA layers, and allow tens of gigabytes more for the ISO build.

## Build disk images (GitHub Actions) — currently blocked

**Build disk images** (`.github/workflows/build-disk.yml`) requires the image to be pullable by `osbuild/bootc-image-builder-action`. That action exposes no authentication or pull-secret input, so it cannot pull the private `arcalium-os-nvidia` package. Options, none adopted yet:

- Build disk images locally (preferred while the package stays private).
- Upload to S3 with the workflow's existing `S3_*` secrets, which avoids artifact storage limits but does not solve the pull.
- Revisit if upstream adds registry authentication.

## Bootstrap the first test machine (no Arcalium ISO needed)

An Arcalium ISO is only needed for clean-install repeatability testing. To validate hardware sooner, rebase an existing Bazzite install:

1. Install stock `bazzite-nvidia-open` from the official [Bazzite ISO](https://download.bazzite.gg).
2. Authenticate to GHCR for the private package — see [GHCR authentication for bootc](#ghcr-authentication-for-bootc) below, which is not a plain `podman login`.

3. Switch to the Arcalium image and reboot:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:dev
sudo systemctl reboot
```

That machine then doubles as the local ISO builder.

## After an ISO install: point the system at GHCR

A system installed from the ISO will not update until you do this once, by design.

The ISO installs from the container image baked into it (`--transport=containers-storage`), so the installed system initially tracks `localhost/arcalium-os-nvidia:dev` — a reference that can never be pulled. The kickstart tries to correct this in `%post` with `bootc switch --mutate-in-place`, but the GHCR package is private during the alpha and the installer has no credentials, so that step fails. It deliberately runs without `--erroronfail` so a failed registry lookup cannot abort a tester's install.

Confirm what the system is tracking:

```bash
sudo bootc status
```

If `image` shows `localhost/arcalium-os-nvidia:dev`, authenticate as below and then repoint it:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:dev
sudo systemctl reboot
```

`bootc upgrade` works normally after that. Making the GHCR package public removes this step entirely, but that is held behind the Steam licensing gate in `docs/PRODUCT_SPEC.md` §17.2.

## GHCR authentication for bootc

Two things trip this up, and a plain `sudo podman login ghcr.io` hits both.

**The token needs `read:packages`.** A GitHub password will not work, and neither will most tokens you already have — the `gh` CLI's own OAuth token is scoped `gist, read:org, repo` by default, so reusing it returns `403 Forbidden`. Create a classic token with only the `read:packages` scope:

<https://github.com/settings/tokens/new?scopes=read:packages&description=Arcalium%20bootc%20pull>

**bootc does not read podman's credentials.** `podman login` writes to `$XDG_RUNTIME_DIR/containers/auth.json`, which is both ephemeral and in a location system services should not read. bootc reads `/etc/ostree/auth.json`, `/run/ostree/auth.json` or `/usr/lib/ostree/auth.json` instead ([bootc secrets docs](https://bootc.dev/bootc/building/secrets.html)). Authenticating the ordinary way therefore appears to succeed and then `bootc upgrade` still fails, or works until the next reboot.

Write the credentials straight to the persistent path bootc uses:

```bash
echo '<TOKEN>' | sudo podman login ghcr.io \
  -u <github-username> --password-stdin \
  --authfile /etc/ostree/auth.json
sudo chmod 600 /etc/ostree/auth.json
```

## Important gates

- Do not publish a public ISO until the Steam licensing gate in `docs/PRODUCT_SPEC.md` §17.2 is resolved.
- Do not start the Control Centre until the base image and ISO workflow are proven (spec §28).
- Do not invent Flatpak IDs, `ujust` paths, or bootc flags — verify against upstream first.
