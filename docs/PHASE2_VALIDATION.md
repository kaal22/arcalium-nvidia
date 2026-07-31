# Phase 2 validation on the RTX 3060 test PC

No ISO rebuild for this milestone. After CI publishes the image that includes
`arcaliumctl`, upgrade the existing install and run the checks below.

**Status (2026-07-31):** CLI section **passed** on the RTX 3060 upgrade install
(`system summary`, `gpu status`, `gpu validate`, `vulkan test` — all `--json`).
Steam/Heroic game path **passed** (owner-confirmed). Phase 2 complete on this machine.

## 1. Upgrade

```bash
sudo bootc upgrade
sudo systemctl reboot
```

Confirm the new deployment:

```bash
bootc status
which arcaliumctl
arcaliumctl --help
```

## 2. Diagnostics (paste JSON back)

Run from a **graphical Konsole session** on the desktop (so Wayland env vars are set):

```bash
arcaliumctl system summary --json
arcaliumctl gpu status --json
arcaliumctl gpu validate --json
arcaliumctl vulkan test --json
```

Human-readable variants (optional):

```bash
arcaliumctl system summary
arcaliumctl gpu validate
arcaliumctl vulkan test
```

### What “good” looks like on the 3060

| Check | Expect |
|---|---|
| `gpu validate` → `overall` | `ready` (or `warning` only for non-critical items) |
| `gpu-present` | `ready` — name mentions RTX 3060 |
| `nvidia-modules` | `ready` — `nvidia` / `nvidia_drm` listed |
| `nvidia-smi` | `ready` |
| `vulkan-nvidia` | `ready` — NVIDIA device in list |
| `wayland` | `ready` |
| `software-render` | `ready` (not llvmpipe) |

Error codes (PRODUCT_SPEC §22) appear under each failed check and in `errorCodes`:

- `ARC-GPU-001` NVIDIA GPU not detected
- `ARC-GPU-002` NVIDIA module not loaded / nvidia-smi failed
- `ARC-GPU-003` Software rendering
- `ARC-GPU-004` nouveau instead of nvidia
- `ARC-VLK-001` Vulkan unavailable
- `ARC-VLK-002` Vulkan has no NVIDIA device

Schemas for the JSON payloads live at `/usr/share/arcalium/schemas/`.

## 3. Game path (manual)

Not automated in Phase 2 — report pass/fail in chat.

### Steam

1. Launch Steam from the application menu or taskbar.
2. Start one Proton-compatible Windows title you already own (or a free title).
3. Note: launches to desktop, plays, crashes, or black screen.

### Heroic

Heroic is in the batched ISO set; on this upgrade-only machine install once if needed:

```bash
flatpak install --system flathub com.heroicgameslauncher.hgl
```

Then open Heroic, sign in to Epic or GOG if you use them, and launch one library title (or confirm the library UI loads).

## 4. What to paste back

1. Full JSON from the four `arcaliumctl … --json` commands (or attach files).
2. Steam game name + result.
3. Heroic result (or “not installed / skipped”).
4. Anything unexpected (`systemctl --failed`, display blanking, etc.).

Results go into `docs/IMPLEMENTATION_STATUS.md` verification log.
