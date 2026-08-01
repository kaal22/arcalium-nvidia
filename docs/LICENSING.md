# Licensing inventory (Phase 0 draft)

Status: **in progress** — Steam deferred (not shipped; Valve download from Control Centre). Expand notices/privacy before public distribution.

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
| `com.heroicgameslauncher.hgl` | Yes — verified via `heroicgameslauncher.com` | GPL-3.0 | Open-source launcher for Epic, GOG and Amazon libraries. Arcalium redistributes only the launcher: no store client, game content or store credentials. Users authenticate to those stores themselves, and Arcalium is not affiliated with Epic Games, GOG or Amazon. |

## Catalogue Flatpaks (install-on-demand, not ISO-bundled)

Offered by Control Centre `apps install` / Applications pages. Not copied into the live ISO unless also listed under `installer/flatpaks`. Confirm redistribution before any public ISO that bundles them.

| Flatpak ID | Verified on Flathub | Notes |
|---|---|---|
| `com.usebottles.bottles` | Yes | Optional Wine prefix manager |
| `org.prismlauncher.PrismLauncher` | Yes | Minecraft launcher |
| `com.github.Matoking.protontricks` | Yes | Proton helper |
| `com.github.tchx84.Flatseal` | Yes | Flatpak permissions |
| `com.discordapp.Discord` | Yes | Proprietary client |
| `com.obsproject.Studio` | Yes | Streaming/recording |
| `dev.lizardbyte.app.Sunshine` | Yes | Opt-in host; extra Flatpak install script; firewall not opened by Arcalium |
| `com.moonlight_stream.Moonlight` | Yes | GameStream client |
| `com.protonvpn.www` | Yes | Optional VPN GUI; secrets not imported by Control Centre |

## Web-app launchers

| Launcher | URL | Redistribution note |
|---|---|---|
| ChatGPT | — | Removed 2026-07-31. Previously a Brave `--app=` shortcut to `https://chatgpt.com/` only; no OpenAI client or assets were redistributed. |

## Branding and trademarks

Arcalium OS is an independent project built on Bazzite and is **not** affiliated with or endorsed by Valve, NVIDIA, OpenAI, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

Third-party names are used only to describe compatibility.

## Release gates (do not skip)

1. Preserve all required Bazzite / Universal Blue notices.
2. **Steam:** do not ship the Steam client in the image or ISO. `build.sh` removes inherited `steam` RPMs. Users install Valve’s Flatpak from Flathub via Control Centre / `arcaliumctl steam install --visible` (alias `open-download`). Steam shows the Steam Subscriber Agreement on first launch (PRODUCT_SPEC §17.2).
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
