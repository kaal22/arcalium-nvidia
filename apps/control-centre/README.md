# Arcalium Control Centre

Tauri 2 + React + TypeScript app (`io.arcalium.ControlCentre`).

Overview MVP calls allowlisted `arcaliumctl … --json` commands only. Other nav
pages are stubs until later phases.

## Local build (WSL)

```bash
just build-control-centre
# artifacts: output/control-centre/arcalium-control-centre
```

The full OS image build compiles this stage automatically (see Containerfile
`control-centre` stage) and `build_files/build.sh` installs the binary to
`/usr/bin/arcalium-control-centre`.
