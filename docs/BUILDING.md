# Building Arcalium OS NVIDIA Edition

Arcalium derives from Universal Blue’s [image-template](https://github.com/ublue-os/image-template) and the Bazzite NVIDIA-open desktop image.

## Prerequisites

- GitHub repository with Actions enabled
- Cosign keypair (`cosign.pub` in repo; private key only as `SIGNING_SECRET`)
- For local builds: a Linux host with Podman (preferably already on a Universal Blue / bootc system). A Windows workstation cannot build disk images; Bootc Image Builder needs a privileged Linux container with loop devices.

## One-time Cosign setup

Keys were generated with Cosign **v2.6.3** (empty password, as required by the template workflow):

```bash
COSIGN_PASSWORD="" cosign generate-key-pair
```

1. Commit **only** `cosign.pub`.
2. Add the contents of `cosign.key` as the Actions secret `SIGNING_SECRET`.
3. Delete or securely store `cosign.key` outside the repo.

Verify a published image:

```bash
cosign verify --key cosign.pub ghcr.io/kaal22/arcalium-os-nvidia:dev
```

## Configure identity

Edit `image-template.env` if needed:

| Variable | Value |
|---|---|
| `IMAGE_NAME` | `arcalium-os-nvidia` |
| `REPO_ORGANIZATION` | GitHub owner (currently `kaal22`) |
| `DEFAULT_TAG` | `dev` |

Keep `disk_config/iso.toml` and `.github/workflows/build-disk.yml` in sync with those values.

## Build OCI image (GitHub Actions)

1. Push to the default branch (`main`).
2. Workflow: **Build container image** (`.github/workflows/build.yml`).
3. Image publishes to `ghcr.io/<owner>/arcalium-os-nvidia` with `dev` and date/SHA alias tags.
4. The workflow signs the digest with Cosign.

## Visibility model

| Surface | Setting | Reason |
|---|---|---|
| GitHub repository | public | Free Actions minutes and artifact storage; spec principle 9 (open maintenance) |
| GHCR image package | private | Spec §17.2 — the built image carries the inherited Steam client |
| Disk images (ISO/QCOW2) | private artifacts | Downloaded by the maintainer, or built locally |

Making a GHCR package public is irreversible. Do not change the package to public until the Steam licensing gate is resolved.

## Build disk images (QCOW2 / ISO) — local, preferred

Local builds run against the image in local container storage, so they never pull from GHCR and need no registry credentials.

Requires a Linux host with Podman, `sudo`, privileged containers, and plenty of free disk. A machine already running Bazzite or Arcalium is ideal.

```bash
just build                # builds localhost/arcalium-os-nvidia:dev
just build-qcow2          # QCOW2 for VM boot tests
just build-iso            # Anaconda installer ISO
```

Output lands in `output/`. `build-iso` uses `disk_config/iso.toml`; `build-qcow2` uses `disk_config/disk.toml`.

## Build disk images (GitHub Actions) — currently blocked

**Build disk images** (`.github/workflows/build-disk.yml`) requires the image to be pullable by `osbuild/bootc-image-builder-action`. That action exposes no authentication or pull-secret input, so it cannot pull the private `arcalium-os-nvidia` package. Options, none adopted yet:

- Build disk images locally (preferred while the package stays private).
- Upload to S3 with the workflow's existing `S3_*` secrets, which avoids artifact storage limits but does not solve the pull.
- Revisit if upstream adds registry authentication.

## Bootstrap the first test machine (no Arcalium ISO needed)

An Arcalium ISO is only needed for clean-install repeatability testing. To validate hardware sooner, rebase an existing Bazzite install:

1. Install stock `bazzite-nvidia-open` from the official [Bazzite ISO](https://download.bazzite.gg).
2. Authenticate to GHCR for the private package, using a token with `read:packages`:

```bash
sudo podman login ghcr.io -u <github-username>
```

3. Switch to the Arcalium image and reboot:

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:dev
sudo systemctl reboot
```

That machine then doubles as the local ISO builder.

Note: `disk_config/iso.toml` runs `bootc switch` in the Anaconda `%post` stage. While the package is private, that step needs credentials available to the installer.

## Important gates

- Do not publish a public ISO until the Steam licensing gate in `docs/PRODUCT_SPEC.md` §17.2 is resolved.
- Do not start the Control Centre until the base image and ISO workflow are proven (spec §28).
- Do not invent Flatpak IDs, `ujust` paths, or bootc flags — verify against upstream first.
