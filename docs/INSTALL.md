# Install Arcalium OS (NVIDIA Edition)

Private alpha — expect rough edges. Read [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) first.

## What you need

- A PC with a supported NVIDIA GPU (primary test hardware: RTX 3060 12 GB)
- 8 GB+ RAM recommended; more for ISO builds is irrelevant to install
- USB stick or Ventoy
- Current live ISO (e.g. `Arcalium-Live-alpha-final.iso`)

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

The ISO may leave the system tracking a local image reference. To follow the published `dev` channel (private GHCR during alpha):

```bash
# Token needs read:packages for the private package
podman login ghcr.io -u YOUR_GITHUB_USER
# Prefer the bootc/ostree auth path documented in BUILDING.md if upgrades fail after reboot
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:dev
sudo systemctl reboot
```

Later:

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Full detail: [BUILDING.md](BUILDING.md). Rollback: [RECOVERY.md](RECOVERY.md).

## Help

[SUPPORT.md](SUPPORT.md) · [NOTICES.md](NOTICES.md) · [PRIVACY.md](PRIVACY.md)
