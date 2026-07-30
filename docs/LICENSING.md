# Licensing inventory (Phase 0 draft)

Status: **in progress** — expand before private alpha distribution.

## Arcalium OS

- Project licence for Arcalium-authored files: TBD (repository currently carries the Apache-2.0 `LICENSE` from Universal Blue’s image-template).
- Product name: Arcalium OS / Arcalium OS NVIDIA Edition.
- Package namespace (planned): `io.arcalium`.

## Upstream bases

| Component | Source | Notes |
|---|---|---|
| image-template | ublue-os/image-template | Apache-2.0 |
| Bazzite NVIDIA-open | ghcr.io/ublue-os/bazzite-nvidia-open | Follow Bazzite / Universal Blue notices |
| Fedora Atomic / bootc | Fedora Project | Upstream OS licences |

## Bundled Flatpaks

Anything listed in `installer/flatpaks` is copied into the ISO, so we redistribute it rather than merely linking to it. Each entry needs a redistribution check before a public release.

| Flatpak ID | Verified on Flathub | Licence | Redistribution note |
|---|---|---|---|
| `com.brave.Browser` | Yes — verified via `brave.com`, publisher Brave Software | MPL-2.0 (project) | The Flathub build repacks Brave's official release archive, so a public ISO redistributes Brave's binaries and marks. Confirm Brave's terms and trademark policy before any public ISO. |
| `com.spotify.Client` | **No** — community-provided package | Proprietary Spotify client | Not affiliated with or supported by Spotify. The Flatpak repackages Spotify's official client; every user-facing catalogue and setup surface must disclose that the package is community-maintained. Confirm redistribution terms before a public ISO. |
| `com.vysp3r.ProtonPlus` | Yes — verified via `vysp3r.com`, publisher Vysp3r | GPL-3.0-or-later | Compatibility-tool manager, not Proton VPN and not affiliated with Proton AG. |

## Web-app launchers

| Launcher | URL | Redistribution note |
|---|---|---|
| ChatGPT | `https://chatgpt.com/` | Shortcut only: launches the official website in Brave's app-window mode. Arcalium does not redistribute a ChatGPT client, OpenAI assets or credentials. There is no official Linux ChatGPT application as of 2026-07-30; do not replace this with an unofficial wrapper without a separate security and licensing review. |

## Branding and trademarks

Arcalium OS is an independent project built on Bazzite and is **not** affiliated with or endorsed by Valve, NVIDIA, OpenAI, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

Third-party names are used only to describe compatibility.

## Release gates (do not skip)

1. Preserve all required Bazzite / Universal Blue notices.
2. Resolve Steam client redistribution before any **public** ISO (PRODUCT_SPEC §17.2).
3. Disclose community Flatpaks (e.g. Spotify) accurately. Brave and Firefox are both publisher-verified on Flathub, so neither carries the "community-maintained" caveat.
4. Confirm Brave's redistribution and trademark terms before a public ISO bundles it.
5. Do not ship assets without redistribution rights.
6. Cosign private key must never be committed.

## Assets still needed

- Arcalium logo licence record (`assets/arccleanSVG.svg` mark, `assets/ARG_fullSVG.svg` wordmark — supplied by the project owner; source/author/redistribution licence still need recording before a public image or ISO)
- `assets/arcalium-wallpaper.png`: supplied for use by the project owner; original source, author and redistribution licence still need recording before any public image or ISO
- Lock-screen wallpaper licence record
- Font licence records (when fonts are added)
- Proton-GE notices if an archive is ever bundled
- Plymouth watermark PNG — generated at image-build time from `assets/ARG_fullSVG.svg` into `/usr/share/plymouth/themes/spinner/watermark.png` (~256×121, transparent)
- Dark (non-white) mark variant for light Plasma panels — current SVGs are white fill only
