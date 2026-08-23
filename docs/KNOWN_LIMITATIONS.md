# Known limitations

For Arcalium OS NVIDIA Edition **0.2.0**:

- Not every Windows game works on Linux.
- Some anti-cheat systems block Linux or Proton.
- Xbox PC Game Pass titles generally cannot be installed locally the way they are on Windows; cloud gaming may be an alternative.
- NVIDIA Steam Gaming Mode / console session is **not** the version 1 target.
- HDR and VRR depend on GPU, display, cable, and game.
- Proton-GE is not automatically better for every game.
- VPN use can increase latency.
- NTFS game libraries are unsupported for the intended Bazzite-style gaming workflow.
- `bootc` rollback restores a previous OS deployment; it does **not** undelete personal files.
- Community Flatpaks (e.g. Spotify on Flathub) may not be supported by the original vendor.
- Brave and Spotify are optional Flathub installs — they are not preinstalled.
- Steam is optional Flathub install — not shipped in the image.
- Fresh ISOs bundle matching Flatpak `GL.nvidia-*` / GL32 runtimes next to Firefox/Heroic. After a driver re-pin, installed machines rely on `arcalium-flatpak-nvidia.service` (or `arcaliumctl steam harden`) to pull the new GL tag — Flatpaks do not travel with `bootc upgrade`. Without matching GL + device overrides: Heroic “no OpenGL” / Steam ~0% GPU util / soft browser video. Native (non-Flatpak) apps use the host driver and do not need this.
- Local AI needs about **16 GiB system RAM** and **8 GiB GPU VRAM**; Setup and Control Centre warn when the PC is below that.
- NVIDIA drivers are **nvidia-open** from the OS image; use Control Centre → GPU → Drivers (or Updates) to check/apply an Arcalium image update — do not install GeForce / `.run` drivers on top of bootc.
- Bazzite Portal (yafti), Bazzite Documentation, Discourse, Bazzite Announcements, Bazzite Updater (`bazzite-updater` RPM / old `system-update.desktop`), and Bold Brew / Bazzite CLI menu entries are removed from Arcalium images — use Control Centre → Updates instead. Existing user homes are scrubbed on login by `arcalium-cleanup-bazzite.service` (`~/.config/autostart` + `~/.local/share/applications`).
- Arcalium is an independent Bazzite-derived project, not an official Valve, NVIDIA, or Bazzite product.

See also [`docs/PRODUCT_SPEC.md`](PRODUCT_SPEC.md) §25.
