# Building Arcalium OS NVIDIA Edition

Arcalium derives from Universal Blue’s [image-template](https://github.com/ublue-os/image-template) and the Bazzite NVIDIA-open desktop image.

## When to rebuild what

ISOs are **milestone artifacts**, not per-commit ones. A live ISO build is ~6 GB and tens of minutes; the container image is a push and a `bootc upgrade`. Default to the image loop and batch ISO rebuilds behind meaningful milestones.

| Change | Reaches machines via | Needs an ISO? |
|---|---|---|
| `system_files/`, `build_files/`, `Containerfile` — desktop defaults, taskbar pins, branding, layered packages | `just build` locally, or CI → `bootc upgrade` | No |
| `installer/` — Anaconda profile, Install launcher, live-session tweaks | live media only | **Yes** |
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
| Brave / Spotify / ProtonPlus / Heroic Flatpaks | Flatpak or Bazaar on the machine; the bundled *set* changes only with a new ISO |
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
- Visible **Install Arcalium OS** launcher (`arcalium-install.sh` → `liveinst --profile bazzite`)
- Steam and Bazzite announcement autostart disabled for the live session only

There is no autostart welcome dialog — testers open Install from the desktop or application menu. The previous popup framed the live session as a "test environment" and was removed once the stock desktop launcher proved reliable.

### Default applications (`installer/flatpaks`)

Applications for the **installed** system are Flatpaks listed one ref per line in `installer/flatpaks`, following PRODUCT_SPEC §7.3 rather than layering RPMs into the immutable image:

```
app/com.brave.Browser/x86_64/stable
app/com.spotify.Client/x86_64/stable
app/com.vysp3r.ProtonPlus/x86_64/stable
app/com.heroicgameslauncher.hgl/x86_64/stable
```

The payload build adds the Flathub remote and installs the list into the live image's `/var/lib/flatpak`. That store only reaches the installed system because `arcalium-install-flatpaks.ks` rsyncs it across in a `%post --nochroot` — `ostreecontainer` deploys the container image and nothing else. Omitting that post-script silently produced installs with none of the bundled apps.

Two things about that script are easy to get wrong:

- **Relabel in `--nochroot`, against the path you just wrote.** Anaconda's chroot does not see the deployment's `/var`, so a separate chroot `%post` running `chcon -R -t var_lib_t /var/lib/flatpak` operates on a directory that does not exist there and fails.
- **Never use `--erroronfail` here.** A failure aborts the whole install with "critical error running post installation scripts" *after* the OS is already on disk and bootable. Missing apps are recoverable with `flatpak install`; a failed install is not. The script exits `0` and writes `/var/log/arcalium-flatpaks-failed` on the target instead, so a silent failure stays detectable.

The copy target deserves a note, because the documentation is contradictory. The [ostree deployment docs](https://ostreedev.github.io/ostree/deployment/) say each stateroot has one shared `/var` at `/ostree/deploy/$stateroot/var`, which implies writing to `deploy/$checksum.0/var/lib` can never surface as `/var/lib`. The [`ostree-prepare-root(1)`](https://man.archlinux.org/man/ostree-prepare-root.1.en) man page says the opposite: *"For /var, by default a bind mount is created from the deployment root to /sysroot/var."* Hardware wins the argument — an install using the deployment path came up with all bundled Flatpaks present at `/var/lib/flatpak`. Keep the deployment path and do not switch to the stateroot path on the strength of the deployment doc alone. This is the same mechanism Bazzite uses for its defaults, and omitting it is why builds before this shipped with **no browser at all** — Firefox in the live session is an `anaconda-webui` dependency and never reaches the installed system.

Two consequences worth knowing. Each entry pulls its runtimes as well, so the first browser added roughly a gigabyte to the ISO. And changes only reach machines that are installed from a **rebuilt ISO**: existing installs need `flatpak install` by hand, since `bootc upgrade` does not touch Flatpaks.

Verify any new ID on Flathub before committing it — PRODUCT_SPEC principle 4 forbids inventing Flatpak IDs, and `docs/LICENSING.md` tracks redistribution for anything bundled.

### Taskbar and default browser

New users get the daily-use bundled apps pinned on the Icon Tasks panel and in Kickoff favorites. Panel order (left → right): Files, Bazaar, Brave, Steam, Heroic, Spotify. Heroic opens directly; it does not download Proton before launch.

Two deliberate absences from the panel:

- **Control Centre** — its icon is the Arcalium mark, the same artwork as the Kickoff launcher button at the far left, so pinning it placed two identical marks side by side. It stays in Kickoff favorites. If it ever gets its own distinct icon, it can be pinned again.
- **ProtonPlus** — a setup/utility tool rather than a daily launcher, so Kickoff favorites only.

The ChatGPT Brave web-app launcher was removed entirely (2026-07-31); Brave itself remains the default browser.

The pins come from the **panel layout template**, which is the part that trips people up. Plasma runs `/usr/share/plasma/layout-templates/org.kde.plasma.desktop.defaultPanel/contents/layout.js` when it first creates a panel for a new user, and Bazzite patches that file to write its own launcher list. Update scripts under `shells/org.kde.plasma.desktop/contents/updates/` run *after* that and every one of them guards on `launchers` being empty — so by the time they run there is nothing left to do.

We originally shipped `arcalium-pins.js` as an update script and it never had any effect. Fresh installs came up with Bazzite's list, and because `preferred://browser` resolves through our `mimeapps.list` default, Brave appeared pinned while nothing else of ours did. That looked like a partial success and was actually zero.

- `build_files/patch_panel_pins.py` — rewrites the launcher array in the layout template, and in `bazzite-pins.js` as a defensive second writer. Owns the pin order; it is the only place the list is defined. Fails the build if upstream moves or renames the template.
- `system_files/etc/xdg/mimeapps.list` — Brave as the default for `http`/`https`/`text/html` (keeps Bazzite's Bazaar `.flatpakref` association)
- `system_files/.../kicker-extra-favoritesrc` — the same bundled apps in application-launcher favorites

The browser slot deliberately stays `preferred://browser` rather than naming `com.brave.Browser.desktop`. It is the one entry confirmed to pin correctly on a fresh install, and it follows the user's default browser if they change it.

These live in the **bootc image**, not the live ISO payload, so they reach machines via `just build` + `bootc upgrade`/`switch`, or a fresh ISO install. Only brand-new user profiles get them: the template does not run for a user whose panel already exists, which is intended — PRODUCT_SPEC §11.2 forbids reapplying the desktop layout over a user's own changes.

### ChatGPT web app

Removed 2026-07-31. The previous Brave `--app=https://chatgpt.com/` launcher (`arcalium-chatgpt.desktop`) is gone from the image, Kickoff favorites and the panel pins. Users open ChatGPT in Brave themselves if they want it.

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

Plymouth (the “OS Loading” screen after GRUB) uses `/usr/share/plymouth/themes/spinner/watermark.png`. `build.sh` rasterises `logo-wordmark.svg` to that path at ~256×121 with a transparent background via ImageMagick. The default `bgrt` theme reads the same ImageDir, so both themes pick it up. `NAME` / `PRETTY_NAME` in `/usr/lib/os-release` are rewritten to Arcalium at the same time (keeping `ID=bazzite` for the live Anaconda profile).

#### Plymouth needs the initramfs rebuilt

Writing the watermark into `/usr` is not enough, and the failure is easy to misread as “the change did not apply”: Plymouth runs **from the initramfs during boot** and **from the root filesystem during shutdown**, so a `/usr`-only change gives you Arcalium on shutdown and stock Bazzite on boot.

bootc does **not** regenerate the initramfs on deploy — the image ships a prebuilt `/usr/lib/modules/<kver>/initramfs.img`, and the one inherited from Bazzite was generated before our layer existed. `build.sh` therefore rebuilds it. The arguments are not guesswork; the original invocation is recorded in the image and can be read back with:

```bash
lsinitrd /usr/lib/modules/<kver>/initramfs.img | head -1
# Arguments: --no-hostonly --kver '<kver>' --reproducible --zstd -v --add 'ostree' --add 'fido2' -f
```

We reuse exactly those, restore mode `0600`, and then assert that the watermark inside the new initramfs is byte-identical to the one in `/usr` and that its `os-release` says Arcalium. A wrong initramfs is an unbootable machine, so those assertions are deliberately fatal to the build. Consequences worth knowing:

- Build time grows by a few minutes and the image carries its own ~240 MB initramfs layer instead of sharing Bazzite's.
- `--reproducible` keeps the output stable across rebuilds, so the layer digest only churns when its inputs actually change.
- The live ISO was never affected: `installer/build.sh` already regenerates the payload initramfs (with `dmsquash-live`) on top of our branded `/usr`.

#### Login screen is plasmalogin, not SDDM

Plasma 6.7 replaced SDDM with `plasma-login-manager`, so `/etc/systemd/system/display-manager.service` points at `plasmalogin.service` and there is no `sddm` binary in the image at all. SDDM recipes found online do nothing here.

Its config cascade (from `PlasmaLoginSettings::getInstance()`) is `/etc/plasmalogin.conf` → `/etc/plasmalogin.conf.d/*` → `/usr/lib/plasmalogin/defaults.conf` → `/usr/lib/plasmalogin/plasmalogin.conf.d/*`. Distro defaults belong in `defaults.conf`, which we ship from `system_files`; anything a user picks in System Settings is written to `/etc/plasmalogin.conf` and still wins. The group nesting comes from `WallpaperIntegration` (`Greeter` → `Wallpaper` → plugin id) plus the plugin's own group (`General` for `org.kde.image`):

```ini
[Greeter][Wallpaper][org.kde.image][General]
Image=/usr/share/wallpapers/arcalium-wallpaper.png
```

The **lock** screen is separate again: Bazzite hard-codes `/usr/share/wallpapers/convergence.jxl` in `/etc/xdg/kscreenlockerrc` (and the kde-settings profile copy), and we override both. So three different files govern desktop, lock and login wallpaper — which is why a manually chosen desktop wallpaper sticks while the login screen still shows Bazzite.

### Hostname and Konsole welcome

The shell prompt’s `@bazzite` half is the machine hostname, not the OS name. Defaults:

- `DEFAULT_HOSTNAME=arcalium` in `/usr/lib/os-release` (Anaconda suggestion)
- `/etc/hostname` → `arcalium`
- `arcalium-migrate-hostname.service` renames a stock `bazzite` / `localhost` hostname once after rebase; custom hostnames are left alone

Konsole’s banner is the interactive MOTD (`/etc/profile.d/user-motd.sh`). We replaced Bazzite’s tip markdown with `fastfetch` using `/usr/share/arcalium/fastfetch.jsonc` and the ASCII mark in `/usr/share/arcalium/logo.txt`. `fastfetch` / `neofetch` aliases point at the same config. Per-user opt-out is unchanged: `touch ~/.config/no-show-user-motd` (or `ujust toggle-user-motd`).

#### The Konsole ASCII mark

`logo.txt` is plain ASCII art in the Ubuntu/`neofetch` idiom: the `A` of `assets/arccleanSVG.svg` built from `#` with a `.` / `:` stipple along its edges, crossed by a brighter swoosh rising from the lower-left and tapering off to the upper-right. `$1` / `$3` / `$5` are `fastfetch` colour slots resolved by `fastfetch.jsonc` — white swoosh, cyan `A`, light-blue stipple. Two earlier attempts are worth not repeating: stacked `/\` chevrons over widening `====` rows read as a christmas tree, and a Block Elements (`█ ▄ ▀`) version was legible but not the ASCII look we wanted.

Regenerate after changing the geometry constants (or just hand-edit the file — it is only text):

```bash
python tools/gen_ascii_logo.py system_files/usr/share/arcalium/logo.txt
```

To preview a draft on a running machine without a rebuild, point a copy of the config at it:

```bash
cp /usr/share/arcalium/fastfetch.jsonc ~/ff.jsonc   # edit "source" to your draft
fastfetch -c ~/ff.jsonc
```

Note how helper scripts are addressed: the `ctx` stage does `COPY build_files /`, so `build.sh`'s siblings are at `/ctx/install_logos.py`, **not** `/ctx/build_files/install_logos.py`. Getting this wrong fails the build immediately, which is how it was caught.

Still outstanding for full branding: a dark mark for light panels (current fills are white).

### Phase 2 — `arcaliumctl`

`/usr/bin/arcaliumctl` is a Python CLI (library under `/usr/lib/arcalium/ctl/`). Diagnostic commands only run allowlisted binaries (`nvidia-smi`, `vulkaninfo`, `lspci`, `lsmod`, `bootc`, `uname`) — never a user shell fragment. Proton install uses Python's `urllib` + `tarfile` against the GloriousEggroll GitHub releases API. Implemented commands:

```bash
arcaliumctl system summary --json
arcaliumctl gpu status --json
arcaliumctl gpu validate --json
arcaliumctl vulkan test --json
arcaliumctl proton list --json
arcaliumctl proton install-recommended --json
```

JSON schemas ship in `/usr/share/arcalium/schemas/` from `config/schemas/` (Containerfile `COPY config /config`). Remaining stubs (`apps`, `storage`, `vpn`, `updates`, `diagnostics`) exit `3` with `ARC-CMD-002`. Hardware runbook: [`docs/PHASE2_VALIDATION.md`](PHASE2_VALIDATION.md).

### Heroic Proton setup

Heroic Flatpak does not ship a Wine/Proton runtime. Without one, Windows game install/import fails and beginners have no idea to open **Settings → Wine Manager**.

The automatic pre-launch downloader was removed on 2026-07-31 because it did not behave reliably. Heroic now opens immediately. Proton setup is explicitly user-initiated through one of these paths:

- Control Centre → Compatibility → **Install recommended**
- Control Centre Overview → **Install Proton-GE**
- Heroic → Settings → Wine Manager
- `arcaliumctl proton install-recommended` (add `--force` to replace the recommended build)

`/usr/bin/arcalium-heroic` remains as a direct-launch compatibility shim because existing user profiles may still reference it. The `/etc/skel` desktop entry launches the Flatpak directly for new profiles. Installing GE-Proton needs network once (~400 MB).

### Icon names must exist in Breeze

Plasma's default theme is Breeze, and a desktop entry naming an icon Breeze does not carry renders blank. Bundled Flatpaks supply their own icons (`com.heroicgameslauncher.hgl` and friends), so their entries look blank until the Flatpak itself is installed — check `find /usr/share/icons/breeze* -name '<name>.*'` before shipping an entry.

### Control Centre

Source: [`apps/control-centre/`](../apps/control-centre/). Tauri 2 + React; app ID `io.arcalium.ControlCentre`.

- The Containerfile `control-centre` stage builds the Linux binary on Fedora 42 and places it in the `ctx` mount as `/control-centre/arcalium-control-centre`.
- `build_files/build.sh` installs it to `/usr/bin/arcalium-control-centre`, ensures `webkit2gtk4.1` is present, and installs the hicolor icon.
- The UI invokes only allowlisted `arcaliumctl` argv sequences (see `apps/control-centre/src-tauri/src/ctl.rs`). All §9.2 pages are live. App catalogue: `config/catalogue/apps.v1.json` → `/usr/share/arcalium/catalogue/`. `apps install|uninstall` are user Flatpak only (ID allowlisted in Rust + catalogue). Updates page shows `bootc` status and copyable apply/rollback commands but does not run them. Diagnostics can write a redacted bundle under `~/.local/state/arcalium/`. Quick actions launch allowlisted `.desktop` files via `gio launch` (fallback `gtk-launch` / `kioclient exec`) — never `xdg-open` on the path.
- Local iteration: `just build-control-centre` (WSL + Podman) extracts artifacts to `output/control-centre/`.
- Desktop entry: `io.arcalium.ControlCentre.desktop`; in Kickoff favorites for new Plasma users, deliberately not pinned to the panel (its icon is the Arcalium mark and would duplicate the launcher button).
- **Window icon:** we build with `--no-bundle`, so `bundle.icon` in `tauri.conf.json` is only consumed by bundlers and never reaches the running window — the window showed the toolkit's default mark instead. Two fixes are needed because the two display servers source the icon differently:
  - X11 reads `_NET_WM_ICON`, so `lib.rs` calls `window.set_icon()` with `include_bytes!("../icons/256x256.png")` (requires the `image-png` feature on the `tauri` crate). `apps/control-centre/build.sh` generates those PNGs from `assets/arccleanSVG.svg` before cargo runs, so the include always resolves.
  - Wayland has no per-window icon protocol in GTK3, so KWin takes the icon from the `.desktop` file it matches by `app_id`. GTK reports the program name (`arcalium-control-centre`), which does not match `io.arcalium.ControlCentre.desktop`, hence `StartupWMClass=arcalium-control-centre` in the entry. To confirm the value on a live machine, run `qdbus6 org.kde.KWin /KWin org.kde.KWin.queryWindowInfo` and click the window; `resourceClass` must equal `StartupWMClass`.
- **In-app mark:** the sidebar mark was a CSS `clip-path` triangle placeholder. `App.tsx` now imports `assets/arccleanSVG.svg` from the repo root so the UI cannot drift from the OS icons. The import escapes the Vite root, which Rollup handles for builds; `server.fs.allow` covers `npm run dev`. The mark carries `.st0 { fill: #fff }`, which suits the dark sidebar.
- **NVIDIA/WebKitGTK:** on Wayland the webview process dies before a window appears (blank window on X11). Confirmed on the RTX 3060: the app runs under `__NV_DISABLE_EXPLICIT_SYNC=1` and dies without it. The desktop entry exports that variable through `Exec=env …`, and `main.rs` additionally sets the session-appropriate variable before WebKit initialises so terminal launches and X11 sessions are covered. Set `ARCALIUM_CC_NO_GPU_WORKAROUND=1` to opt out.

Setup wizard shares this codebase (`arcalium-control-centre --setup` / `arcalium-setup`). Visual polish of the Control Centre UI is deferred until every §9.2 page works (see `docs/IMPLEMENTATION_STATUS.md` Decisions).

### Setup wizard

- Progress: `~/.config/arcalium/setup-progress.json`; completion: `setup-complete.json` (PRODUCT_SPEC §8.2).
- CLI: `arcaliumctl setup status|save|mark|complete|reset --json`.
- Autostart: `/etc/xdg/autostart/arcalium-setup.desktop` and skel copy call `arcalium-setup --autostart` (no-op on live ISO and when already complete).
- Menu: `io.arcalium.Setup.desktop` always opens the wizard (Resume).
- Control Centre → Settings: Resume / Restart setup (restart confirms then `setup reset`).
- Privileged policy matches Control Centre: user Flatpak installs OK; `bootc` apply and VPN secret import are guidance only; no disk formatting.

### Install time and the deploy step

An install writes the whole OS image to disk, so it takes 15–40 minutes and spends nearly all of that inside one Anaconda step with little visible progress. Anaconda reports nothing during `ostree container deploy`; `hwclock` is often the last log line before it starts. The former external progress tracker was removed because it launched as soon as Anaconda opened, before the user completed the installer wizard, which made its status misleading.

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
