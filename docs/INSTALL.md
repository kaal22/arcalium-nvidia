# Install Arcalium OS (NVIDIA Edition)

Version **0.2.0** — read [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) first. Downloads: [getarcalium.com](https://getarcalium.com).

## What you need

- A PC with a supported NVIDIA GPU (primary validation: RTX 3060 12 GB)
- Enough RAM for gaming (Local AI wants 16 GiB+ if you use it)
- USB stick or Ventoy
- Current live ISO (`Arcalium-Live-0.2.0.iso` from the GitHub Release / download site)

## Boot the live ISO

1. Write the ISO to USB (Rufus, balenaEtcher, or Ventoy).
2. On Ventoy, prefer **GRUB2** mode.
3. On NVIDIA hardware, if the default live entry black-screens, choose **Basic Graphics Mode** (`nomodeset`). The **installed** system uses nvidia-open; the live session often uses Nouveau.

## Install

1. From the live desktop, open **Install Arcalium OS**.
2. Complete Anaconda (disk, user, timezone). Expect a long, quiet deploy step.
3. When finished, reboot into the installed system (remove the USB when asked).

## First boot

1. Plasma Welcome may run (sometimes before login, then a restart). That is separate from Arcalium Setup.
2. After login, open **Arcalium Control Centre** from the Desktop or application menu.
3. Until Setup is finished, that launcher opens the **Setup** wizard. Complete or skip optional steps as you like.
4. **Firefox** is the default browser. Install **Steam**, **Brave**, or **Spotify** later from Control Centre → Applications (Flathub) if you want them — they are not preinstalled.

## After install: updates

Point the system at the public **stable** channel (required if the ISO still tracked a localhost image, or while GHCR was private at install time):

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:stable
sudo systemctl reboot
```

If the GHCR package is still private during your install window, authenticate first (see [BUILDING.md](BUILDING.md) — ostree/`/etc/ostree/auth.json`). Once the package is public, no login is needed for pulls.

Later upgrades:

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Rollback: [RECOVERY.md](RECOVERY.md).

## Help

[SUPPORT.md](SUPPORT.md) · [NOTICES.md](NOTICES.md) · [PRIVACY.md](PRIVACY.md) · [RELEASE_NOTES_0.2.0.md](RELEASE_NOTES_0.2.0.md)
