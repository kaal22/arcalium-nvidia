# Building Arcalium OS NVIDIA Edition

Arcalium derives from Universal Blue’s [image-template](https://github.com/ublue-os/image-template) and the Bazzite NVIDIA-open desktop image.

## When to rebuild what

ISOs are **milestone artifacts**, not per-commit ones. A live ISO build is ~6 GB and tens of minutes; the container image is a push and a `bootc upgrade`. Default to the image loop and batch ISO rebuilds behind meaningful milestones.

| Change | Reaches machines via | Needs an ISO? |
|---|---|---|
| `system_files/`, `build_files/`, `Containerfile` — desktop defaults, taskbar pins, branding, layered packages | `just build` locally, or CI → `bootc upgrade` | No |
| `installer/` — Anaconda profile, welcome dialog, progress window, live-session tweaks | live media only | **Yes** |
| `installer/flatpaks` — bundled apps such as Brave | copied to disk by Anaconda at install time | **Yes** |
| `disk_config/`, `Justfile` build recipes | whichever build you run | Only if testing that build |

The trap worth remembering: **Flatpaks do not travel with `bootc upgrade`.** Anything in `installer/flatpaks` reaches only machines installed from a rebuilt ISO. On an existing box, `flatpak install` it by hand rather than cutting a new ISO.

Milestones that justify an ISO: installer behaviour changed, bundled app set changed, or a tester needs a clean bare-metal install. Otherwise push, let CI publish the image, and `bootc upgrade` on the test machine.

### What CI does automatically

- **`build.yml`** — builds, signs and pushes the container image on every push to `main`, and on PRs. This is the cheap path and the one to rely on. No nightly schedule: `:dev` moves only when we push, so a tester's `bootc upgrade` never pulls an unreviewed base change. Take Bazzite updates deliberately by re-pinning the digest in the `Containerfile`, or run the workflow by hand.
- **`build-disk.yml`** — **manual only** (`workflow_dispatch`). It never fires on a push. It builds qcow2 only; the live ISO comes from `just build-iso-live` in WSL, since Bootc Image Builder cannot depsolve this base.

## How updates reach users, and how Bazzite changes get in

Arcalium is the update source of truth. An installed machine tracks `ghcr.io/kaal22/arcalium-os-nvidia:dev` and never pulls from `bazzite-nvidia-open` directly — rebasing onto the Bazzite image would take the machine off Arcalium entirely. `bootc upgrade` fetches the next Arcalium image, stages a deployment and reboots; the previous deployment stays bootable for rollback. Flatpaks and user data are untouched by that.

| Layer | How it updates |
|---|---|
| Kernel, NVIDIA driver, Plasma, Steam (Bazzite base) | Only when we re-pin the base digest and publish a new Arcalium image |
| Arcalium branding, pins, wallpaper, Control Centre later | With every Arcalium image push |
| Brave / Spotify / ProtonPlus Flatpaks | Flatpak or Bazaar on the machine; the bundled *set* changes only with a new ISO |
| Home directory, Steam library, user settings | Not touched by image updates |

The `Containerfile` pins the base by digest, so the `:stable` tag in the `FROM` line is documentation — the digest is what actually builds. Bazzite moving `:stable` therefore changes nothing here until we act, which is the point: no tester receives a base change nobody reviewed. The trade-off is that **upstream security and driver fixes do not arrive on their own**, so re-pin on a deliberate cadence.

### Taking a Bazzite update

Resolve what `:stable` currently points at (no pull needed; `skopeo` is not installed in WSL, so use the registry API):

```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:ublue-os/bazzite-nvidia-open:pull&service=ghcr.io" | jq -r .token)
curl -sI -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
  https://ghcr.io/v2/ublue-os/bazzite-nvidia-open/manifests/stable \
  | grep -i docker-content-digest
```

If it differs from the digest in the `Containerfile`, update the `FROM` line and the date comment above it, then push. CI rebuilds Arcalium on the new base, signs it, and testers pick it up with `bootc upgrade`. Re-pinning the kernel and NVIDIA stack is exactly the kind of change that deserves a bare-metal check on the 3060 before it goes further.

Last checked 2026-07-30: `:stable` is still `sha256:83c6084f…`, matching the current pin.

## Standard ISO build workflow

Use this at milestones, not for every change. Git is the transfer mechanism between the Windows workstation and the Linux build host — never copy the working tree across manually, and never build from `/mnt/c`.

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

Run the ISO step detached, because it outlives most terminals:

```bash
setsid nohup just build-iso-live > output/iso-build.log 2>&1 < /dev/null &
tail -f output/iso-build.log
```

### The WSL VM can die mid-squashfs

On 2026-07-30 the whole WSL VM disappeared at 90% of `mksquashfs`, taking the build container with it: no error in the log, no exit status, and `uptime` afterwards showed a freshly booted VM. Nothing was in the Windows event log, and the payload image survived, so a rerun resumed from cache and only redid the ISO step.

Default WSL2 takes 50% of host RAM (16 GB of 32 GB) with no swap, so a spike has nowhere to go but the VM's death. `%USERPROFILE%\.wslconfig` now sets `memory=24GB`, `swap=8GB`, `processors=16`; apply changes with `wsl --shutdown`. Compressing a ~31 GB payload only needs ~3 GB resident, but page cache fills whatever is available, so leave the swap in place.

If a build dies this way, don't start over — `just build-iso-live` reuses the cached payload image and goes straight back to squashfs.

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

### Default applications (`installer/flatpaks`)

Applications for the **installed** system are Flatpaks listed one ref per line in `installer/flatpaks`, following PRODUCT_SPEC §7.3 rather than layering RPMs into the immutable image:

```
app/com.brave.Browser/x86_64/stable
app/com.spotify.Client/x86_64/stable
app/com.vysp3r.ProtonPlus/x86_64/stable
```

The payload build adds the Flathub remote and installs the list into the live image's `/var/lib/flatpak`; Anaconda then copies that store onto the target, so the apps arrive without a network during the install. This is the same mechanism Bazzite uses for its defaults, and omitting it is why builds before this shipped with **no browser at all** — Firefox in the live session is an `anaconda-webui` dependency and never reaches the installed system.

Two consequences worth knowing. Each entry pulls its runtimes as well, so the first browser added roughly a gigabyte to the ISO. And changes only reach machines that are installed from a **rebuilt ISO**: existing installs need `flatpak install` by hand, since `bootc upgrade` does not touch Flatpaks.

Verify any new ID on Flathub before committing it — PRODUCT_SPEC principle 4 forbids inventing Flatpak IDs, and `docs/LICENSING.md` tracks redistribution for anything bundled.

### Taskbar and default browser

New users get every bundled Arcalium app pinned on the Icon Tasks panel and in Kickoff favorites: Brave, the ChatGPT web app, Spotify and ProtonPlus. Existing Bazzite defaults Steam and Bazaar remain pinned too.

- `system_files/.../updates/arcalium-pins.js` — runs before Bazzite's `bazzite-pins.js` (alphabetical) and only writes when `launchers` is empty, per PRODUCT_SPEC §11.2
- `system_files/etc/xdg/mimeapps.list` — Brave as the default for `http`/`https`/`text/html` (keeps Bazzite's Bazaar `.flatpakref` association)
- `system_files/.../kicker-extra-favoritesrc` — the same bundled apps in application-launcher favorites

These live in the **bootc image**, not the live ISO payload. They reach machines via `just build` + `bootc upgrade`/`switch`, or a fresh ISO install. Existing users whose taskbar was already configured are left alone — pin Brave once by hand if needed. Control Centre is omitted until it exists.

### ChatGPT web app

`system_files/usr/share/applications/arcalium-chatgpt.desktop` adds ChatGPT to the application menu and launches the official `https://chatgpt.com/` site in a dedicated Brave app window. It is also included in the new-user taskbar defaults.

This is a launcher, not a redistributed ChatGPT client: OpenAI does not publish an official Linux app as of 2026-07-30, and unofficial wrappers would make users trust third-party code with their OpenAI credentials. The launcher adds negligible image size and reaches existing systems through the bootc image, but requires the Brave Flatpak to be installed.

### Desktop wallpaper

The build installs `assets/arcalium-wallpaper.png` as `/usr/share/wallpapers/arcalium-wallpaper.png`. The Bazzite Vapor look-and-feel setup script is overridden so Plasma selects it only while creating a new desktop containment. Existing users keep their chosen wallpaper, as required by PRODUCT_SPEC §11.2.

The source is 5504×3072, which is sufficient for 4K displays (the IDE preview is downscaled and must not be used to infer source dimensions). A future replacement can use the same filename without changing the configuration. Record its author, source and redistribution licence in `docs/LICENSING.md` before a public image or ISO.

### Logos

Source assets:

| File | Role |
|---|---|
| `assets/arccleanSVG.svg` | Primary mark — application menu / Kickoff icon and other compact surfaces |
| `assets/ARG_fullSVG.svg` | Wordmark (mark + “ARCALIUM OS” text) — splash and branding screens |

`build_files/install_logos.py` strips Adobe Illustrator private metadata at image-build time (the raw exports are ~10× larger and the metadata is unused for rendering) and installs:

- Mark → `/usr/share/icons/hicolor/scalable/places/{distributor-logo,distributor-logo-white,start-here-kde}.svg` and `/usr/share/arcalium/logo-mark.svg`
- Wordmark → `/usr/share/arcalium/logo-wordmark.svg`
- Both also under `/usr/share/icons/hicolor/scalable/apps/` as `arcalium-logo.svg` / `arcalium-wordmark.svg`

Any existing `bazzite_logo.svgz` under Plasma look-and-feel packages is replaced with a gzipped copy of the wordmark so the desktop splash shows Arcalium without rewriting Splash.qml. Verify by comparing checksums rather than grepping for a marker: `gzip -dc <svgz> | sha256sum` must equal `sha256sum /usr/share/arcalium/logo-wordmark.svg`.

Plymouth (the “OS Loading” screen after GRUB) uses `/usr/share/plymouth/themes/spinner/watermark.png`. `build.sh` rasterises `logo-wordmark.svg` to that path at ~256×121 with a transparent background via ImageMagick. The default `bgrt` theme reads the same ImageDir, so both themes pick it up. `NAME` / `PRETTY_NAME` in `/usr/lib/os-release` are rewritten to Arcalium at the same time (keeping `ID=bazzite` for the live Anaconda profile). After `bootc upgrade` and a reboot, the new watermark is inside the regenerated initramfs — no manual `plymouth-set-default-theme` is required.

Login / lock greeter wallpaper is **not** the desktop wallpaper setting. Bazzite hard-codes `/usr/share/wallpapers/convergence.jxl` in `/etc/xdg/kscreenlockerrc` (and the kde-settings profile copy). We override both to `/usr/share/wallpapers/arcalium-wallpaper.png`. That is why a manually chosen desktop wallpaper can stick while the login screen still shows Bazzite until this image lands.

### Hostname and Konsole welcome

The shell prompt’s `@bazzite` half is the machine hostname, not the OS name. Defaults:

- `DEFAULT_HOSTNAME=arcalium` in `/usr/lib/os-release` (Anaconda suggestion)
- `/etc/hostname` → `arcalium`
- `arcalium-migrate-hostname.service` renames a stock `bazzite` / `localhost` hostname once after rebase; custom hostnames are left alone

Konsole’s banner is the interactive MOTD (`/etc/profile.d/user-motd.sh`). We replaced Bazzite’s tip markdown with `fastfetch` using `/usr/share/arcalium/fastfetch.jsonc` and the ASCII mark in `/usr/share/arcalium/logo.txt`. `fastfetch` / `neofetch` aliases point at the same config. Per-user opt-out is unchanged: `touch ~/.config/no-show-user-motd` (or `ujust toggle-user-motd`).

Note how helper scripts are addressed: the `ctx` stage does `COPY build_files /`, so `build.sh`'s siblings are at `/ctx/install_logos.py`, **not** `/ctx/build_files/install_logos.py`. Getting this wrong fails the build immediately, which is how it was caught.

Still outstanding for full branding: a dark mark for light panels (current fills are white).

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
