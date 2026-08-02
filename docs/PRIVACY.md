# Privacy

**Effective for:** private alpha / public-prep documentation  
**Product:** Arcalium OS NVIDIA Edition

## Summary

Arcalium OS does **not** phone home. There is no Arcalium account, telemetry service, or mandatory analytics in the image.

## What stays on your machine

- Setup progress and preferences under `~/.config/arcalium/`
- Control Centre local UI preferences (e.g. browser `localStorage`)
- Optional diagnostics bundles written under `~/.local/state/arcalium/` when you run diagnostics — review before sharing
- Flatpak apps, Steam, Ollama models, and game libraries you install — governed by those products’ own policies

## Third-party services

When you use Steam, Brave, Spotify, Firefox accounts, Heroic store logins, Proton VPN, Discord, or similar, those apps may collect data under **their** privacy policies. Arcalium only launches or installs them; it does not proxy or monetize that traffic.

## Updates

OS updates come from the container registry you configure (private GHCR during alpha). That uses normal HTTPS image pulls. Arcalium does not add a separate telemetry channel to updates.

## Contact

See [`docs/SUPPORT.md`](SUPPORT.md).
