# Before next ISO

Target public artifact: **`Arcalium-Live-0.2.0.iso`** (SHA-256 required for the GitHub Release / getarcalium.com).

Last alpha live ISO: `Arcalium-Live-alpha-final.iso` on the Desktop  
Built from `cf0008f` (public-friendly app descriptions).

**On GHCR / bootc since that ISO (needs full ISO to land on clean installs):**
- Local AI Desktop shortcut + Space Invaders pixel icon (`2b77d67`)
- Local AI min-spec UI 16 GiB RAM / 8 GiB VRAM (`335e611`+)

Next rebuild: full `just build` then `just build-iso-live` via WSL Ubuntu (`tools/wsl-cleanup-and-rebuild.sh` if used). Copy/rename to `Arcalium-Live-0.2.0.iso` and record SHA-256.
