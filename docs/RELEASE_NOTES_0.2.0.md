# Release notes — 0.2.0

**Channel:** `stable` (first public stable)  
**Edition:** NVIDIA Edition (Bazzite NVIDIA-open base)  
**Download:** [getarcalium.com](https://getarcalium.com) · GitHub Release `0.2.0`

## Highlights

- Immutable gaming desktop on nvidia-open with KDE Plasma (Wayland)
- Arcalium Control Centre + first-run Setup
- Steam, Brave, and Spotify install from Flathub via Control Centre (not preinstalled)
- Firefox bundled as default browser (MPL-2.0); Heroic + ProtonPlus bundled
- Public-friendly app catalogue descriptions
- Storage **Open disk utility** → KDE Partition Manager
- Optional Local AI assistant (Ollama) with **minimum hardware guidance: 16 GiB RAM and 8 GiB GPU VRAM** (soft warning, not a hard block)
- After Local AI model pull: Desktop shortcut + Space Invaders-style pixel icon (`arcalium-assistant`)
- Live installer ISO for clean installs

## Upgrade (installed systems)

Track the public stable channel:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:stable
sudo systemctl reboot
```

Later:

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Verify the image signature:

```bash
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:stable
```

## Known limitations

See [`docs/KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

## Licensing / notices

See [`docs/LICENSING.md`](LICENSING.md) and [`docs/NOTICES.md`](NOTICES.md).

## Checksums

Published with GitHub Release `0.2.0`:

- Container image digest (Arcalium `0.2.0` / `stable`)
- Upstream base digest (pinned in `Containerfile`)
- SHA-256 of `Arcalium-Live-0.2.0.iso`
