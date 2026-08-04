# Release notes — 0.1.0-alpha.1 (historical draft)

Superseded by [`RELEASE_NOTES_0.2.0.md`](RELEASE_NOTES_0.2.0.md) for the first public stable.

**Channel:** private alpha / `dev`  
**Edition:** NVIDIA Edition (Bazzite NVIDIA-open base)

## Highlights

- Immutable gaming desktop on nvidia-open with KDE Plasma (Wayland)
- Arcalium Control Centre + first-run Setup (Desktop/Kickoff; no login Setup popup)
- Steam, Brave, and Spotify install from Flathub via Control Centre (not preinstalled)
- Firefox bundled as default browser (MPL-2.0)
- Heroic + ProtonPlus bundled; Proton-GE install via Control Centre
- Public-friendly app catalogue descriptions in Control Centre
- Storage **Open disk utility** launches KDE Partition Manager (in-image)
- Optional Local AI assistant (Ollama) from Control Centre / Setup — after model pull, a Desktop shortcut with a Space Invaders-style pixel icon
- Live installer ISO (`just build-iso-live`) with Install-focused live desktop

## Known limitations

See [`docs/KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

## Licensing / notices

See [`docs/LICENSING.md`](LICENSING.md) and [`docs/NOTICES.md`](NOTICES.md).

## Upgrade

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Private GHCR needs registry credentials for ostree pulls (see [`docs/BUILDING.md`](BUILDING.md) — `~/.config/ostree/auth.json` / `podman login`). Package remains **private** for alpha.

## Checksums

Publish SHA-256 of the signed image digest and ISO alongside the GitHub Release when tagging `0.1.0-alpha.1`.
