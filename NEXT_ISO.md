# Before next ISO

**Public 0.2.0 live ISO:** Desktop `Arcalium-Live-0.2.0.iso` (~7.2 GB)  
SHA-256: `d5bf497b7398ae69a098b7f07cd7ab146c933296e500ff2dd4877ecd3e16258a`  
Built **2026-08-05** from `origin/main` @ `c5f816f` (Flatpak NVIDIA GL on ISO + minimal harden overrides). WSL root: pull CI `:dev` (`6867947ad624`) → `just build-iso-live`.

**Published tags:** `ghcr.io/kaal22/arcalium-os-nvidia:0.2.0` and `:stable` may still point at the earlier promote digest until you re-promote; `:dev` matches this ISO’s base image. Package still private until getarcalium.com download page.

Next rebuild only when installer / Flatpak set / brand changes demand a clean-install artifact. Prefer `wsl -d Ubuntu -u root` for ISO builds (see `docs/BUILDING.md`).
