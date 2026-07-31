# Arcalium Control Centre

Tauri 2 + React + TypeScript app (`io.arcalium.ControlCentre`).

Live pages call allowlisted `arcaliumctl … --json` commands only:

- **Overview** — system / GPU / Vulkan summary; quick actions including Install Proton-GE
- **Compatibility** — `proton list`, `proton install-recommended`, Open ProtonPlus, static ProtonDB / anti-cheat guidance
- **About** — image identity

Other nav pages remain stubs until later one-feature passes.

## Local build (WSL)

```bash
just build-control-centre
# artifacts: output/control-centre/arcalium-control-centre
```

The full OS image build compiles this stage automatically (see Containerfile
`control-centre` stage) and `build_files/build.sh` installs the binary to
`/usr/bin/arcalium-control-centre`.
