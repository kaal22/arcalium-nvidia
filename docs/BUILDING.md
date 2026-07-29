# Building Arcalium OS NVIDIA Edition

Arcalium derives from Universal Blue’s [image-template](https://github.com/ublue-os/image-template) and the Bazzite NVIDIA-open desktop image.

## Prerequisites

- GitHub repository with Actions enabled
- Cosign keypair (`cosign.pub` in repo; private key only as `SIGNING_SECRET`)
- For local builds: a Linux host with Podman (preferably already on a Universal Blue / bootc system)

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

## Build disk images (QCOW2 / ISO)

1. Ensure a `dev` image already exists in GHCR.
2. Manually run **Build disk images** (`.github/workflows/build-disk.yml`).
3. Choose platform `amd64`.
4. Artifacts: QCOW2 + Anaconda ISO (+ checksums when uploaded).

Local equivalent on a suitable host:

```bash
just build
just build-qcow2
just build-iso
```

## Switch an existing Bazzite system (private testing)

```bash
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:dev
sudo systemctl reboot
```

## Important gates

- Do not publish a public ISO until the Steam licensing gate in `docs/PRODUCT_SPEC.md` §17.2 is resolved.
- Do not start the Control Centre until the base image and ISO workflow are proven (spec §28).
- Do not invent Flatpak IDs, `ujust` paths, or bootc flags — verify against upstream first.
