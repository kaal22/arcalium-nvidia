# Before next ISO

**Public 0.2.2 live ISO:** Desktop `Arcalium-Live-0.2.2.iso` (building)  
SHA-256: *pending live cut*  
Built **2026-08-10** from promoted `:0.2.2` / `:stable` @ `sha256:650f5f1e184f5c88905a39d937e826538983265106460c17af5ec37f6e4184f0` (source tip `e8ff573`). WSL root: pull GHCR `:0.2.2` → `just build-iso-live`.

**Published tags:** `ghcr.io/kaal22/arcalium-os-nvidia:0.2.2` and `:stable` @ that digest. GHCR package is **public**.

Next rebuild only when installer / Flatpak set / brand changes demand a clean-install artifact. Prefer `wsl -d Ubuntu -u root` for ISO builds (see `docs/BUILDING.md`).
