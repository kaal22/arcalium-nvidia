# Documentation index

Public-prep docs for **Arcalium OS NVIDIA Edition**. GHCR remains private until you intentionally publish.

| Doc | Purpose |
|---|---|
| [PRODUCT_SPEC.md](PRODUCT_SPEC.md) | Product requirements (canonical) |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | What is done / next |
| [BUILDING.md](BUILDING.md) | Maintainer build / ISO / bootc |
| [LICENSING.md](LICENSING.md) | Licence inventory and release gates |
| [NOTICES.md](NOTICES.md) | Third-party notices |
| [PRIVACY.md](PRIVACY.md) | Privacy policy |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | What version 1 does not promise |
| [SUPPORT.md](SUPPORT.md) | How to report issues |
| [RECOVERY.md](RECOVERY.md) | Rollback and recovery |
| [INSTALL.md](INSTALL.md) | End-user install (live ISO) |
| [RELEASE_NOTES_0.1.0-alpha.1.md](RELEASE_NOTES_0.1.0-alpha.1.md) | Draft alpha release notes |
| [PHASE2_VALIDATION.md](PHASE2_VALIDATION.md) | Hardware CLI validation runbook |

## Bundled vs on-demand apps (summary)

**Bundled in the ISO:** Firefox (default browser), Heroic, ProtonPlus.

**Install from Flathub via Control Centre:** Steam, Brave, Spotify, and other catalogue apps.

## Before a public GHCR / public ISO

1. Accept notices, privacy, support, and known limitations.
2. Confirm `docs/LICENSING.md` release gates.
3. Tag + checksum + release notes.
4. Intentionally make the GHCR package public (irreversible).
5. Publish download page on **getarcalium.com** when ready.
