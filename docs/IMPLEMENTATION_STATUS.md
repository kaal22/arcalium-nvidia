# Arcalium OS — Implementation Status

**Edition:** NVIDIA Edition  
**Channel:** private alpha / `dev`  
**Upstream template:** [ublue-os/image-template](https://github.com/ublue-os/image-template) @ `3d68ac893a31f5947dfe6210c04aee2cc469a02e`  
**Base image:** `ghcr.io/ublue-os/bazzite-nvidia-open:stable@sha256:83c6084f9713abda10b966dce3631f4c9b4430e419f06c9a76dad10bfc43cbe9` (resolved 2026-07-29)  
**Status values:** `not started` · `in progress` · `blocked` · `tested` · `complete`

---

## Where we left off (2026-07-29 evening)

Phase 0 scaffolding is done. Local WSL builds work. The ISO installs and the installed system boots in VMware (UEFI).

**Last successful artifacts (on the Windows Desktop and in WSL `~/arcalium-nvidia/output/`):**

| Artifact | Location | Notes |
|---|---|---|
| Live ISO | `C:\Users\Kaal\Desktop\Arcalium-Live.iso` (5.8 GB) | zstd squashfs, Anaconda profile, Firefox, progress window, Steam suppressed |
| QCOW2 | WSL `~/arcalium-nvidia/output/qcow2/disk.qcow2` (~5.8 GB) | Not yet boot-tested |
| OCI image | WSL `localhost/arcalium-os-nvidia:dev` | 13.2 GB |
| Payload image | WSL `localhost/arcalium-os-nvidia-payload:dev` | Live/installer layer |

**Proven today**

- `just build` and `just build-qcow2` in WSL Ubuntu
- Titanoboa live ISO path (`just build-iso-live`) — not Bootc Image Builder
- UEFI boot of the live ISO in VMware Workstation
- Live desktop comes up; welcome dialog appears
- **Full chain: ISO → Anaconda install → boot to first-run setup**
- WSL Ubuntu was recovered after a bad `mv` (not reinstalled)

**Not finished — next session**

1. Repoint the installed VM off the `localhost` ref once the GHCR package is published. `bootc status` is confirmed showing `localhost/arcalium-os-nvidia:dev`, so `bootc upgrade` cannot work until then (see `docs/BUILDING.md`).
2. Set GitHub Actions secret `SIGNING_SECRET` from local `cosign.key`, then get CI to publish the private `ghcr.io/kaal22/arcalium-os-nvidia:dev`.
3. Hardware install on RTX 3090 / RTX 2060 — the VM install now works, so this is unblocked apart from hardware access.
4. Retest in a VM with a preallocated disk and a Defender exclusion for the VM folder, to confirm the deploy step is disk-bound.
5. Branding replaces the Bazzite first-run wizard and logo — but only after the spec's base+ISO gate, which is now met.
6. Do **not** start Control Centre until the licensing and signing items above are settled (spec gate).

**Resume commands**

```powershell
wsl -d Ubuntu -u root
cd /home/kaal/arcalium-nvidia && git pull
just build && just build-iso-live
cp output/Arcalium-Live.iso /mnt/c/Users/Kaal/Desktop/
```

Repo: https://github.com/kaal22/arcalium-nvidia — HEAD includes the Firefox installer fix (`6399708` and parents).

---

## Phase 0 — Repository and research

| Requirement | Status | Notes |
|---|---|---|
| Repository created from current `ublue-os/image-template` | complete | Copied template tree; history retained from template commit above |
| `docs/PRODUCT_SPEC.md` | complete | Copied from `Arcalium_OS_NVIDIA_Product_Spec.md` |
| `docs/IMPLEMENTATION_STATUS.md` | complete | This file |
| Licence inventory | in progress | Apache-2.0 template LICENSE retained; Arcalium notices TBD in `docs/LICENSING.md` |
| Confirmed image tag `bazzite-nvidia-open:stable` | complete | GHCR tags include `stable`; digest pinned in Containerfile |
| Confirmed build workflow | complete | `.github/workflows/build.yml` + `build-disk.yml` present |
| Cosign setup (public key committed, private key secret) | in progress | `cosign.pub` generated; `cosign.key` local only — must set GitHub secret `SIGNING_SECRET` before publish |
| Private GHCR `dev` image | in progress | Repository pushed to `kaal22/arcalium-nvidia`; Actions still needs `SIGNING_SECRET`. Package stays private per spec §17.2 |
| Image signature verifies | blocked | Depends on first successful signed publish |
| Test machine switch / QCOW2 boot | blocked | Depends on published image; bootstrap path is rebase from stock Bazzite, see `docs/BUILDING.md` |

## Phase 1 — Minimal Arcalium NVIDIA image

| Requirement | Status | Notes |
|---|---|---|
| NVIDIA-open Bazzite base | complete | Containerfile uses verified base |
| Arcalium image metadata | complete | `image-template.env` + `/etc/arcalium/image-info.json` |
| Basic branding | not started | Wallpaper / logos deferred until assets exist |
| Arcalium wallpaper | not started | |
| Control Centre placeholder | not started | Spec forbids Control Centre until base+ISO proven |
| First-boot placeholder | not started | Same gate |
| QCOW2 workflow | tested | Built locally in WSL2, 5.8 GB; boot test still outstanding |
| ISO workflow | tested | Live ISO boots in VMware UEFI; Install needs retest after Firefox was added to the payload |
| Bootc Image Builder ISO (`just build-iso`) | blocked | Upstream BIB #1188 — do not use |

## Phase 2 — Hardware validation

| Requirement | Status | Notes |
|---|---|---|
| `arcaliumctl system summary` | not started | |
| `arcaliumctl gpu status` | not started | |
| NVIDIA / Vulkan / Wayland validation | not started | |
| Diagnostics JSON schemas | not started | |

## Phase 3 — Setup wizard

| Requirement | Status | Notes |
|---|---|---|
| First-run service + resume state | not started | Gated until Phase 0–1 proven |
| Wizard pages (hardware → completion) | not started | |

## Phase 4 — Application provisioning

| Requirement | Status | Notes |
|---|---|---|
| Declarative app catalogue | not started | Flatpak IDs must be re-validated on Flathub before commit |
| Spotify / ProtonPlus / optional launchers | not started | |

## Phase 5 — Proton-GE

| Requirement | Status | Notes |
|---|---|---|
| Recommended-version manifest + install action | not started | |

## Phase 6 — Storage and VPN

| Requirement | Status | Notes |
|---|---|---|
| Drive scan / filesystem warnings | not started | |
| ProtonVPN import flow | not started | |

## Phase 7 — Control Centre completion

| Requirement | Status | Notes |
|---|---|---|
| All version 1 pages | not started | |

## Phase 8 — Private alpha

| Requirement | Status | Notes |
|---|---|---|
| `0.1.0-alpha.1` signed image + ISO + QCOW2 | not started | |
| Hardware matrix (RTX 3090 + 2× RTX 2060) | not started | |

## Phase 9 — Public-release preparation

| Requirement | Status | Notes |
|---|---|---|
| Steam licensing gate | blocked | Public ISO blocked until Valve redistribution review |
| Trademark / notices / privacy | not started | |

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
| 6 | Configure Cosign (no private key in git) | in progress — pubkey ready; secret upload pending |
| 7 | Build/publish private `dev` image to GHCR | in progress — repository pushed; signing secret pending |
| 8 | Verify image signature | blocked — needs a CI-published image, which needs `SIGNING_SECRET` |
| 9 | Build QCOW2 | complete — `output/qcow2/disk.qcow2`, built locally under WSL2 |
| 10 | Boot-test unbranded image | complete (VM) — installed from the live ISO and booted to first-run setup in VMware |
| 11 | Build installer ISO | complete — `output/Arcalium-Live.iso` via titanoboa (`just build-iso-live`) |
| 12–13 | Install on RTX 3090 / RTX 2060 | blocked — hardware |
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
| 2026-07-29 | Deploy step is indistinguishable from a hang | Treated as a defect, not impatience. Added `arcalium-install-progress.sh` (bytes written, elapsed, throughput) and routed both launch paths through `arcalium-install.sh`. Welcome dialog now states 15–40 minutes up front. |
| 2026-07-29 | titanoboa builds a **gzip** squashfs, not zstd | Upstream `build_iso.sh` puts `-comp zstd -Xcompression-level 19` after `-e`, and `mksquashfs` reads everything after `-e` as exclude paths. Log line: `Exportable Squashfs 4.0 filesystem, gzip compressed`. `build-iso-live` now patches the clone and asserts the fix. Worth an upstream PR. |
| 2026-07-29 | Rebuild with zstd fix | **success** — `Exportable Squashfs 4.0 filesystem, zstd compressed`; squashfs 5.30 GiB (was 5.71), ISO 5.8 GB (was 6.2) |
| 2026-07-29 | **Full install + first boot in VMware** | **success** — installed from `Arcalium-Live.iso` (8 vCPU, 16 GB, 40 GB NVMe-controller disk, UEFI) and booted to the first-run setup wizard. First end-to-end proof of the ISO → install → boot chain. |
| 2026-07-29 | Deploy step throughput measured | `vmstat 5` during deploy: ~7 MB/s, `wa` 7–15%, CPU 81–85% idle, `b` 1–2. **Disk-bound, not CPU-bound** — ostree's small-file, checksum-and-sync writes through VMware's virtual disk. More vCPUs will not help. |
| 2026-07-29 | Progress window reported delta, not total | Bytes since the window opened, so attaching mid-install read as a stall. Now reports total on target with the rate labelled an average. |
| 2026-07-29 | Anaconda finish screen offers no restart | Live installer returns to the desktop and tells the user to exit it. Acceptable for alpha; an end user expects an explicit "Restart now". Polish item. |
| 2026-07-29 | `bootc status` on the installed VM | `localhost/arcalium-os-nvidia:dev` as predicted — the ISO's embedded image, so `bootc upgrade` is inert until the GHCR package is published and the system is repointed |
| 2026-07-29 | First-run setup completed; Steam installed on the installed system | **correct behaviour** — Steam belongs on the installed system and was only suppressed in the live installer session |
| 2026-07-29 | Installed system shows **Bazzite** first-run wizard and logo | Expected at this phase — no branding work has been done, and the spec gates Control Centre and branding behind proving base + ISO. Records the branding surfaces that need replacing: first-run wizard, logo, `os-release`, Plymouth. |

---

## Blockers

1. **`SIGNING_SECRET`:** Paste contents of local `cosign.key` into the `kaal22/arcalium-nvidia` Actions secret `SIGNING_SECRET`. Never commit `cosign.key`.
2. **Bootc Image Builder ISO (`just build-iso`):** Cannot produce an Anaconda ISO from this base ([BIB #1188](https://github.com/osbuild/bootc-image-builder/issues/1188)). Use `just build-iso-live` instead. The `installer/` payload layer is implemented.
3. **CI disk builds vs private package:** `osbuild/bootc-image-builder-action` documents no authentication or pull-secret input, so `build-disk.yml` cannot pull the private `arcalium-os-nvidia` package. Upstream interface unconfirmed — not worked around. Disk images are built locally instead.
4. **Steam redistribution:** Blocks public ISO and public package only; private alpha testing on owned hardware may continue.

Resolved: local build host — WSL2 Ubuntu 24.04 on the Windows workstation runs Podman with working loop devices, and has produced both an image and a QCOW2. See `docs/BUILDING.md`.

## Decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-29 | Repository public, GHCR package private | Free CI minutes and artifact storage; spec principle 9 wants build instructions visible, while §17.2 requires the Steam-bearing image to stay undistributed. Package visibility is irreversible once public. |
| 2026-07-29 | Disk images built locally, not in CI | Local builds run from local container storage and need no registry credentials; CI cannot pull the private package. |
| 2026-07-29 | ISOs will use titanoboa, not Bootc Image Builder | BIB's `anaconda-iso` depsolve is broken against Bazzite's Terra repos (BIB #1188), and titanoboa is what Bazzite uses for its own ISOs. Keeps Arcalium aligned with upstream instead of disabling signature checks. |
| 2026-07-29 | ISO build workflow: edit on Windows → push to GitHub → pull in WSL → build in WSL | Git is the transfer mechanism between workstation and build host. Avoids `/mnt/c` performance and permission problems, prevents the two checkouts drifting, and keeps the CI image and local ISO on the same commit. See `docs/BUILDING.md`. |
| 2026-07-29 | Kickstart `%post` registry switch runs without `--erroronfail` | The GHCR package is private, so the installer cannot reach it and the switch fails. A registry lookup must never abort a tester's install. Consequence: installed systems track `localhost/arcalium-os-nvidia:dev` and need one manual `bootc switch` before they can update — documented in `docs/BUILDING.md`. Publishing the package removes the step. |
