# Arcalium Control Centre

Tauri 2 + React + TypeScript app (`io.arcalium.ControlCentre`).

All §9.2 navigation pages are live. They call allowlisted `arcaliumctl … --json`
commands and/or `gio launch` for desktop entries:

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
| Settings | local preferences + System Settings link |
| About | image identity |

Privileged policy: user Flatpak install/uninstall only. No Polkit helper yet;
`bootc` mutate stays as copyable commands.

Catalogue source: `config/catalogue/apps.v1.json` → `/usr/share/arcalium/catalogue/`.

**Deferred:** UI polish after every page works; Setup wizard next.

## Local build (WSL)

```bash
just build-control-centre
# artifacts: output/control-centre/arcalium-control-centre
```

The full OS image build compiles this stage automatically (see Containerfile
`control-centre` stage) and `build_files/build.sh` installs the binary to
`/usr/bin/arcalium-control-centre`.
