# Before next ISO

Do a **full** `just build` (image), then `just build-iso-live`.

ISO-only is not enough. Unshipped image changes since `Arcalium-Live-alpha-final.iso`:

1. **Disk utility** — `kde-partitionmanager` *(in GHCR `fa4162f` — already on bootc)*
2. **Ollama install** — brew non-zero OK when binary present *(in GHCR `fa4162f`)*
3. **App catalogue descriptions** — human blurbs for OBS etc.; no Flatpak IDs as card copy *(local, not pushed yet)*

Desktop target: `Arcalium-Live-alpha-final.iso` (via WSL Ubuntu helpers under `tools/`).
