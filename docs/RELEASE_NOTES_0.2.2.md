# Release notes — 0.2.2

**Channel:** `stable`  
**Edition:** NVIDIA Edition (Bazzite NVIDIA-open base)  
**Download:** [getarcalium.com](https://getarcalium.com) · GitHub Release `0.2.2`

## Highlights

- Control Centre Overview polish (terminal-dashboard layout, Home disk space preference, clearer button spacing)
- Flatpak NVIDIA harden oneshot improved for faster idempotent boots
- Retries for bundled Flatpak + NVIDIA GL pulls during ISO payload builds
- Includes 0.2.1 Flatpak NVIDIA GL/GL32 on live media + harden path

## Image

- `ghcr.io/kaal22/arcalium-os-nvidia:0.2.2`
- `ghcr.io/kaal22/arcalium-os-nvidia:stable` (same digest)
- Digest: `sha256:650f5f1e184f5c88905a39d937e826538983265106460c17af5ec37f6e4184f0`
- Source tip: `e8ff573` (`dev-20260807-e8ff573`)

Verify:

```bash
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:0.2.2
```

## Upgrade (installed systems)

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Or switch explicitly:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:stable
sudo systemctl reboot
```

GHCR package visibility is **public**.

## ISO

- File: `Arcalium-Live-0.2.2.iso` — host on [getarcalium.com](https://getarcalium.com)
- SHA-256: published with GitHub Release asset `Arcalium-Live-0.2.2.iso.sha256` after the live cut finishes

## Known limitations

See [`docs/KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).
