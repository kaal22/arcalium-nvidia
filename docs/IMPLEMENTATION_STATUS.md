# Arcalium OS — Implementation Status

**Edition:** NVIDIA Edition  
**Channel:** private alpha / `dev`  
**Upstream template:** [ublue-os/image-template](https://github.com/ublue-os/image-template) @ `3d68ac893a31f5947dfe6210c04aee2cc469a02e`  
**Base image:** `ghcr.io/ublue-os/bazzite-nvidia-open:stable@sha256:83c6084f9713abda10b966dce3631f4c9b4430e419f06c9a76dad10bfc43cbe9` (resolved 2026-07-29)  
**Status values:** `not started` · `in progress` · `blocked` · `tested` · `complete`

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
| ISO and QCOW2 workflow | blocked | `disk_config/iso.toml` points at `ghcr.io/kaal22/arcalium-os-nvidia:dev`; CI disk builds cannot pull the private package (see blocker 2). Local `just build-iso` is the adopted path |

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
| 8 | Verify image signature | blocked |
| 9 | Build QCOW2 | blocked |
| 10 | Boot-test unbranded image | blocked |
| 11 | Build installer ISO | blocked |
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
| 2026-07-29 | Local OCI build on this Windows workstation | blocked — Podman/Docker not available here; use GitHub Actions or a bootc host |

---

## Blockers

1. **`SIGNING_SECRET`:** Paste contents of local `cosign.key` into the `kaal22/arcalium-nvidia` Actions secret `SIGNING_SECRET`. Never commit `cosign.key`.
2. **CI disk builds vs private package:** `osbuild/bootc-image-builder-action` documents no authentication or pull-secret input, so `build-disk.yml` cannot pull the private `arcalium-os-nvidia` package. Upstream interface unconfirmed — not worked around. Disk images are built locally instead.
3. **Local build host:** This Windows workstation lacks Podman and cannot run Bootc Image Builder. A Linux/bootc host is required for `just build-iso`; the first test machine will serve this role.
4. **Steam redistribution:** Blocks public ISO and public package only; private alpha testing on owned hardware may continue.

## Decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-29 | Repository public, GHCR package private | Free CI minutes and artifact storage; spec principle 9 wants build instructions visible, while §17.2 requires the Steam-bearing image to stay undistributed. Package visibility is irreversible once public. |
| 2026-07-29 | Disk images built locally, not in CI | Local `just build-iso` builds from local container storage and needs no registry credentials; CI cannot pull the private package. |
