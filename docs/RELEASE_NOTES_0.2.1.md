# Release notes — 0.2.1

**Channel:** `stable` (when promoted)  
**Edition:** NVIDIA Edition (Bazzite NVIDIA-open base)  
**Download:** [getarcalium.com](https://getarcalium.com) · GitHub Release `0.2.1`

## Highlights

- Bundle matching Flatpak NVIDIA `GL.nvidia` / GL32 runtimes on the live ISO so Heroic/Firefox are not “no OpenGL” out of the box
- Auto Flatpak NVIDIA harden after boot / driver change (`arcalium-flatpak-nvidia.service`), plus `arcaliumctl steam harden`
- Harden overrides limited to GPU devices + game library mounts (avoids Steam Flatpak D-Bus `DISPLAY` breakage)
- Setup-friendly harden: user overrides for system apps; quiet skip for apps not installed yet
- Includes earlier 0.2.0 Control Centre / Setup / Local AI min-spec guidance

## Upgrade (installed systems)

After `0.2.1` is promoted to `:stable`:

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Or switch explicitly:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:stable
sudo systemctl reboot
```

GHCR may still be **private** until the download page gate clears — auth may be required for pulls.

## Checksums

See GitHub Release asset `Arcalium-Live-0.2.1.iso.sha256` and the Desktop / website ISO copy.

## Known limitations

See [`docs/KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md). Secondary Steam libraries from older installs can still need a clean library folder; Prefer Proton / Steam Linux Runtime on the home library.
