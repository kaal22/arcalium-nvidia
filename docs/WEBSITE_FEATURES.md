# Arcalium OS — feature inventory for website copy (0.2.0)

**Audience:** you writing getarcalium.com copy. This is a **facts list**, not marketing prose.  
**Edition:** Arcalium OS **NVIDIA Edition** · version **0.2.0** · channel **`stable`**.  
**Base:** Bazzite NVIDIA-open (`bazzite-nvidia-open`) → Fedora Atomic / **bootc** immutable image.  
**Desktop:** **KDE Plasma** on **Wayland**.  
**Site:** https://getarcalium.com · GitHub: https://github.com/kaal22/arcalium-nvidia  
**Image:** `ghcr.io/kaal22/arcalium-os-nvidia:stable` (Cosign-signed).

**Required disclaimer (product / trademarks):**  
Arcalium OS is an independent project built on Bazzite. It is **not** affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue, or the Bazzite project.

---

## One-line positioning

Gaming-first Linux desktop OS for **NVIDIA** PCs: install, set up games and apps with a visual Control Centre, update/rollback safely, optional offline Local AI — without shipping Steam or redistributing proprietary clients by default.

---

## Core platform

| Feature | Detail |
|---|---|
| Immutable OS image | Atomic updates via **bootc** / ostree; previous deployment kept for rollback |
| NVIDIA drivers | **nvidia-open** stack (Turing and newer — GTX 16 / all RTX). No manual driver hunt. Newer drivers arrive with **OS image updates** after Arcalium re-pins Bazzite — not GeForce Experience / `.run` installers |
| Wayland Plasma | Modern KDE desktop as the daily environment |
| Live installer ISO | Bootable live/installer ISO (`Arcalium-Live-0.2.0.iso`); Install-focused live session |
| Secure Boot path | Live ISO uses Fedora-signed kernel path for Secure Boot on live media (installed system uses image kernel/drivers) |
| Signed releases | Container images signed with **Cosign** (public key in repo) |
| No Arcalium telemetry | No phone-home / no Arcalium account (see Privacy) |
| Hostname | Default suggestion **arcalium** |
| Branding | Arcalium wallpaper (desktop + lock + login), logo mark/wordmark, Plasma splash, Plymouth watermark (“OS Loading”) showing Arcalium |

---

## Hardware guidance (website-safe)

| Item | Guidance |
|---|---|
| Target GPUs | NVIDIA **Turing and newer** (e.g. RTX 20 / 30 / 40-class; primary validation: **RTX 3060 12 GB**) |
| Not v1 target | Pascal / Maxwell / Volta legacy; Steam Gaming Mode / NVIDIA “console” session |
| Local AI floor | Soft minimum **16 GiB system RAM** and **8 GiB GPU VRAM** (warn in Setup/CC; not a hard block) |
| Live ISO on NVIDIA | May need **Basic Graphics Mode** (`nomodeset`) if live session black-screens; **installed** system uses nvidia-open |
| Game libraries | Prefer Linux-friendly filesystems; **NTFS game libraries unsupported** for intended workflow |

---

## Install & first run

| Feature | Detail |
|---|---|
| Live USB / Ventoy | Write ISO; Ventoy: prefer **GRUB2**; optional Basic Graphics Mode on live |
| Anaconda installer | Familiar bootc/Bazzite-style install flow (“Install Arcalium OS”) |
| Plasma Welcome | May still appear (upstream); separate from Arcalium Setup |
| Arcalium Setup | First-run **visual wizard** (opens from Control Centre / Desktop shortcut while incomplete — **no forced login popup**) |
| Setup can be skipped / resumed | Steps skippable where designed; resume from Settings / Kickoff → Arcalium Setup |
| Desktop shortcut | New installed users get **Arcalium Control Centre** on Desktop; Kickoff entry too |

### Setup wizard steps (in order)

1. Welcome  
2. Hardware summary  
3. NVIDIA / GPU check  
4. Display  
5. Updates / deployment awareness  
6. Applications (catalogue picks)  
7. Proton-GE (recommended install action)  
8. Steam (optional Flathub install — not preinstalled)  
9. Storage (scan drives; open disk utility)  
10. VPN (Proton VPN guidance / optional app)  
11. Streaming (Sunshine / Moonlight / OBS optional)  
12. Validation / diagnostics checklist  
13. **Local AI** (optional Install Ollama / pull model / Skip)  
14. Completion → handoff to Control Centre  

---

## Arcalium Control Centre (pages)

