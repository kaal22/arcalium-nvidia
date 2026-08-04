# Arcalium OS — Implementation Status

**Edition:** NVIDIA Edition  
**Channel:** `0.2.0` / `stable` prep (CI tip `:dev`; GHCR still private until download page)  
**Upstream template:** [ublue-os/image-template](https://github.com/ublue-os/image-template) @ `3d68ac893a31f5947dfe6210c04aee2cc469a02e`  
**Base image:** `ghcr.io/ublue-os/bazzite-nvidia-open:stable@sha256:83c6084f9713abda10b966dce3631f4c9b4430e419f06c9a76dad10bfc43cbe9` (resolved 2026-07-29)  
**Status values:** `not started` · `in progress` · `blocked` · `tested` · `complete`

---

## Where we left off (2026-08-04)

**0.2.0 public release path:** notices/privacy/support accepted; Promote stable workflow added; getarcalium.com must ship a real ISO download before flipping GHCR public. Primary hardware remains the **3060**.

**Shipped on `main` through Local AI min-spec (`335e611`+):**
- Public-prep app policy: Firefox bundled; Brave / Spotify / Steam on-demand
- KDE Partition Manager in image — Setup/Control Centre **Open disk utility**
- Ollama install tolerates brew non-zero exit when the `ollama` binary is present
- Public-friendly catalogue descriptions (no Flatpak IDs as card copy)
- Local AI Desktop shortcut + Space Invaders pixel icon after model pull (`io.arcalium.Assistant` / `arcalium-assistant`)
- Local AI minimum hardware soft-warn: **16 GiB RAM / 8 GiB VRAM** in Setup + Control Centre

**Next:** RC smoke on 3060 (`docs/RC_SMOKE_0.2.0.md`); cut `Arcalium-Live-0.2.0.iso`; Promote `0.2.0`+`stable`; GitHub Release; then public GHCR after download page.

**Roles**

| Role | Machine | Notes |
|---|---|---|
| Build | this Windows workstation + WSL Ubuntu | Edit here, push, pull in WSL, `just build` / `just build-iso-live` |
| Hardware test | separate bare-metal PC, RTX **3060 12 GB** | Installs and post-boot checks only; not the build host |
| VMware | retired for install validation | Used once to prove the ISO chain; further installs are bare metal |

**Last successful artifacts**

| Artifact | Location | Notes |
|---|---|---|
| Live ISO — **current** | Desktop `Arcalium-Live-alpha-final.iso` (~7.3 GB) + WSL `~/arcalium-nvidia/output/Arcalium-Live.iso` | Built **2026-08-03** from `cf0008f` (public-friendly app descriptions). Does **not** yet include `2b77d67` AI Desktop shortcut — that needs another full ISO or bootc upgrade only for installed systems |
| GHCR image — **current** | `ghcr.io/kaal22/arcalium-os-nvidia:dev` (private) | Through `2b77d67` (AI shortcut); 3060 uses `sudo bootc upgrade` |
| OCI image (WSL) | `localhost/arcalium-os-nvidia:dev` | Local build cache for ISO |
| Payload image (WSL) | `localhost/arcalium-os-nvidia-payload:dev` | Live/installer layer |

**Proven**

- `just build` and `just build-iso-live` in WSL Ubuntu (titanoboa — not BIB)
- Full install chain on VMware (retired) then **bare metal RTX 3060**
- Repeated `bootc upgrade` on the 3060 from private GHCR
- Partition Manager, Firefox-default / Brave·Spotify on-demand, Local AI pull path exercised in alpha

**Not finished — next**

1. RC smoke on 3060 (`docs/RC_SMOKE_0.2.0.md`) after CI for min-spec image.
2. Cut `Arcalium-Live-0.2.0.iso` (full `just build` first) — see `NEXT_ISO.md`.
3. Promote `0.2.0` + `stable` (Promote stable workflow); GitHub Release with checksums.
4. Ship real download on getarcalium.com → flip GHCR public.

**Resume commands**

```powershell
wsl -d Ubuntu -u root
cd /home/kaal/arcalium-nvidia && git pull
just build && just build-iso-live
# Copy via the WSL helpers; Desktop target: Arcalium-Live-alpha-final.iso
```

On the 3060: `sudo bootc upgrade && sudo systemctl reboot` (private GHCR may need ostree/podman auth — see `docs/BUILDING.md`).

Repo: https://github.com/kaal22/arcalium-nvidia

---

## Phase 0 — Repository and research

| Requirement | Status | Notes |
|---|---|---|
| Repository created from current `ublue-os/image-template` | complete | Copied template tree; history retained from template commit above |
| `docs/PRODUCT_SPEC.md` | complete | Copied from `Arcalium_OS_NVIDIA_Product_Spec.md` |
| `docs/IMPLEMENTATION_STATUS.md` | complete | This file |
| Licence inventory | complete | Accepted for 0.2.0 in `docs/LICENSING.md` |
| Confirmed image tag `bazzite-nvidia-open:stable` | complete | GHCR tags include `stable`; digest pinned in Containerfile |
| Confirmed build workflow | complete | `.github/workflows/build.yml` + `build-disk.yml` present |
| Cosign setup (public key committed, private key secret) | complete | `cosign.pub` in repo; `SIGNING_SECRET` set in Actions |
| Private GHCR `dev` image | complete | `ghcr.io/kaal22/arcalium-os-nvidia:dev` published and Cosign-signed 2026-07-30; package stays private per spec §17.2 |
| Image signature verifies | blocked | Depends on first successful signed publish |
| Test machine switch / QCOW2 boot | blocked | Depends on published image; bootstrap path is rebase from stock Bazzite, see `docs/BUILDING.md` |

## Phase 1 — Minimal Arcalium NVIDIA image

| Requirement | Status | Notes |
|---|---|---|
| NVIDIA-open Bazzite base | complete | Containerfile uses verified base |
| Arcalium image metadata | complete | `image-template.env` + `/etc/arcalium/image-info.json` |
| Basic branding | in progress | Wallpaper (desktop + lock + login), logo mark/wordmark, Plasma splash, Plymouth watermark + initrd-release NAME wired; dark-panel mark still needed |
| Arcalium wallpaper | in progress | 5504×3072 asset installed for new Plasma desktops; lock screen via `kscreenlockerrc`; login screen via `/usr/lib/plasmalogin/defaults.conf` (not SDDM). Redistribution licence record pending |
| Control Centre placeholder | complete | Full Control Centre + Setup wizard shipped in image; overview-only placeholder retired |
| First-boot placeholder | complete | Setup via Desktop/Kickoff Control Centre (`arcalium-control-centre-launch`); no login Setup autostart |
| QCOW2 workflow | tested | Built locally in WSL2, 5.8 GB; superseded by bare-metal validation |
| ISO workflow | tested | Bare-metal install on RTX 3060 12 GB; live session needs Basic Graphics (`nomodeset`) on Nouveau |
| Bootc Image Builder ISO (`just build-iso`) | blocked | Upstream BIB #1188 — do not use |

## Phase 2 — Hardware validation

| Requirement | Status | Notes |
|---|---|---|
| Bare-metal install (primary test PC) | tested | RTX **3060 12 GB**: `:dev` image, `nvidia-smi` OK, Wayland, Secure Boot off, 0 failed units |
| `arcaliumctl system summary` | tested | RTX 3060: `--json` passed as expected (2026-07-31) |
| `arcaliumctl gpu status` | tested | Same |
| NVIDIA / Vulkan / Wayland validation | tested | `gpu validate` + `vulkan test` `--json` passed on 3060; Wayland confirmed earlier |
| Steam / Heroic game path | tested | Owner-confirmed on RTX 3060 (2026-07-31) |
| Diagnostics JSON schemas | complete | `/usr/share/arcalium/schemas/*.json` from `config/schemas/` |

## Phase 3 — Setup wizard

| Requirement | Status | Notes |
|---|---|---|
| First-run service + resume state | complete | Per-user markers under `~/.config/arcalium/`; `arcaliumctl setup status/save/mark/complete/reset/set-autostart`; prefs `setup-prefs.json` (`showOnStartup`); **no login autostart** — Desktop/Kickoff Control Centre via `arcalium-control-centre-launch` opens Setup until finished; Settings toggle + Resume/Restart; menu `io.arcalium.Setup` |
| Wizard pages (hardware → completion) | complete | Shared Control Centre binary `--setup` mode; 14 pages per §8.3 including optional `localAi` before Finish. Updates/VPN secrets/format stay guidance-only. |

## Phase 4 — Application provisioning

| Requirement | Status | Notes |
|---|---|---|
| Declarative app catalogue | complete | `config/catalogue/apps.v1.json` → `/usr/share/arcalium/catalogue/`; public-friendly descriptions; Control Centre Applications/Gaming/Streaming cards |
| Spotify / ProtonPlus / optional launchers | complete | **ISO bundles** Firefox, ProtonPlus, Heroic. **On-demand:** Brave, Spotify, Steam (Flathub via Control Centre). Lutris dropped. |

## Phase 5 — Proton-GE

| Requirement | Status | Notes |
|---|---|---|
| Recommended-version manifest + install action | in progress | `arcaliumctl proton list` / `install-recommended`; Control Centre **Compatibility** page + Overview Install Proton-GE quick action wire the same CLI. Heroic pre-launch automation removed 2026-07-31; installation is explicit. |

## Phase 6 — Storage and VPN

| Requirement | Status | Notes |
|---|---|---|
| Drive scan / filesystem warnings | in progress | Control Centre / Setup Storage: read-only `arcaliumctl storage scan`; **Open disk utility** → KDE Partition Manager (`kde-partitionmanager` layered in image). No format from UI. |
| ProtonVPN import flow | in progress | Status + optional Proton VPN Flatpak; secret import stays in the VPN client / Plasma Network — not Control Centre. |

## Phase 7 — Control Centre completion

| Requirement | Status | Notes |
|---|---|---|
| All version 1 pages | complete | All §9.2 pages live including Local AI Assistant. User Flatpak install/uninstall; no Polkit / no bootc mutate from UI. **Visual polish deferred**. |
| Local AI Assistant (§9.14) | complete | Safe terminal agent; Homebrew Ollama + model pull with live progress; base `gemma4:e4b-it-qat`. Brew non-zero exit treated as OK when `ollama` is present. After pull: Desktop shortcut + menu entry `io.arcalium.Assistant` (Space Invaders pixel icon) via `arcalium-assistant`. |

## Phase 8 — Private alpha

| Requirement | Status | Notes |
|---|---|---|
| `0.1.0-alpha.1` signed image + ISO + QCOW2 | complete | Superseded by 0.2.0 path; historical notes kept |
| Hardware matrix (RTX 3090 + 2× RTX 2060) | deferred | Primary hardware is RTX **3060 12 GB** |
| Notices / privacy / support / recovery | complete | Accepted for 0.2.0 |
| Brave / Spotify ISO redistribution | complete | Removed from `installer/flatpaks`; Firefox bundled instead; Brave/Spotify Flathub on demand |

## Phase 9 — Public-release preparation

| Requirement | Status | Notes |
|---|---|---|
| Steam licensing gate | complete | Steam not in image/ISO; Flathub via Control Centre |
| Brave / Spotify ISO gate | complete | Not bundled; Flathub on demand (Firefox is the default browser) |
| Trademark / notices / privacy | complete | Accepted for 0.2.0 |
| Promote `0.2.0` / `:stable` workflow | complete | `.github/workflows/promote-stable.yml` |
| Public download site | in progress | Domain live as placeholder; **must** host ISO + checksums before GHCR public flip |
| Public GHCR package | blocked | Waiting on getarcalium.com download page |

## Phase 10 — AMD/Intel edition

| Requirement | Status | Notes |
|---|---|---|
| `FROM ghcr.io/ublue-os/bazzite:stable` edition | not started | After NVIDIA desktop is stable |

---

## Immediate Cursor task list (spec §28)

| # | Task | Status |
|---|---|---|
| 1 | Create repo from latest `image-template` | complete |
| 2 | Set base to `bazzite-nvidia-open:stable` | complete |
| 3 | Set metadata for `arcalium-os-nvidia` | complete |
| 4 | Add `docs/PRODUCT_SPEC.md` | complete |
| 5 | Add `docs/IMPLEMENTATION_STATUS.md` | complete |
| 6 | Configure Cosign (no private key in git) | complete — `cosign.pub` in repo; `SIGNING_SECRET` set in Actions 2026-07-30 |
| 7 | Build/publish private `dev` image to GHCR | complete — `ghcr.io/kaal22/arcalium-os-nvidia:dev` published 2026-07-30 |
| 8 | Verify image signature | complete — CI Cosign sign + local `cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:dev` (digest `sha256:bbcea0…ebe90`) |
| 9 | Build QCOW2 | complete — `output/qcow2/disk.qcow2`, built locally under WSL2 |
| 10 | Boot-test unbranded image | complete — VM then bare-metal RTX 3060 12 GB |
| 11 | Build installer ISO | complete — `output/Arcalium-Live.iso` via titanoboa (`just build-iso-live`) |
| 12–13 | Hardware install | complete (primary) — RTX 3060 12 GB; original 3090/2060 checklist deferred |
| 14 | Record commands, failures, upstream changes | in progress — see below |
| 15 | Do not begin Control Centre until base+ISO proven | complete (honoured) |

---

## Verification log

| Date | Action | Result |
|---|---|---|
| 2026-07-29 | Cloned `ublue-os/image-template` | HEAD `3d68ac8` |
| 2026-07-29 | Confirmed GHCR package `ublue-os/bazzite-nvidia-open` tags include `stable` | OK |
| 2026-07-29 | Resolved `:stable` digest | `sha256:83c6084f9713abda10b966dce3631f4c9b4430e419f06c9a76dad10bfc43cbe9` |
| 2026-07-29 | Generated Cosign keypair (v2.6.3) | `cosign.pub` + local `cosign.key` |
| 2026-07-29 | Local OCI build on this Windows workstation | resolved — WSL2 Ubuntu 24.04 provisioned with Podman 4.9.3 as the local build host |
| 2026-07-29 | WSL2 privileged container loop-device support | OK — `/dev/loop-control` visible, `losetup -f` returns `/dev/loop0` |
| 2026-07-29 | Podman `--security-opt label=type:unconfined_t` on non-SELinux host | accepted; no Justfile change required |
| 2026-07-29 | Ubuntu apt `just` 1.21 vs Justfile `[group(...)]` attributes | incompatible — installed upstream `just` 1.57.0 to `/usr/local/bin` |
| 2026-07-29 | Root build against user-owned clone | git refused with "dubious ownership"; fixed with `safe.directory` for root |
| 2026-07-29 | `just build` | **success** — `localhost/arcalium-os-nvidia:dev`, 13.2 GB, ~3 min, `bootc container lint` 13 checks passed, 1 skipped |
| 2026-07-29 | Arcalium files present in built image | `/etc/arcalium/image-info.json` and `/usr/share/arcalium/os-release.snippet` verified |
| 2026-07-29 | `just build-qcow2` | **success** — `output/qcow2/disk.qcow2`, 5.8 GB, ~14 min; loop devices, Btrfs and `bootc install-to-filesystem` all worked under WSL2 |
| 2026-07-29 | `just build-iso-live` (titanoboa) | **success** — payload image 27.4 GB; `output/Arcalium-Live.iso` ~6 GB squashfs live installer |
| 2026-07-29 | Live ISO Install button | **failed silently** — Anaconda had no profile for `os_id=bazzite`; fixed with `installer/system_files/etc/anaconda/profile.d/bazzite.conf` |
| 2026-07-29 | Steam autostart on live ISO | Expected from Bazzite skel; suppressed in payload (`rm steam.desktop`, hide announcements, add Arcalium welcome dialog) |
| 2026-07-29 | Rebuild `Arcalium-Live.iso` with installer fixes | **success** — payload verified (profile present, Steam gone, welcome + Install launcher); ISO ~6.1 GB |
| 2026-07-29 | Install still silent after profile fix | Missing Firefox — `anaconda-webui` needs it at runtime; soft RPM dep does not pull it without `fedora-release-workstation`. Installing Firefox like Bazzite. |
| 2026-07-29 | `disk_config/disk.toml` `[[customizations.filesystem]]` | reported unsupported for `qcow2` by this BIB version; the 20 GiB minsize was ignored and a default layout used |
| 2026-07-29 | VM boot of `Arcalium-Live.iso` with BIOS firmware | failed to PXE — titanoboa ISOs are UEFI-only; resolved by switching the VMware VM to UEFI |
| 2026-07-29 | Live ISO Install after adding Firefox | **works** — Anaconda launches and reaches deployment |
| 2026-07-29 | Anaconda `ostreecontainer` deploy step duration | slow but healthy — `ostree-container ... deploy` sat on "Deployment starting…" for 10+ min while unpacking a 27 GB payload; confirmed alive via CPU time, not hung |
| 2026-07-29 | Deploy step is indistinguishable from a hang | Initially added `arcalium-install-progress.sh`, but removed it 2026-07-31 because it started before the user completed Anaconda's wizard and therefore presented misleading progress. |
| 2026-07-31 | Dropped live-session welcome popup | Autostart dialog framed the session as a "test environment"; testers preferred the stock desktop Install launcher. Removed `arcalium-live-welcome.sh` and its skel autostart. `liveinst.desktop` → `arcalium-install.sh` remains so `--profile bazzite` stays required. Needs an ISO rebuild to take effect. |
| 2026-07-31 | Panel / favourites trim | Control Centre and ProtonPlus no longer pinned to Icon Tasks (Control Centre icon duplicates Kickoff; ProtonPlus is a utility). ChatGPT Brave web-app launcher removed entirely. Kickoff still lists Control Centre and ProtonPlus. |
| 2026-07-29 | titanoboa builds a **gzip** squashfs, not zstd | Upstream `build_iso.sh` puts `-comp zstd -Xcompression-level 19` after `-e`, and `mksquashfs` reads everything after `-e` as exclude paths. Log line: `Exportable Squashfs 4.0 filesystem, gzip compressed`. `build-iso-live` now patches the clone and asserts the fix. Worth an upstream PR. |
| 2026-07-29 | Rebuild with zstd fix | **success** — `Exportable Squashfs 4.0 filesystem, zstd compressed`; squashfs 5.30 GiB (was 5.71), ISO 5.8 GB (was 6.2) |
| 2026-07-29 | **Full install + first boot in VMware** | **success** — installed from `Arcalium-Live.iso` (8 vCPU, 16 GB, 40 GB NVMe-controller disk, UEFI) and booted to the first-run setup wizard. First end-to-end proof of the ISO → install → boot chain. |
| 2026-07-29 | Deploy step throughput measured | `vmstat 5` during deploy: ~7 MB/s, `wa` 7–15%, CPU 81–85% idle, `b` 1–2. **Disk-bound, not CPU-bound** — ostree's small-file, checksum-and-sync writes through VMware's virtual disk. More vCPUs will not help. |
| 2026-07-29 | Progress window reported delta, not total | Historical: changed to total-on-target, then the tracker was removed 2026-07-31 because its lifecycle began before Anaconda installation actually started. |
| 2026-07-29 | Anaconda finish screen offers no restart | Live installer returns to the desktop and tells the user to exit it. Acceptable for alpha; an end user expects an explicit "Restart now". Polish item. |
| 2026-07-29 | `bootc status` on the installed VM | `localhost/arcalium-os-nvidia:dev` as predicted — the ISO's embedded image, so `bootc upgrade` is inert until the GHCR package is published and the system is repointed |
| 2026-07-29 | First-run setup completed; Steam installed on the installed system | **correct behaviour** — Steam belongs on the installed system and was only suppressed in the live installer session |
| 2026-07-29 | Firefox present on live ISO, absent from installed system | Expected today — Firefox is installed only into the titanoboa payload for Anaconda Web UI, not into the shipped OS image. Candidate for the installed system: package Brave instead of (or alongside) Firefox. Decision deferred. |
| 2026-07-29 | Installed system shows **Bazzite** first-run wizard and logo | Expected at this phase — no branding work has been done, and the spec gates Control Centre and branding behind proving base + ISO. Records the branding surfaces that need replacing: first-run wizard, logo, `os-release`, Plymouth. |
| 2026-07-29 | Bare-metal live session on NVIDIA | Default GRUB entry: Bazzite splash → black screen + cursor for minutes → late Arcalium welcome. **Basic Graphics Mode** (`nomodeset`) shows desktop. Ventoy needs **GRUB2** mode. Live uses Nouveau; installed system uses nvidia-open. |
| 2026-07-29 | Progress window closed immediately on bare metal | Race: monitor started before Anaconda process existed. Fixed in `7e172de` (next ISO). Manual restart of the script still works. |
| 2026-07-29 | Bare-metal deploy throughput | ~17–30 MiB/s vs ~7 MiB/s in VMware — confirms VM slowness was virtual disk, not the image. |
| 2026-07-30 | **Bare-metal install + boot on RTX 3060 12 GB** | **success** — `localhost/arcalium-os-nvidia:dev`, `nvidia-smi` OK, Wayland, Secure Boot disabled, 0 failed units. Primary hard-install test machine going forward; VMware dropped for install validation. Spec checklist 3090/2060 deferred. |
| 2026-07-30 | **No browser on the installed system** | Root cause: our hand-written `installer/build.sh` omitted the Flatpak provisioning step that upstream Bazzite runs (`flatpak install` from `installer/<de>_flatpaks/flatpaks`), which is where Bazzite's own Firefox comes from. Live-session Firefox is an `anaconda-webui` dependency and never reaches disk. Fixed by adding `installer/flatpaks` plus the Flathub remote and `var-lib-flatpak.mount` in the payload build. |
| 2026-07-30 | Browser choice: **Brave** (`com.brave.Browser`) | Flathub-verified via `brave.com`, publisher Brave Software, MPL-2.0, so no community-maintained caveat is needed. Its Flathub manifest repacks Brave's official release zip at build time rather than using `extra-data`, so the Flatpak can be bundled into the ISO and installed offline. Redistribution check recorded in `docs/LICENSING.md`. |
| 2026-07-30 | Bundled-app taskbar defaults | `arcalium-pins.js` (before `bazzite-pins.js`, empty-launchers only) and `kicker-extra-favoritesrc` now include Brave, ChatGPT web app, Spotify, ProtonPlus and Heroic; Steam and Bazaar remain pinned. Matches PRODUCT_SPEC §11.2 skeleton-defaults rule and never overwrites an existing user's layout. |
| 2026-07-30 | ChatGPT added to application menu and taskbar | Dedicated Brave web-app launcher for the official `https://chatgpt.com/` site. No official Linux ChatGPT app exists, so no unofficial credential-handling wrapper is bundled. No OpenAI assets or client binaries are redistributed. |
| 2026-07-30 | Spotify and ProtonPlus bundled | Added verified IDs `com.spotify.Client` and `com.vysp3r.ProtonPlus` to `installer/flatpaks`. Spotify is proprietary, community-maintained and unsupported by Spotify; disclosure and public-ISO redistribution gates recorded in `docs/LICENSING.md`. ProtonPlus is a publisher-verified GPL compatibility-tool manager—not Proton VPN. |
| 2026-07-30 | Arcalium desktop wallpaper wired in | `assets/arcalium-wallpaper.png` is installed to `/usr/share/wallpapers/` and selected through the Bazzite Vapor look-and-feel setup script for newly created Plasma desktops only. Existing user wallpaper is not overwritten. Source is 5504×3072 (the IDE preview was downscaled); redistribution licence record remains. |
| 2026-07-30 | Logo mark + wordmark wired | Sources `assets/arccleanSVG.svg` (Kickoff/distributor mark) and `assets/ARG_fullSVG.svg` (wordmark). `install_logos.py` strips Illustrator metadata (~46 KB→~1 KB mark, ~68 KB→~7 KB wordmark) and installs into hicolor places + `/usr/share/arcalium/`. Plasma splash `bazzite_logo.svgz` replaced with gzipped wordmark where present. Plymouth watermark PNG and dark-panel mark still needed. |
| 2026-07-30 | Plymouth + login wallpaper | Spinner `watermark.png` rasterised from `ARG_fullSVG.svg` (~256×121 RGBA). `/usr/lib/os-release` NAME/PRETTY_NAME rewritten to Arcalium (ID stays `bazzite` for Anaconda). Lock greeter (`kscreenlockerrc`) retargeted from `convergence.jxl`. |
| 2026-07-30 | Boot still Bazzite after watermark change | Expected given the mechanism: Plymouth boots from the initramfs and shuts down from `/usr`, so a `/usr`-only change produces exactly "Arcalium on shutdown, Bazzite on boot". bootc does not regenerate the initramfs on deploy. Fixed by rebuilding `/usr/lib/modules/<kver>/initramfs.img` in `build.sh` with the args `lsinitrd` records, then asserting watermark byte-identity and `NAME="Arcalium OS"` in `initrd-release`. |
| 2026-07-31 | Phase 2 `arcaliumctl` | Shipped Phase-2-only CLI: `system summary`, `gpu status`, `gpu validate`, `vulkan test` with allowlisted subprocesses, ARC-* codes, and JSON schemas under `/usr/share/arcalium/schemas/`. Runbook: `docs/PHASE2_VALIDATION.md`. |
| 2026-07-31 | Phase 2 CLI on RTX 3060 | **pass** — `arcaliumctl system summary|gpu status|gpu validate|vulkan test --json` all behaved as expected on the upgrade install. Game-path checklist still open. |
| 2026-07-31 | Lutris dropped from catalogue | Product decision: do not offer Lutris. Heroic covers Epic/GOG/Amazon; dual launchers would duplicate that role. Spec + Flatpak ID list updated; Lutris was never in `installer/flatpaks`. |
| 2026-07-31 | Phase 2 game path on RTX 3060 | **pass** — Steam and Heroic exercised (owner-confirmed). Phase 2 hardware validation complete; Control Centre gate open for private alpha. |
| 2026-07-31 | Control Centre Overview MVP | Tauri 2 + React app `io.arcalium.ControlCentre`: nav shell for all §9.2 pages, Overview live from allowlisted `arcaliumctl` JSON, stubs elsewhere. Built in Containerfile `control-centre` stage; installed to `/usr/bin/arcalium-control-centre` with WebKit runtime + Kickoff favourite (panel pin dropped 2026-07-31 — its icon duplicates the Kickoff launcher mark). |
| 2026-07-31 | Control Centre Compatibility page | First live page beyond Overview. Allowlists `proton list` / `install-recommended` (30 min timeout for download), Open ProtonPlus via Flatpak export path resolution, static ProtonDB / anti-cheat links. Overview Quick action Install Proton-GE uses the same install command. |
| 2026-08-03 | Local AI Desktop shortcut | After model pull/ensure: trusted `~/Desktop/arcalium-assistant.desktop` + menu `io.arcalium.Assistant` + `arcalium-assistant` launcher; Space Invaders-style pixel icon (`assets/io.arcalium.Assistant.png`). GHCR `2b77d67`. |
| 2026-08-03 | Alpha live ISO rebuild | Desktop `Arcalium-Live-alpha-final.iso` (~7.3 GB) from `cf0008f` (friendly catalogue descriptions). Old Desktop/WSL Arcalium ISOs deleted before rebuild. |
| 2026-08-03 | Partition Manager | `kde-partitionmanager` layered in image; Setup/Control Centre Open disk utility no longer falls back to System Settings. GHCR `fa4162f`. |
| 2026-08-03 | Ollama brew false failure | Install succeeds when `ollama` binary is present even if `brew install` exits non-zero. |
| 2026-08-02 | Public-prep Flatpaks + docs | Firefox bundled as default; Brave/Spotify/Steam on-demand. Notices, privacy, support, recovery, install guide, draft release notes. |
| 2026-08-01 | Setup wizard (Phase 3) | Shared Control Centre `--setup` mode with 13 pages (§8.3). State via `arcaliumctl setup` → `~/.config/arcalium/setup-progress.json` / `setup-complete.json`. Autostart `arcalium-setup --autostart` (live + completed skipped); menu `io.arcalium.Setup.desktop`; Settings Resume/Restart. Updates/VPN secrets/format remain guidance-only. |
| 2026-08-01 | Every `arcaliumctl` command crashed after the pages commit | `apps.py` computed a repo-checkout catalogue fallback with `Path(__file__).resolve().parents[5]` at import time. That index is valid in the checkout (`<repo>/system_files/usr/lib/arcalium/ctl/`) but the installed path `/usr/lib/arcalium/ctl/` has only five parents, so it raised `IndexError: 5` while importing — taking down every subcommand and the whole Control Centre, which reported only "Could not load diagnostics". Now probed by `len(parents)` instead of indexed blindly. `build.sh` runs `arcaliumctl --help` and parses the catalogue so an import-time break fails CI rather than shipping. |
| 2026-07-31 | Control Centre showed the wrong icon in two places | Both were placeholders never revisited. **Window/taskbar icon:** `--no-bundle` means `bundle.icon` is consumed only by bundlers, so the running window fell back to the toolkit default. X11 needed `window.set_icon()` (`image-png` feature, embedding the generated `icons/256x256.png`); Wayland has no GTK3 window-icon protocol and matches `app_id` to a desktop file instead, so the entry gained `StartupWMClass=arcalium-control-centre` to match GTK's program name against `io.arcalium.ControlCentre.desktop`. **Sidebar mark:** a CSS `clip-path` triangle, now the real `assets/arccleanSVG.svg` imported from the repo root so the UI and OS icons share one source. |
| 2026-07-31 | Batched live ISO with Control Centre | **built** — 7.7 GB `Arcalium-Live.iso` from `49b5e7d`. Desktop copy as `Arcalium-Live-CC.iso` (old Desktop ISO locked); Ventoy `F:\Arcalium-Live.iso`. GHCR `:dev` published [run 30626397101](https://github.com/kaal22/arcalium-nvidia/actions/runs/30626397101). |
| 2026-07-31 | Heroic silent no-op after Proton download | Self-inflicted. `install-recommended` created `config.json` when absent, writing only three `defaultSettings` keys; Heroic expects a full block and refuses to open on a partial one with no error printed. On a fresh install the wrapper always runs before Heroic's first launch, so it hit this every time. Now only merges into a config Heroic wrote, and writes via temp-file rename. Recovery on an affected machine: delete `~/.var/app/com.heroicgameslauncher.hgl/config/heroic/config.json`. |
| 2026-07-31 | Login splash wordmark squashed | Vapor/VGUI `Splash.qml` sets both `sourceSize.width` and `sourceSize.height` to `size`, rasterising into a square. Correct for Bazzite's square mark, wrong for our 510×242 wordmark. `build.sh` now deletes the height line (unique to the logo — the spinner uses grid units) so Qt derives it from the aspect ratio, and asserts the edit. |
| 2026-07-31 | Only Brave pinned on a fresh install, none of the other bundled apps | Not a partial success — nothing of ours was pinned at all. Bazzite patches the Plasma panel layout template to write its launcher list, and that runs before update scripts, all of which skip when `launchers` is non-empty. Our `arcalium-pins.js` update script never executed. Brave appeared because Bazzite's list starts with `preferred://browser`, which resolves through our `mimeapps.list` default. Replaced the script with `build_files/patch_panel_pins.py`, which rewrites the array in the layout template (and in `bazzite-pins.js`) at build time. Verified against the real files from the `:dev` image; needs a fresh-install check to confirm on hardware. |
| 2026-07-31 | Install aborted: "critical error running post installation scripts" | The separate `arcalium-flatpak-selinux.ks` ran `chcon -R -t var_lib_t /var/lib/flatpak` as a chroot `%post`, but Anaconda's chroot does not see the deployment's `/var`, so the path did not exist and the script failed. It carried `--erroronfail` (copied from Bazzite), which turned that into an aborted install even though the OS had already deployed successfully — the machine booted fine and had all four Flatpaks. Merged into the single `--nochroot` copy script, which now relabels the path it just wrote, never exits non-zero, and drops `/var/log/arcalium-flatpaks-failed` on the target if the copy did not happen. The copy target itself was correct and is unchanged; the deployment glob no longer assumes a stateroot named `default`. |
| 2026-07-31 | Bundled Flatpaks never installed | Fresh installs shipped with no Brave/Spotify/ProtonPlus/Heroic and an apparently empty taskbar. `ostreecontainer` deploys only the container image; the live `/var/lib/flatpak` needs an explicit `%post --nochroot` rsync, which we never wrote (upstream Bazzite has `install-flatpaks.ks`). Pins then referenced `.desktop` files Plasma could not resolve and silently dropped them. Added `arcalium-install-flatpaks.ks` + SELinux relabel. Verifiable only via a rebuilt ISO. |
| 2026-07-31 | Blank menu icons after upgrade | Two causes. ChatGPT used `Icon=web-browser`, absent from Breeze (present only in `AdwaitaLegacy`) — changed to `internet-web-browser`. Heroic's icon ships with the Flatpak, so its entry stays blank until the Flatpak is installed. |
| 2026-07-31 | Duplicate Heroic menu entry | Self-inflicted by the first-run Proton commit: shipping `com.heroicgameslauncher.hgl.desktop` under `/usr/share/applications` cannot override the Flatpak export (which outranks `/usr/share`) and instead added a second, icon-less entry. Replaced both it and `arcalium-heroic.desktop` with a single `/etc/skel/.local/share/applications/` override, since `XDG_DATA_HOME` does outrank the export. |
| 2026-07-31 | Control Centre exits immediately | WebKitGTK versus the proprietary NVIDIA driver: documented as a blank window on X11 and a process that never starts on Wayland. **Confirmed on the RTX 3060** — `__NV_DISABLE_EXPLICIT_SYNC=1 arcalium-control-centre` runs, unset it and the process dies. Fixed in two places so no launch path depends on the other: the desktop entry exports the variable via `Exec=env …`, and `main.rs` sets the session-appropriate variable before WebKit initialises for terminal launches and X11. |
| 2026-07-31 | Heroic first-run Proton (superseded) | Beginners hit a missing Wine/Proton runtime (`which: no wine`) until Wine Manager is used. Initially shipped `arcaliumctl proton list` / `install-recommended` plus an `/usr/bin/arcalium-heroic` pre-launch downloader. The automatic downloader did not work as intended and was removed later the same day. `arcaliumctl` and the Control Centre actions remain as explicit install methods; the wrapper is now only a direct-launch compatibility shim. |
| 2026-07-30 | Heroic Games Launcher bundled | `com.heroicgameslauncher.hgl` added to `installer/flatpaks` and pinned next to Steam. ID matches the one already named in PRODUCT_SPEC §game-launchers; verified on Flathub (developer-verified via `heroicgameslauncher.com`, GPL-3.0) and confirmed **not** present in the Bazzite base — Bazzite only lists it in the Bazaar catalogue. Reaches machines via a rebuilt ISO only. |
| 2026-07-30 | Login screen still Bazzite wallpaper | Plasma 6.7 replaced SDDM with `plasma-login-manager` (`plasmalogin.service`); there is no `sddm` binary. Wallpaper comes from `/usr/lib/plasmalogin/defaults.conf` under `[Greeter][Wallpaper][org.kde.image][General]`, not from `kscreenlockerrc`. Fixed by shipping that file; user overrides in `/etc/plasmalogin.conf` still win. |
| 2026-07-30 | Hostname + Konsole welcome | Default hostname `arcalium` (`DEFAULT_HOSTNAME`, `/etc/hostname`, one-shot migrates stock `bazzite`). Konsole MOTD runs Arcalium `fastfetch` (ASCII mark + specs) instead of Bazzite tip markdown; `neofetch`/`fastfetch` aliases retargeted. |
| 2026-07-30 | Nightly image rebuild removed | `build.yml` no longer runs on a cron. `:dev` now moves only on push, so a tester's `bootc upgrade` cannot pull a base change nobody reviewed. Bazzite updates are taken deliberately by re-pinning the `Containerfile` digest (currently `sha256:83c6084f…`, pinned 2026-07-29) or by manual dispatch. Trade-off accepted: upstream security fixes no longer arrive on their own. |
| 2026-07-30 | **Policy: ISOs are milestone artifacts** | Iterate via container image + `bootc upgrade`; rebuild the ~6 GB live ISO only when installer behaviour or the bundled app set changes, or a tester needs a clean install. `build-disk.yml` made `workflow_dispatch`-only (its `pull_request` trigger was dead anyway — the `./`-prefixed path filters never matched) and its `anaconda-iso` matrix entry dropped, since BIB cannot depsolve this base and the run could only fail. Caveat recorded in `docs/BUILDING.md`: Flatpaks do **not** travel with `bootc upgrade`. |
| 2026-07-30 | Added `.gitattributes` (`* text=auto eol=lf`) | `installer/flatpaks` was written CRLF from the Windows workstation, which would have made `xargs` pass a ref with a trailing carriage return. Second line-ending bug in this repo, so enforced repo-wide. |
| 2026-07-30 | CI publish + Cosign sign | **success** — `ghcr.io/kaal22/arcalium-os-nvidia:dev` and `:dev-20260730`; digest `sha256:bbcea032d6369e77927d3497a3d64ade5dbb1dae6805198d2ec128c37c6ebe90`; [Actions run 30524876626](https://github.com/kaal22/arcalium-nvidia/actions/runs/30524876626) |
| 2026-07-30 | Local Cosign verify | **success** — `cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:dev` from build workstation |
| 2026-07-30 | GHCR login returned 403 | Token scope, not credentials. The `gh` CLI OAuth token is `gist, read:org, repo` — no `read:packages`. Needs a classic token with that scope. |
| 2026-07-30 | `podman login` is not sufficient for bootc | bootc reads `/etc/ostree/auth.json`, not podman's `$XDG_RUNTIME_DIR/containers/auth.json`, so a normal login looks fine and then upgrades fail or stop working after reboot. `docs/BUILDING.md` corrected — it previously documented the wrong command. |

---

## Blockers

1. ~~**`SIGNING_SECRET`:**~~ Set 2026-07-30 via `gh secret set`. Never commit `cosign.key`.
2. **Bootc Image Builder ISO (`just build-iso`):** Cannot produce an Anaconda ISO from this base ([BIB #1188](https://github.com/osbuild/bootc-image-builder/issues/1188)). Use `just build-iso-live` instead. The `installer/` payload layer is implemented.
3. **CI disk builds vs private package:** `osbuild/bootc-image-builder-action` documents no authentication or pull-secret input, so `build-disk.yml` cannot pull the private `arcalium-os-nvidia` package. Upstream interface unconfirmed — not worked around. Disk images are built locally instead.
4. **Steam / Brave / Spotify:** not in the ISO; Flathub via Control Centre. Firefox is the bundled default browser. Public release still waits on intentional GHCR visibility after notices/privacy acceptance.

Resolved: local build host — WSL2 Ubuntu 24.04 on the Windows workstation runs Podman with working loop devices, and has produced both an image and a QCOW2. See `docs/BUILDING.md`.

## Decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-29 | Repository public, GHCR package private | Free CI minutes and artifact storage; spec principle 9 wants build instructions visible, while §17.2 requires the Steam-bearing image to stay undistributed. Package visibility is irreversible once public. |
| 2026-07-29 | Disk images built locally, not in CI | Local builds run from local container storage and need no registry credentials; CI cannot pull the private package. |
| 2026-07-29 | ISOs will use titanoboa, not Bootc Image Builder | BIB's `anaconda-iso` depsolve is broken against Bazzite's Terra repos (BIB #1188), and titanoboa is what Bazzite uses for its own ISOs. Keeps Arcalium aligned with upstream instead of disabling signature checks. |
| 2026-07-29 | ISO build workflow: edit on Windows → push to GitHub → pull in WSL → build in WSL | Git is the transfer mechanism between workstation and build host. Avoids `/mnt/c` performance and permission problems, prevents the two checkouts drifting, and keeps the CI image and local ISO on the same commit. See `docs/BUILDING.md`. |
| 2026-07-29 | Kickstart `%post` registry switch runs without `--erroronfail` | The GHCR package is private, so the installer cannot reach it and the switch fails. A registry lookup must never abort a tester's install. Consequence: installed systems track `localhost/arcalium-os-nvidia:dev` and need one manual `bootc switch` before they can update — documented in `docs/BUILDING.md`. Publishing the package removes the step. |
| 2026-07-30 | Build host vs test host | Builds stay on this Windows/WSL workstation. Hardware validation runs on a separate RTX 3060 12 GB PC — never conflate the two. |
| 2026-07-30 | ISO builds run detached, on a WSL VM with explicit memory and swap | The VM died at 90% of `mksquashfs` with no error and no exit status, losing ~40 minutes. Default WSL2 gets half of host RAM and no swap. `%USERPROFILE%\.wslconfig` now sets `memory=24GB`/`swap=8GB`, and the build runs under `setsid nohup` writing to `output/iso-build.log` so it survives a disconnecting terminal. Reruns are cheap: the payload image is cached, so only the squashfs is repeated. |
| 2026-08-02 | Setup opens from Control Centre, not login | Fighting Plasma Welcome for login autostart failed repeatedly. Final approach: no Setup login autostart; Desktop + Kickoff Control Centre → `arcalium-control-centre-launch` opens Setup while incomplete; live ISO strips the CC Desktop shortcut. |
| 2026-08-02 | Firefox default; Brave/Spotify on-demand | Bundled ISO Flatpaks: Firefox, Heroic, ProtonPlus. Brave/Spotify/Steam install from Flathub via Control Centre (same pattern as Steam). |
| 2026-07-31 | Control Centre UI polish waits until all pages work | Ship one live page at a time with a functional shell. Visual polish (layout, typography, motion, empty states, copy tone) is a dedicated pass after every §9.2 page and the Setup wizard share a working codebase — not interleaved with feature wiring. |
| 2026-07-30 | Bazzite updates arrive only by re-pinning the base digest | Machines track `ghcr.io/kaal22/arcalium-os-nvidia:dev` and never rebase onto `bazzite-nvidia-open` — doing so would take them off Arcalium. The `Containerfile` pins the base by digest, so upstream moving `:stable` changes nothing until we re-pin, rebuild and publish; `bootc upgrade` then delivers Bazzite fixes and Arcalium changes as one atomic image with the previous deployment kept for rollback. Matches PRODUCT_SPEC §14 (Arcalium updates by receiving a new signed Arcalium image) and principle 7 (stay close to upstream). Accepted trade-off: upstream security and driver fixes do not flow automatically, so re-pinning needs a deliberate cadence. Procedure and digest-resolution command in `docs/BUILDING.md`. |
