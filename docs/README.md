# Documentation index

Docs for **Arcalium OS NVIDIA Edition 0.2.0**. Public channel: `stable`. GHCR package stays private until getarcalium.com ships a real download page.

| Doc | Purpose |
|---|---|
| [PRODUCT_SPEC.md](PRODUCT_SPEC.md) | Product requirements (canonical) |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | What is done / next |
| [BUILDING.md](BUILDING.md) | Maintainer build / ISO / bootc |
| [LICENSING.md](LICENSING.md) | Licence inventory and release gates |
| [NOTICES.md](NOTICES.md) | Third-party notices |
| [PRIVACY.md](PRIVACY.md) | Privacy policy |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | What 0.2.0 does not promise |
| [SUPPORT.md](SUPPORT.md) | How to report issues |
| [RECOVERY.md](RECOVERY.md) | Rollback and recovery |
| [INSTALL.md](INSTALL.md) | End-user install (live ISO) |
| [RELEASE_NOTES_0.2.0.md](RELEASE_NOTES_0.2.0.md) | 0.2.0 release notes |
| [RC_SMOKE_0.2.0.md](RC_SMOKE_0.2.0.md) | Pre-promote smoke checklist |
| [RELEASE_NOTES_0.1.0-alpha.1.md](RELEASE_NOTES_0.1.0-alpha.1.md) | Historical alpha draft |
| [PHASE2_VALIDATION.md](PHASE2_VALIDATION.md) | Hardware CLI validation runbook |

## Bundled vs on-demand apps (summary)

**Bundled in the ISO:** Firefox (default browser), Heroic, ProtonPlus.

**Install from Flathub via Control Centre:** Steam, Brave, Spotify, and other catalogue apps.

## Before flipping GHCR public

1. Notices, privacy, support, and known limitations accepted (done for 0.2.0).
2. Tag + Cosign + release notes + ISO checksums (`0.2.0` / `stable`).
3. Publish download page on **getarcalium.com** (ISO + SHA-256 + install link).
4. Intentionally make the GHCR package public (irreversible).