Single Tauri app: **Control Centre** + **Setup** modes (`io.arcalium.ControlCentre`).

| Page | What it does |
|---|---|
| Overview | System / GPU / Vulkan snapshot; Steam status; Install Steam (Flathub) / Launch |
| Gaming | Catalogue gaming apps; Steam install; Flatpak install/uninstall (terminal progress) |
| Compatibility | Proton list; install recommended Proton-GE; ProtonPlus / Protontricks |
| GPU and Display | `nvidia-smi`-class status; Vulkan test; display info; **Drivers** block (check/apply OS update for newer nvidia-open) |
| Applications | Full declarative app catalogue (friendly descriptions, not Flatpak-ID-first copy) |
| Storage | Read-only drive/mount scan; **Open disk utility** → **KDE Partition Manager** |
| Network and VPN | Network status; Proton VPN Flatpak (user signs in — Arcalium never stores VPN secrets) |
| Controllers | Detect connected game controllers |
| Streaming | Sunshine / Moonlight / OBS install paths |
| Updates and Recovery | Check / apply update / rollback / reboot via terminal + `sudo bootc` (user types `yes` for apply/rollback); no silent privileged mutate from UI |
| Diagnostics | Health checklist; redacted support bundle under `~/.local/state/arcalium/` |
| Local AI Assistant | Install Ollama, pull/configure model, launch assistant, refresh agent prompt, unload model; min-spec display |
| Settings | Preferences; reopen / restart Setup |
| About | Image identity / notices |

**Privileged policy:** user Flatpak installs OK; OS update/mutate happens in a terminal with password + confirmation — never silent Polkit bootc from the GUI.

Also available: **Bazaar** / Flathub for broader Flatpak discovery (upstream gaming desktop pattern).

---

## Updates, rollback, recovery

| Feature | Detail |
|---|---|
| Update channel | Track `ghcr.io/kaal22/arcalium-os-nvidia:stable` |
| Apply update | `bootc upgrade` (Control Centre opens a guided terminal) |
| Rollback | Previous OS deployment bootable (`bootc rollback`) — restores OS image, **not** deleted personal files |
| Reboot | Explicit after update/rollback |
| CLI | `arcaliumctl updates status\|check\|apply\|rollback\|reboot` |
| Local AI tools | Assistant can call allowlisted `updates_*` tools (mutating ones ask for `yes`) |

---

## Gaming & compatibility

| Feature | Detail |
|---|---|
| Steam | **Not** in the image/ISO. Install from Control Centre → Flathub (`com.valvesoftware.Steam`). SSA on first Steam launch |
| Proton / Proton-GE | Install recommended Proton-GE into Steam compatibility tools; Steam’s default remains until user chooses |
| ProtonPlus | Bundled helper to manage Proton versions |
| Protontricks | Optional Flatpak for per-game fixes |
| Heroic | Bundled — Epic / GOG / Amazon |
| Bottles | Optional — Windows apps/games in isolated prefixes |
| Prism Launcher | Optional — Minecraft |
| Controllers | Detection in Control Centre |
| Explicitly not offered | **Lutris** (by design — Heroic covers non-Steam stores) |
| Explicitly not v1 | Steam Gaming Mode / console-style session on NVIDIA |

---

## Apps: bundled vs install-on-demand

### Bundled in the ISO / install (preinstalled Flatpaks)

| App | Role |
|---|---|
| **Firefox** | Default browser |
| **Heroic Games Launcher** | Epic / GOG / Amazon |
| **ProtonPlus** | Proton version manager |

### On-demand via Control Centre / Flathub (not preinstalled)

| App | Role / note |
|---|---|
| **Steam** | Primary PC game store; SSA on first launch |
| **Brave** | Optional privacy browser |
| **Spotify** | Community Flatpak — disclose not official Spotify |
| **Bottles** | Windows prefixes |
| **Prism Launcher** | Minecraft |
| **Protontricks** | Game-specific Proton fixes |
| **Flatseal** | Flatpak permissions |
| **Discord** | Chat / voice |
| **OBS Studio** | Record / stream |
| **Sunshine** | Game-stream **host** (may need extra docs/firewall; ports not auto-opened) |
| **Moonlight** | Game-stream **client** (pairs with Sunshine) |
| **Proton VPN** | VPN GUI; user signs in; Arcalium does not import secrets |

---

## Local AI Assistant (optional)

