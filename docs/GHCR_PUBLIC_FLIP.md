# Flip GHCR public (after getarcalium.com download)

Do **not** run this until:

1. [getarcalium.com](https://getarcalium.com) hosts `Arcalium-Live-0.2.0.iso` + SHA-256 + install link (not a placeholder landing page).
2. GitHub Release `0.2.0` notes match the published checksum.
3. Notices / privacy / support remain accepted (`docs/LICENSING.md`).

## Steps

1. GitHub → Packages → `arcalium-os-nvidia` → Package settings → change visibility to **Public** (irreversible).
2. Confirm anonymous pull:

```bash
podman pull ghcr.io/kaal22/arcalium-os-nvidia:stable
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:stable
```

3. Update status docs: Phase 9 public GHCR → complete; remove "auth required" as the happy path in `docs/INSTALL.md` / `docs/BUILDING.md` (kickstart `%post` can then reach GHCR).
4. Point getarcalium.com at the Release and checksums.
