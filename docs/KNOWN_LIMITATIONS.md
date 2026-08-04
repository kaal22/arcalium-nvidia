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
- Flatpak Steam needs NVIDIA GL Flatpak runtimes + device/mount overrides (`arcaliumctl steam harden`); native bundled Steam did not.
- Local AI needs about **16 GiB system RAM** and **8 GiB GPU VRAM**; Setup and Control Centre warn when the PC is below that.
- NVIDIA drivers are **nvidia-open** from the OS image; use Control Centre → GPU → Drivers (or Updates) to check/apply an Arcalium image update — do not install GeForce / `.run` drivers on top of bootc.
- Bazzite Portal, Bazzite Documentation, and the Bazzite “System Update” (`ujust update`) menu entries are removed from Arcalium images — use Control Centre → Updates instead.
- Arcalium is an independent Bazzite-derived project, not an official Valve, NVIDIA, or Bazzite product.

See also [`docs/PRODUCT_SPEC.md`](PRODUCT_SPEC.md) §25.
