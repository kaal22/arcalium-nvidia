# Third-party notices

Arcalium OS NVIDIA Edition is an independent project. It is **not** affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Mozilla, Brave Software, Fedora, Universal Blue, or the Bazzite project.

## Software included or used

| Component | Licence / terms | Notes |
|---|---|---|
| Arcalium-authored files | Apache-2.0 (see repository `LICENSE`) | Control Centre, `arcaliumctl`, setup, branding wiring |
| Universal Blue image-template | Apache-2.0 | Build scaffolding |
| Bazzite NVIDIA-open | Upstream Bazzite / Universal Blue notices | Base OS image |
| Fedora / bootc / rpm-ostree | Fedora Project licences | Atomic update stack |
| Firefox Flatpak | MPL-2.0 | Bundled default browser |
| Heroic Games Launcher | GPL-3.0 | Bundled |
| ProtonPlus | GPL-3.0-or-later | Bundled |
| Steam, Brave, Spotify, other catalogue apps | Respective vendors / Flathub packages | **Not** shipped in the ISO; installed by the user from Flathub |

Preserve any additional licence texts shipped inside the base image and Flatpak runtimes.

## Trademarks

Product and company names (Steam, NVIDIA, Firefox, Brave, Spotify, Heroic, Proton, Fedora, Bazzite, etc.) are trademarks of their respective owners and are used only to describe compatibility.

## Cosign

Container images may be signed with Cosign. The public key is `cosign.pub` in this repository. The private signing key is never committed.
