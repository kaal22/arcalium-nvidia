# Arcalium Control Centre

Tauri 2 + React + TypeScript app (`io.arcalium.ControlCentre`).

## Modes

- **Control Centre** (default) — all §9.2 pages; `arcalium-control-centre-launch` opens Setup first while incomplete
- **Setup wizard** — `arcalium-control-centre --setup` or `arcalium-setup`

No login autostart. Desktop + Kickoff Control Centre use the launch router.
Resume / restart: Kickoff → **Arcalium Setup**, or Settings → Setup wizard.

## Pages

| Page | Backend |
|---|---|
| Overview | `system` / `gpu` / `vulkan` / `steam status` + Install Steam (Flathub) / Launch |
| Gaming | `apps list` / Steam via `steam install --visible` / Flatpak install (terminal) / uninstall + launch |
| Compatibility | `proton list` / `install-recommended`, ProtonPlus, Protontricks |
| GPU and Display | `gpu status` / `validate`, `vulkan test` |
| Applications | catalogue-driven `apps` ops |
| Storage | `storage scan` (read-only); Open disk utility → KDE Partition Manager |
| Network and VPN | `network status` + Proton VPN Flatpak |
| Controllers | `controllers list` |
| Streaming | Sunshine / Moonlight / OBS via `apps` |
| Updates and Recovery | `updates status` / `check` / `apply` / `rollback` / `reboot` (terminal + sudo) |
| Diagnostics | `diagnostics run` / `bundle` |
| Local AI Assistant | `ai install-ollama` / `ensure` / `launch` / `stop`; min 16 GiB RAM / 8 GiB VRAM soft warning; Desktop shortcut after successful ensure |
| Settings | prefs + setup resume/restart |
| About | image identity |

Privileged policy: user Flatpak install/uninstall only. No Polkit helper yet;
`bootc` mutate stays as copyable commands.

Catalogue source: `config/catalogue/apps.v1.json` → `/usr/share/arcalium/catalogue/`.

Setup progress: `~/.config/arcalium/setup-progress.json`  
Setup complete: `~/.config/arcalium/setup-complete.json`  
Setup prefs: `~/.config/arcalium/setup-prefs.json` (`showOnStartup` = open Setup from Control Centre)

Settings: **Open Setup from Control Centre** toggle + Resume / Restart.

**Deferred:** UI polish after Setup wizard and Control Centre pages are solid.

## Local build (WSL)

```bash
just build-control-centre
# artifacts: output/control-centre/arcalium-control-centre
```

The full OS image build compiles this stage automatically (see Containerfile
`control-centre` stage) and `build_files/build.sh` installs the binary to
`/usr/bin/arcalium-control-centre`.