| Feature | Detail |
|---|---|
| Engine | **Ollama** (user install via Homebrew in the user environment — **not** layered into the immutable image) |
| Base model | `gemma4:e4b-it-qat` (first pull ~**10 GB** class) |
| Session model | `arcalium-assistant` (Modelfile + Arcalium system prompt: Linux / bash / bootc / Flatpak context) |
| Surfaces | Setup step + Control Centre page + menu entry + Desktop shortcut after successful pull |
| Launcher / icon | `arcalium-assistant` / `io.arcalium.Assistant` — Space Invaders–style pixel face icon |
| Agent mode | Allowlisted tools only (`ARCALIUM_TOOL …`); read-only auto-run; mutating needs typing **`yes`**; no arbitrary shell/`sudo`/raw bootc |
| Example tools | GPU/Vulkan/system status, apps install/uninstall, Steam install, updates status/check/apply/rollback, diagnostics, controllers |
| Min hardware UI | Shows **16 GiB RAM · 8 GiB VRAM** floor + measured This PC; soft-warn if below |
| VRAM for gaming | Closing the assistant terminal stops/unloads models so GPU memory is freed |
| Privacy | Chat stays **local/offline** after model is present — no Arcalium cloud chat API |

---

## Storage & disks

| Feature | Detail |
|---|---|
| Storage page | Read-only overview of drives, mounts, capacity |
| Disk utility | Opens **KDE Partition Manager** (included in the image) |
| Secondary game drives | Setup/Control Centre guidance; safe detection over silent format |
| Spec constraint | No disk formatting / destructive wipe from Control Centre itself |

---

## Network & privacy posture

| Feature | Detail |
|---|---|
| Privacy | No Arcalium telemetry, accounts, or mandatory analytics |
| Updates | Normal HTTPS image pulls from the configured registry |
| Third-party apps | Steam / Discord / Spotify / etc. follow **their** policies once installed |
| Diagnostics | Redacted support bundles; review before sharing |
| Docs | Notices, Privacy, Support, Recovery, Known limitations shipped in repo |

---

## CLI (`arcaliumctl`) — useful for accurate “power user” blurb

JSON-friendly allowlisted CLI covering: system/gpu/vulkan, steam, apps, proton, storage, network, controllers, updates, diagnostics, setup, ai.  
Diagnostic commands only run allowlisted binaries (e.g. `nvidia-smi`, `vulkaninfo`, `bootc`) — not arbitrary shell fragments.

---

## What to **avoid** claiming on the website

- That every Windows game / anti-cheat title works  
- Official partnership with Valve, NVIDIA, Spotify, Bazzite, Universal Blue, etc.  
- That Steam, Brave, or Spotify come **preinstalled**  
- Steam Gaming Mode / console UI as a product feature  
- Game Pass–style local Xbox PC library parity  
- That Local AI runs well on machines under **16 GiB RAM / 8 GiB VRAM**  
- That users should install NVIDIA Game Ready drivers from nvidia.com on Arcalium  
- That `bootc` rollback undeletes personal files  
- That Arcalium phones home or needs a cloud account  
- That VPN is zero-latency or that Sunshine firewall ports are magically opened  

---

## Short “what you get” bullet bank (raw — rewrite as you like)

- Gaming Linux desktop built for NVIDIA GPUs  
- KDE Plasma on Wayland  
- Atomic updates with easy rollback  
- Guided first-run Setup  
- Arcalium Control Centre for games, apps, GPU, storage, streaming, updates  
- Firefox ready; Steam one click away from Flathub  
- Heroic + Proton tooling included or one click  
- Optional local AI assistant that stays on your PC  
- Partition tools when you need a second drive  
- Cosign-signed releases; open build instructions  

---

## Artefacts to link on the site

| Artefact | Notes |
|---|---|
| Live ISO | `Arcalium-Live-0.2.0.iso` (~7.3 GB) |
| SHA-256 | `ec70c4f69850170ffab3a7ab6cabc15da07de9d76a94b1c3b7f23bd0a90d8d98` |
| Image | `ghcr.io/kaal22/arcalium-os-nvidia:stable` |
| Digest | `sha256:161e87aa0690354fdb35bfc61932d87c9dfc987201270e6d71286890c6b66fb9` |
| GitHub Release | https://github.com/kaal22/arcalium-nvidia/releases/tag/0.2.0 |
| Install / support docs | `docs/INSTALL.md`, `SUPPORT.md`, `PRIVACY.md`, `NOTICES.md`, `KNOWN_LIMITATIONS.md` |

Source of truth for deeper requirements: [`docs/PRODUCT_SPEC.md`](PRODUCT_SPEC.md). Status: [`docs/IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md).
