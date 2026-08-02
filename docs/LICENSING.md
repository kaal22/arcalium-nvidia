# Licensing inventory

Status: **public-prep — docs ready for review** — Steam, Brave, and Spotify are **not** bundled in the ISO (Flathub on demand). Firefox, Heroic, and ProtonPlus are bundled. Notices/privacy/support/install docs are in `docs/`. GHCR package remains **private** until you intentionally publish.

## Arcalium OS

- Project licence for Arcalium-authored files: Apache-2.0 (repository `LICENSE` from Universal Blue’s image-template; Arcalium additions follow the same terms unless a file says otherwise).
- Product name: Arcalium OS / Arcalium OS NVIDIA Edition.
- Package namespace: `io.arcalium`.

### Branding assets (owner-supplied)

| Asset | Path | Licence record |
|---|---|---|
| Mark | `assets/arccleanSVG.svg` | Copyright project owner; supplied for Arcalium OS redistribution in this project |
| Wordmark | `assets/ARG_fullSVG.svg` | Same |
| Wallpaper | `assets/arcalium-wallpaper.png` | Same |
| Plymouth watermark | Generated at build from wordmark | Same |

## Upstream bases

| Component | Source | Notes |
|---|---|---|
| image-template | ublue-os/image-template | Apache-2.0 |
| Bazzite NVIDIA-open | ghcr.io/ublue-os/bazzite-nvidia-open | Follow Bazzite / Universal Blue notices |
| Fedora Atomic / bootc | Fedora Project | Upstream OS licences |

## Bundled Flatpaks (in the ISO)

Listed in `installer/flatpaks` and copied to disk at install. Redistribution checked for public ISO.

| Flatpak ID | Verified on Flathub | Licence | Redistribution note |
|---|---|---|---|
| `org.mozilla.firefox` | Yes — Mozilla | MPL-2.0 | Default browser. Open-source; fine to redistribute. |
| `com.vysp3r.ProtonPlus` | Yes — vysp3r.com | GPL-3.0-or-later | Compatibility-tool manager, not Proton VPN. |
| `com.heroicgameslauncher.hgl` | Yes — heroicgameslauncher.com | GPL-3.0 | Launcher only; no store content. |

## On-demand Flatpaks (Control Centre / Flathub — not ISO-bundled)

| Flatpak ID | Notes |
|---|---|
| `com.valvesoftware.Steam` | Valve Flatpak; SSA on first Steam launch |
| `com.brave.Browser` | Optional browser; install from Flathub (not bundled — avoids redistributing Brave’s branded binaries in every ISO) |
| `com.spotify.Client` | Community package; not affiliated with or supported by Spotify; install from Flathub |
| `com.usebottles.bottles` | Optional |
| `org.prismlauncher.PrismLauncher` | Optional |
| `com.github.Matoking.protontricks` | Optional |
| `com.github.tchx84.Flatseal` | Optional |
| `com.discordapp.Discord` | Proprietary client; optional |
| `com.obsproject.Studio` | Optional |
| `dev.lizardbyte.app.Sunshine` | Optional host |
| `com.moonlight_stream.Moonlight` | Optional |
| `com.protonvpn.www` | Optional VPN GUI |

## Branding and trademarks

Arcalium OS is an independent project built on Bazzite and is **not** affiliated with or endorsed by Valve, NVIDIA, OpenAI, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

Third-party names are used only to describe compatibility. See also [`docs/NOTICES.md`](NOTICES.md).

## Release gates

1. Preserve required Bazzite / Universal Blue notices.
2. **Steam / Brave / Spotify:** do not ship these clients in the image or ISO; Control Centre installs from Flathub.
3. Disclose community Flatpaks (e.g. Spotify) accurately.
4. Firefox (MPL-2.0), Heroic, and ProtonPlus may ship bundled.
5. Do not ship assets without redistribution rights (owner assets recorded above).
6. Cosign private key must never be committed.
7. Do not make the GHCR package public until notices, privacy, and support docs are accepted and you intentionally flip visibility.

## Related docs

- [`docs/NOTICES.md`](NOTICES.md)
- [`docs/PRIVACY.md`](PRIVACY.md)
- [`docs/KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md)
- [`docs/SUPPORT.md`](SUPPORT.md)
- [`docs/RECOVERY.md`](RECOVERY.md)
