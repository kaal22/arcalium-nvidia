# Recovery and rollback

Arcalium uses `bootc` / rpm-ostree style deployments. A failed update should leave the previous deployment bootable.

## Roll back from Control Centre

**Updates and Recovery** → follow the on-screen rollback / reboot actions (opens a terminal with `sudo bootc` so you can authenticate and confirm).

## Roll back from a terminal

```bash
sudo bootc status
sudo bootc rollback
sudo systemctl reboot
```

After reboot, confirm you are on the previous image, then update forward again when ready:

```bash
sudo bootc upgrade
sudo systemctl reboot
```

## Important

- Rollback restores a previous **OS image**. It does not restore deleted documents, game saves, or Flatpak user data you removed yourself.
- If the system will not boot, use the previous GRUB/bootc deployment entry if shown, or reinstall from the live ISO and keep `/home` if your partitioning allows it.
- During private alpha the GHCR package may be private: `bootc upgrade` needs `podman login ghcr.io` (see [`docs/BUILDING.md`](BUILDING.md)).

## Fresh install

Boot `Arcalium-Live-*.iso` → Install Arcalium OS. Prefer **Basic Graphics Mode** on NVIDIA for the live session if the default entry black-screens.
