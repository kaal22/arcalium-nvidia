# Before next ISO

Do a **full** `just build` (image), then `just build-iso-live`.

ISO-only is not enough. Unshipped image changes since `Arcalium-Live-alpha-final.iso`:

1. **Disk utility** — install `kde-partitionmanager`; stop falling back to System Settings
2. **Ollama install** — treat brew non-zero exit as OK when the `ollama` binary is present

Desktop target: `Arcalium-Live-alpha-final.iso` (via WSL Ubuntu helpers under `tools/`).
