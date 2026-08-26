# Arcalium OS — NVIDIA Edition

Gaming-first Linux OS for NVIDIA desktops. Built on [Bazzite](https://bazzite.gg/) / [Universal Blue](https://universal-blue.org/) using the official [image-template](https://github.com/ublue-os/image-template).

> Arcalium OS is an independent project built on Bazzite and is not affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

## Status

**0.2.0 / `stable` release prep.** Download site: [getarcalium.com](https://getarcalium.com). Doc index: [`docs/README.md`](docs/README.md). Spec: [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md). Checklist: [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md). Build: [`docs/BUILDING.md`](docs/BUILDING.md). Install: [`docs/INSTALL.md`](docs/INSTALL.md). Release notes: [`docs/RELEASE_NOTES_0.2.0.md`](docs/RELEASE_NOTES_0.2.0.md).

| Item | Value |
|---|---|
| Image | `arcalium-os-nvidia` |
| Base | `ghcr.io/ublue-os/bazzite-nvidia-open:stable` |
| Desktop | KDE Plasma (Wayland) |
| Public channel | `stable` / `0.2.0` (CI tip remains `dev`) |
| Default browser | Firefox (bundled); Brave/Spotify/Steam via Flathub |
| Test GPU | RTX 3060 12 GB (primary) |

## End users

1. Get the live ISO from [getarcalium.com](https://getarcalium.com) or the GitHub Release.
2. Follow [`docs/INSTALL.md`](docs/INSTALL.md).
3. After install, track updates with:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:stable
sudo systemctl reboot
```

## Maintainers

1. Set GitHub Actions secret `SIGNING_SECRET` from your local `cosign.key` (never commit the key).
2. Confirm `REPO_ORGANIZATION` in `image-template.env`.
3. Push to `main` → **Build container image** publishes `ghcr.io/<owner>/arcalium-os-nvidia:dev`.
4. After hardware validation, run **Promote stable** (`promote-stable.yml`) to tag `0.2.0` and `stable`.
5. Build disk images locally — see [`docs/BUILDING.md`](docs/BUILDING.md).

```bash
cd /home/kaal/arcalium-nvidia && git pull && just build && just build-iso-live
```

## Verify signatures

```bash
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:stable
```

Licensing: [`docs/LICENSING.md`](docs/LICENSING.md). Notices: [`docs/NOTICES.md`](docs/NOTICES.md). Privacy: [`docs/PRIVACY.md`](docs/PRIVACY.md). Support: [`docs/SUPPORT.md`](docs/SUPPORT.md).
