# Licensing inventory (Phase 0 draft)

Status: **in progress** — expand before private alpha distribution.

## Arcalium OS

- Project licence for Arcalium-authored files: TBD (repository currently carries the Apache-2.0 `LICENSE` from Universal Blue’s image-template).
- Product name: Arcalium OS / Arcalium OS NVIDIA Edition.
- Package namespace (planned): `io.arcalium`.

## Upstream bases

| Component | Source | Notes |
|---|---|---|
| image-template | ublue-os/image-template | Apache-2.0 |
| Bazzite NVIDIA-open | ghcr.io/ublue-os/bazzite-nvidia-open | Follow Bazzite / Universal Blue notices |
| Fedora Atomic / bootc | Fedora Project | Upstream OS licences |

## Branding and trademarks

Arcalium OS is an independent project built on Bazzite and is **not** affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

Third-party names are used only to describe compatibility.

## Release gates (do not skip)

1. Preserve all required Bazzite / Universal Blue notices.
2. Resolve Steam client redistribution before any **public** ISO (PRODUCT_SPEC §17.2).
3. Disclose community Flatpaks (e.g. Spotify) accurately.
4. Do not ship assets without redistribution rights.
5. Cosign private key must never be committed.

## Assets still needed

- Arcalium logo licence record
- Wallpaper / lock-screen licence record
- Font licence records (when fonts are added)
- Proton-GE notices if an archive is ever bundled
