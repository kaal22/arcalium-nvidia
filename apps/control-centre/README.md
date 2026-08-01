# Arcalium Control Centre

Tauri 2 + React + TypeScript app (`io.arcalium.ControlCentre`).

## Modes

- **Control Centre** (default) — all §9.2 pages
- **Setup wizard** — `arcalium-control-centre --setup` or `arcalium-setup`

Autostart: `arcalium-setup --autostart` (skips live installer and completed users).
Resume / restart: Kickoff → **Arcalium Setup**, or Settings → Setup wizard.

## Pages

| Page | Backend |
|---|---|
| Overview | `system` / `gpu` / `vulkan` + quick actions |
| Gaming | `apps list` / install / uninstall + launch |
| Compatibility | `proton list` / `install-recommended`, ProtonPlus, Protontricks |
| GPU and Display | `gpu status` / `validate`, `vulkan test` |
| Applications | catalogue-driven `apps` ops |
| Storage | `storage scan` (read-only) |
| Network and VPN | `network status` + Proton VPN Flatpak |
| Controllers | `controllers list` |
| Streaming | Sunshine / Moonlight / OBS via `apps` |
| Updates and Recovery | `updates status` (guidance only for apply/rollback) |
| Diagnostics | `diagnostics run` / `bundle` |
| Settings | prefs + setup resume/restart |
| About | image identity |

Privileged policy: user Flatpak install/uninstall only. No Polkit helper yet;
`bootc` mutate stays as copyable commands.

Catalogue source: `config/catalogue/apps.v1.json` → `/usr/share/arcalium/catalogue/`.

Setup progress: `~/.config/arcalium/setup-progress.json`  
Setup complete: `~/.config/arcalium/setup-complete.json`

**Deferred:** UI polish after Setup wizard and Control Centre pages are solid.

## Local build (WSL)

```bash
just build-control-centre
# artifacts: output/control-centre/arcalium-control-centre
```

The full OS image build compiles this stage automatically (see Containerfile
`control-centre` stage) and `build_files/build.sh` installs the binary to
`/usr/bin/arcalium-control-centre`.
