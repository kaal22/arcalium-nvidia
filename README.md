# Arcalium OS — NVIDIA Edition

Gaming-first Linux OS for NVIDIA desktops. Built on [Bazzite](https://bazzite.gg/) / [Universal Blue](https://universal-blue.org/) using the official [image-template](https://github.com/ublue-os/image-template).

> Arcalium OS is an independent project built on Bazzite and is not affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

## Status

**Private alpha / Phase 0.** Spec: [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md). Checklist: [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md). Build guide: [`docs/BUILDING.md`](docs/BUILDING.md).

| Item | Value |
|---|---|
| Image | `arcalium-os-nvidia` |
| Base | `ghcr.io/ublue-os/bazzite-nvidia-open:stable` |
| Desktop | KDE Plasma (Wayland) |
| Channel | `dev` |
| Test GPUs | RTX 3090, RTX 2060 |

## Quick start (maintainers)

1. Set GitHub Actions secret `SIGNING_SECRET` from your local `cosign.key` (never commit the key).
2. Confirm `REPO_ORGANIZATION` in `image-template.env`.
3. Push to `main` → **Build container image** publishes `ghcr.io/<owner>/arcalium-os-nvidia:dev`.
4. Run **Build disk images** for QCOW2 + installer ISO.
5. Hardware-test before any Control Centre work.

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:dev
```

## Verify signatures

```bash
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:dev
```

## What this is not

- Not a theme pack or post-install script collection
- Not a full Bazzite fork
- Not Steam Gaming Mode / console session (v1)
- Not a public release until licensing gates pass

## Repository layout

Inherited from Universal Blue `image-template`, plus Arcalium docs and identity files under `system_files/` and `docs/`.
