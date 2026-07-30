# Allow build scripts to be referenced without being copied into the final image
FROM scratch AS ctx
COPY build_files /
COPY system_files /system_files
COPY assets /assets

# Base Image — Arcalium OS NVIDIA Edition
# Source of truth: docs/PRODUCT_SPEC.md
# Verified tag exists: ghcr.io/ublue-os/bazzite-nvidia-open (stable, testing, unstable, …)
# Digest resolved 2026-07-29 for :stable — re-pin when promoting builds.
FROM ghcr.io/ublue-os/bazzite-nvidia-open:stable@sha256:83c6084f9713abda10b966dce3631f4c9b4430e419f06c9a76dad10bfc43cbe9
## Edition notes:
# - bazzite-nvidia-open: Turing-and-newer (GTX 16 / all RTX), incl. RTX 2060 + RTX 3090
# - Legacy Pascal/Maxwell/Volta is out of scope for version 1 (see PRODUCT_SPEC)
# Universal Blue packages: https://github.com/orgs/ublue-os/packages

### [IM]MUTABLE /opt
## Some bootable images, like Fedora, have /opt symlinked to /var/opt, in order to
## make it mutable/writable for users. However, some packages write files to this directory,
## thus its contents might be wiped out when bootc deploys an image, making it troublesome for
## some packages. Eg, google-chrome, docker-desktop.
##
## Uncomment the following line if one desires to make /opt immutable and be able to be used
## by the package manager.

# RUN rm /opt && mkdir /opt

### MODIFICATIONS
## make modifications desired in your image and install packages by modifying the build.sh script
## the following RUN directive does all the things required to run "build.sh" as recommended.

RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/build.sh

### LINTING
## Verify final image and contents are correct.
RUN bootc container lint
