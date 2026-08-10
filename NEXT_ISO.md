# Before next ISO

**Public 0.2.2 live ISO:** Desktop `Arcalium-Live-0.2.2.iso` (~7.2 GB)  
SHA-256: `92cf880003359ad13dab7c6e5f120e7c01e1453c0e3ebd468ae05bfe1d2ce54c`  
Built **2026-08-10** from promoted `:0.2.2` / `:stable` @ `sha256:650f5f1e184f5c88905a39d937e826538983265106460c17af5ec37f6e4184f0` (source tip `e8ff573`). WSL root: pull GHCR `:0.2.2` → `just build-iso-live … stable` (`TARGET_IMAGE_REF=:stable`).

**Published tags:** `ghcr.io/kaal22/arcalium-os-nvidia:0.2.2` and `:stable` @ that digest. GHCR package is **public**.

Next rebuild only when installer / Flatpak set / brand changes demand a clean-install artifact. Prefer `wsl -d Ubuntu -u root` for ISO builds (see `docs/BUILDING.md`).
