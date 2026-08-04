# 0.2.0 release-candidate smoke (RTX 3060)

Run after CI published the candidate `:dev` image and before promoting to `0.2.0` / `:stable`.

## Automated gates (maintainer / CI)

| Check | Status |
|---|---|
| CI Build container image on candidate SHA | Required green before promote |
| `build.sh` Steam RPM / `steam.desktop` absence asserts | Enforced in image build |
| Local AI min-spec constants / UI + `ai status` hardware fields | Shipped on candidate |

## On the 3060 (bootc)

```bash
sudo bootc upgrade && sudo systemctl reboot
# confirm deployment
bootc status
```

## Owner checklist

| Check | Pass? |
|---|---|
| Setup / Control Centre **Local AI** shows min 16 GiB RAM · 8 GiB VRAM and This PC measurement | |
| Local AI soft-warns when below floor; Skip still works | |
| Partition Manager opens from Storage / Setup disk utility | |
| `arcaliumctl steam status` — Steam RPM absent; Flathub install path still works | |
| Assistant agent: `updates_status` / `updates_check` tools behave (mutating needs `yes` + sudo terminal) | |
| Catalogue cards show friendly descriptions (not Flatpak IDs as primary copy) | |

## Clean install (after ISO cut)

Boot `Arcalium-Live-0.2.0.iso` → install → first Setup. Until GHCR is public, a post-install `bootc switch` to `ghcr.io/kaal22/arcalium-os-nvidia:stable` (with registry auth if still private) may still be required — see [`INSTALL.md`](INSTALL.md).
