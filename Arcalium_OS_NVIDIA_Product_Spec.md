# Arcalium OS — NVIDIA Edition
## Product Requirements, Technical Architecture and Delivery Plan

**Document status:** Implementation specification  
**Initial release:** Arcalium OS NVIDIA Edition  
**Primary base image:** `ghcr.io/ublue-os/bazzite-nvidia-open:stable`  
**Desktop:** KDE Plasma on Wayland  
**Initial test hardware:** NVIDIA GeForce RTX 3090 and NVIDIA GeForce RTX 2060 systems  
**Future edition:** Arcalium OS AMD/Intel Edition  
**Initial release channel:** Private alpha  

---

# 1. Instructions for Cursor

This document is the source of truth for the first Arcalium OS implementation.

Cursor must:

1. Work through the phases in this document in order.
2. Create a checklist in `docs/IMPLEMENTATION_STATUS.md`.
3. Mark each requirement as `not started`, `in progress`, `blocked`, `tested`, or `complete`.
4. Never invent package names, Flatpak IDs, image tags, Bazzite paths, `ujust` locations, bootc commands, or GitHub Action syntax.
5. Verify mutable implementation details against the current official Bazzite and Universal Blue repositories before writing code.
6. Prefer the official Universal Blue `image-template` over forking the full Bazzite repository.
7. Keep Arcalium close to upstream Bazzite so that upstream fixes continue to flow into Arcalium.
8. Keep every custom action idempotent. Running it twice must not corrupt or duplicate configuration.
9. Keep every risky action reversible.
10. Never silently format disks, alter partitions, change Secure Boot, overclock hardware, disable SELinux, or weaken system security.
11. Never run arbitrary shell commands received from the graphical frontend.
12. Use an allowlisted backend command interface for all system actions.
13. Add automated checks wherever practical.
14. Stop and record a blocker when an upstream interface cannot be confirmed.
15. Do not publicly release an ISO until the licensing release gates in this document have been addressed.

The project should be built as a real maintained operating-system image, not as a theme pack or a collection of post-install scripts.

---

# 2. Product Identity

## 2.1 Product name

**Arcalium OS**

## 2.2 First edition

**Arcalium OS NVIDIA Edition**

Suggested internal identifiers:

```text
Product name: Arcalium OS
Edition name: NVIDIA Edition
Image name: arcalium-os-nvidia
Repository name: arcalium-os
Package namespace: io.arcalium
Control Centre app ID: io.arcalium.ControlCentre
CLI command: arcaliumctl
Current development channel: dev
First public channel: stable
```

## 2.3 Positioning

Arcalium OS is a gaming-first Linux operating system designed to replace Windows on compatible gaming PCs while reducing setup work for ordinary users.

It should provide:

- A ready-to-game desktop.
- Preconfigured NVIDIA graphics support.
- Steam and Windows-game compatibility tooling.
- A straightforward app store.
- Guided installation of gaming launchers and social applications.
- Simple storage, update, rollback, VPN and diagnostics controls.
- A polished first-boot experience.
- Safe defaults rather than questionable “FPS boost” scripts.

## 2.4 Product promise

> Install Arcalium OS, complete one guided setup, sign into your services and start gaming.

## 2.5 Product principles

1. **Gaming first:** Gaming setup must be clearer than a general-purpose Linux distribution.
2. **Stable by design:** Use Bazzite’s atomic image, tested NVIDIA stack and rollback model.
3. **Upstream aligned:** Extend Bazzite rather than replacing its core.
4. **Safe defaults:** No automatic overclocking, unsafe kernel tweaks or random optimisation scripts.
5. **Reversible changes:** Users must be able to undo system changes.
6. **Low terminal dependence:** Routine gaming setup must be possible through the graphical interface.
7. **Transparent compatibility:** Arcalium must clearly explain when a game, anti-cheat system or launcher may not work on Linux.
8. **Privacy:** No Arcalium telemetry by default.
9. **Open maintenance:** Build instructions, source changes, licences and release notes must be visible.
10. **Hardware-aware:** Only show controls that are relevant and supported on the detected hardware.

---

# 3. Platform Decision

## 3.1 Base platform

Arcalium OS NVIDIA Edition will derive from:

```dockerfile
FROM ghcr.io/ublue-os/bazzite-nvidia-open:stable
```

This is the modern NVIDIA Bazzite desktop image.

The first edition targets:

- NVIDIA GTX 16-series GPUs.
- NVIDIA RTX-series GPUs.
- UEFI systems.
- Vulkan-capable gaming hardware.
- KDE Plasma.
- Wayland.

The RTX 2060 and RTX 3090 both fall within the modern RTX hardware target and will be supported by the same Arcalium NVIDIA image.

## 3.2 Why this base is being used

The Bazzite base already provides much of the difficult operating-system work:

- Fedora Atomic/bootc image foundation.
- NVIDIA drivers in the NVIDIA image.
- Gaming-oriented kernel and system integration.
- Steam and core gaming utilities.
- KDE Plasma desktop.
- Wayland.
- Vulkan stack.
- Flathub support.
- Bazaar app store.
- System image updates.
- Rollback deployments.
- Gaming overlays and supporting utilities.
- Controller and multimedia support inherited from Bazzite.
- Secure Boot support through the upstream signing arrangement.

Arcalium should add product experience, automation, diagnostics, configuration and branding rather than rebuilding the driver and gaming stack.

## 3.3 Edition matrix

### Version 1

```text
Arcalium OS NVIDIA Edition
Base: bazzite-nvidia-open
Desktop: KDE Plasma
Session: Wayland
Target: GTX 16 and all RTX GPUs
Mode: Desktop gaming
```

### Future version

```text
Arcalium OS AMD/Intel Edition
Base: bazzite
Desktop: KDE Plasma
Session: Wayland
Target: modern AMD and Intel graphics
Mode: Desktop gaming
```

### Possible future legacy edition

```text
Arcalium OS NVIDIA Legacy Edition
Base: bazzite-nvidia
Target: Pascal, Maxwell and Volta hardware
Status: Not part of version 1
```

## 3.4 Explicit exclusions from version 1

The first release must not attempt to include:

- Legacy NVIDIA GTX 900/1000 support in the modern image.
- Steam Gaming Mode as the default desktop.
- A SteamOS-style console session for NVIDIA.
- X11.
- Custom kernels.
- A custom NVIDIA driver installer.
- User-selectable NVIDIA driver versions.
- Automated GPU overclocking.
- Automated undervolting.
- Unsupported NTFS gaming-library workarounds.
- An independent Arch-style package repository.
- A complete fork of Bazzite.
- An Arcalium account system.
- Cloud telemetry.
- Paid services.
- A proprietary update server.

These can be reconsidered after the desktop NVIDIA edition is stable.

---

# 4. Target Users

## 4.1 Primary users

- Windows gamers considering Linux.
- Users who want Steam and Proton configured with minimal effort.
- NVIDIA desktop owners.
- Families setting up gaming PCs.
- Users who prefer a visual setup and recovery experience.
- Gamers who want an app store and common launchers available immediately.
- People who want system rollback when an update causes trouble.

## 4.2 User skill range

Arcalium must support:

- Beginner users who do not know Linux terminology.
- Intermediate PC gamers familiar with launchers and graphics settings.
- Advanced users who still want access to the terminal, containers and standard Bazzite tools.

## 4.3 Initial real-world test users

1. Primary test machine with RTX 3090.
2. Two family gaming systems using RTX 2060 GPUs.

These provide coverage for:

- Ampere architecture through the RTX 3090.
- Turing architecture through the RTX 2060.
- Higher-end and mid-range gaming hardware.
- Multiple independent installations.
- Repeatability of the installer and first-boot process.

---

# 5. Success Criteria

Arcalium OS NVIDIA Edition version 1 is successful when:

1. The ISO installs successfully on the RTX 3090 system.
2. The same ISO installs successfully on both RTX 2060 systems.
3. The installed system boots into KDE Plasma on Wayland.
4. The NVIDIA driver loads correctly without manual installation.
5. `nvidia-smi` works.
6. Vulkan is detected and passes a basic rendering test.
7. Steam launches.
8. A Windows game launches through Proton.
9. Proton-GE is installed or can be installed through one clearly labelled action.
10. Spotify is available after first-boot provisioning.
11. Bazaar can install and update Flatpak applications.
12. The user can install optional launchers from the Arcalium setup interface.
13. The user can detect and configure a secondary game drive safely.
14. The user can see the current OS deployment and access rollback guidance.
15. The first-boot wizard does not reappear after completion unless manually relaunched.
16. Failed first-boot actions can be retried individually.
17. An update can be applied and the previous deployment remains bootable.
18. The ISO and image are signed and checksummed.
19. No feature requires disabling SELinux.
20. No routine gaming task requires direct package layering.
21. The system remains rebased to the Arcalium image after update.
22. Arcalium changes survive image upgrades.
23. A clean reinstall produces the same expected state.
24. The system can generate a support bundle with private data excluded by default.
25. All third-party software and trademarks are documented accurately.

---

# 6. User Experience Overview

## 6.1 Installation experience

The installer should remain as close as practical to the supported Bazzite/bootc installer.

Arcalium should customise:

- Product name.
- Logo.
- Installer artwork where supported.
- Default hostname suggestion.
- Welcome text.
- Release information.
- Links to documentation and support.

Arcalium must not maintain a completely custom installer during version 1 unless upstream installer customisation proves insufficient.

## 6.2 First boot

On first successful desktop login, launch **Arcalium Setup**.

The wizard must guide the user through:

1. Welcome and important notices.
2. Hardware validation.
3. Display and audio checks.
4. System update check.
5. Gaming application selection.
6. Proton-GE setup.
7. Steam launch and sign-in.
8. Game-storage setup.
9. ProtonVPN setup.
10. Optional game-streaming setup.
11. Final system validation.
12. Optional Local AI assistant (install or skip).
13. Completion and handoff to Arcalium Control Centre.

## 6.3 Daily use

After setup, users should use **Arcalium Control Centre** for:

- Hardware status.
- Driver checks.
- Vulkan checks.
- Launchers and gaming apps.
- Proton compatibility tools.
- Storage.
- VPN.
- Streaming.
- Controllers and peripherals.
- Updates and rollback.
- Diagnostics.
- Offline local AI assistant (optional, session-based).
- Documentation.

---

# 7. Core Applications and Provisioning

## 7.1 Required components

The completed NVIDIA installation must provide:

- Steam through the Bazzite base, subject to the release licensing gate.
- Bazaar app store.
- Spotify.
- ProtonPlus.
- Proton-GE.
- Arcalium Setup.
- Arcalium Control Centre.
- Arcalium CLI.
- NVIDIA and Vulkan diagnostics.
- Update and rollback access.
- ProtonVPN setup support.

## 7.2 Default optional application catalogue

The first-boot wizard should offer grouped optional applications.

### Game launchers

- Heroic Games Launcher (Epic, GOG, Amazon — replaces Lutris in the Arcalium catalogue).
- Bottles.
- Prism Launcher.
- itch.io launcher where a suitable maintained package exists.

Do **not** offer Lutris. Heroic covers the non-Steam store role; bundling both would duplicate that surface.

### Communication

- Discord.
- Vesktop as an alternative to Discord.
- Telegram where desired.

### Streaming and recording

- OBS Studio.
- Sunshine.
- Moonlight.
- Steam Remote Play guidance.

### Compatibility and management

- ProtonPlus.
- Protontricks.
- Flatseal.
- Warehouse.

### Emulation

Do not enable emulation packages by default in the first alpha. Add an optional section later for:

- RetroArch.
- EmulationStation Desktop Edition.
- Dolphin.
- PCSX2.
- RPCS3.
- Steam ROM Manager.

Arcalium must not distribute copyrighted ROMs, BIOS files, keys or game content.

## 7.3 Flatpak policy

Graphical third-party applications should use Flatpak wherever practical.

Requirements:

- Use Flathub as the default source.
- Store application IDs in one declarative manifest.
- Separate required and optional Flatpaks.
- Make installation resumable.
- Display installation progress.
- Record success or failure per application.
- Never treat a partial installation as complete.
- Let the user retry.
- Do not layer ordinary desktop apps into the immutable image.
- Do not silently add untrusted Flatpak remotes.

Initial expected IDs must be verified before implementation. Candidate IDs include:

```text
Spotify: com.spotify.Client
ProtonPlus: com.vysp3r.ProtonPlus
Heroic: com.heroicgameslauncher.hgl
Bottles: com.usebottles.bottles
Discord: com.discordapp.Discord
Vesktop: dev.vencord.Vesktop
Protontricks: com.github.Matoking.protontricks
Flatseal: com.github.tchx84.Flatseal
```

Cursor must validate every ID against Flathub before committing the manifest.

## 7.4 Spotify policy

Spotify should be installed through Flatpak.

The UI and documentation must disclose when the Flatpak is community-maintained rather than officially supported by Spotify.

Failure to install Spotify must not block completion of first boot.

## 7.5 ProtonVPN policy

Arcalium must provide ProtonVPN support, but must not pretend an unofficial client is official.

The Control Centre should provide two methods:

### Recommended method

Import ProtonVPN WireGuard or OpenVPN configuration into NetworkManager.

Features:

- Select a configuration file.
- Explain where the user obtains it.
- Import it through the supported desktop networking stack.
- Show the resulting connection.
- Allow connect and disconnect.
- Provide a DNS leak-test link or explanation without collecting data.
- Warn that advanced ProtonVPN application features may not be available.

### Optional GUI-client method

Offer installation of the currently maintained ProtonVPN Flatpak only after displaying:

- Whether it is official or unofficial.
- Its source.
- Its permissions.
- That VPN clients can be limited by Flatpak sandboxing.
- A clear uninstall action.

Do not bake an unofficial ProtonVPN application into the immutable base image.

## 7.6 Proton-GE policy

Arcalium must make Proton-GE available without requiring terminal commands.

Preferred version 1 implementation:

1. Include ProtonPlus by default.
2. Add an Arcalium action called **Install recommended Proton-GE**.
3. The action resolves a tested Proton-GE version from an Arcalium release manifest.
4. The user can install it into the correct Steam compatibility-tools directory.
5. Steam is restarted or the user is told to restart it.
6. The Control Centre confirms that the compatibility tool is visible.
7. ProtonPlus remains available for later updates and additional compatibility tools.

Optional release enhancement:

- Bundle one tested Proton-GE archive in the ISO for offline installation.
- Keep the archive version in a build variable.
- Verify the upstream checksum during CI.
- Include all required licence notices.
- Install it into the user profile during first boot.
- Never overwrite a newer user-installed version.

Do not automatically set Proton-GE for every game. Steam’s default Proton version should remain the default unless the user chooses otherwise.

---

# 8. Arcalium Setup Wizard

## 8.1 Technology

The setup wizard and Control Centre should share one codebase.

Recommended stack:

- Tauri.
- React.
- TypeScript.
- Vite.
- Rust backend.
- Accessible HTML/CSS UI.
- KDE-friendly desktop integration.

The exact current stable toolchain must be pinned by the repository lockfiles.

## 8.2 First-run detection

Create a per-user completion marker:

```text
~/.config/arcalium/setup-complete.json
```

Example structure:

```json
{
  "schemaVersion": 1,
  "completed": true,
  "completedAt": "ISO-8601 timestamp",
  "imageVersion": "Arcalium image version",
  "steps": {
    "hardware": "complete",
    "updates": "complete",
    "applications": "complete",
    "protonGe": "complete",
    "storage": "skipped",
    "vpn": "skipped",
    "streaming": "skipped",
    "localAi": "skipped"
  }
}
```

The wizard should launch through a systemd user service or supported desktop autostart entry.

Rules:

- Launch once per user.
- Do not launch during the installer environment.
- Do not launch before a usable desktop session exists.
- Do not launch repeatedly after a crash.
- Preserve partial progress.
- Provide a **Resume setup** launcher.
- Provide a **Restart setup** action with confirmation.
- Never require root privileges for the whole application.

## 8.3 Wizard pages

### Page 1 — Welcome

Show:

- Arcalium identity.
- NVIDIA Edition.
- Short explanation.
- Independent-project notice.
- Privacy statement.
- Internet requirement for optional applications.
- Button to begin.

### Page 2 — Hardware scan

Detect:

- CPU model.
- Total RAM.
- GPU model.
- GPU PCI ID.
- NVIDIA driver version.
- Kernel version.
- Current image name and version.
- Session type.
- Vulkan version.
- Display resolution and refresh rate.
- Storage devices.
- Network availability.

Results should be shown as:

- Ready.
- Warning.
- Unsupported.
- Unknown.

Do not display a green “ready” result unless the underlying check actually passed.

### Page 3 — NVIDIA validation

Run allowlisted checks:

- Confirm an RTX or GTX 16-series GPU.
- Confirm the NVIDIA kernel modules are loaded.
- Confirm `nvidia-smi` returns successfully.
- Confirm Vulkan sees the NVIDIA GPU.
- Confirm the desktop is running on Wayland.
- Detect hybrid graphics on laptops.
- Detect software rendering.
- Detect nouveau/NVK being used unexpectedly for the intended proprietary/open-kernel-module image.
- Detect common multi-GPU situations.

Provide a support-bundle option when validation fails.

### Page 4 — Display and audio

Provide links or launchers to the supported KDE settings pages for:

- Resolution.
- Refresh rate.
- Scaling.
- Primary display.
- VRR where supported.
- HDR where supported.
- Audio output.
- Microphone input.

Do not implement a duplicate display-control system in version 1.

### Page 5 — Updates

Show:

- Current image.
- Current version.
- Whether an update is available.
- Last update check.
- Current channel.

Actions:

- Check for updates.
- Apply update.
- Restart later.
- View release notes.

Do not interrupt setup if updates are unavailable due to network failure.

### Page 6 — Gaming applications

Show required and optional apps in clear groups.

Required selections should be preselected where licensing permits.

Each application card should show:

- Name.
- Purpose.
- Source.
- Download size when available.
- Whether it is already installed.
- Install status.
- Uninstall link after installation.

### Page 7 — Proton-GE

Explain:

- What Proton is.
- What Proton-GE is.
- That it is useful for specific games but should not automatically replace the default for everything.

Actions:

- Install recommended Proton-GE.
- Open ProtonPlus.
- Skip.

### Page 8 — Steam

Actions:

- Launch Steam.
- Confirm Steam is installed.
- Open Steam compatibility settings guidance.
- Explain that a Steam account is required.
- Explain that Windows-game compatibility varies.

Do not capture, proxy or store Steam credentials.

### Page 9 — Game storage

Detect:

- Internal drives.
- External drives.
- Filesystem.
- Mount state.
- Existing Steam library paths.
- Free space.

Actions:

- Use an existing Btrfs or Ext4 location.
- Create a Steam library folder.
- Open KDE Partition Manager or the supported disk utility.
- Explain how to add the folder in Steam.
- Show a prominent warning for NTFS, exFAT and FAT32.
- Offer no “force unsupported mode” button in the beginner workflow.

Any formatting action must:

- Require explicit drive selection.
- Display the model, serial fragment, size and existing filesystem.
- Require a typed confirmation.
- Explain that data will be destroyed.
- Never select a drive automatically.
- Never format the current system disk from the Control Centre.

### Page 10 — ProtonVPN

Offer:

- Import WireGuard configuration.
- Import OpenVPN configuration.
- Install optional GUI client with disclosure.
- Skip.

### Page 11 — Game streaming

Offer:

- Sunshine.
- Moonlight.
- Steam Remote Play guidance.
- Skip.

Do not enable remote access without explicit user action.

### Page 12 — Final validation

Run:

- Image status.
- NVIDIA driver.
- Vulkan.
- Steam.
- Proton-GE.
- App provisioning.
- Storage.
- Update service.
- Internet.
- Audio device presence.
- Controller presence if connected.

Display:

- Ready to game.
- Ready with warnings.
- Action required.

### Page 13 — Local AI assistant

Optional offline maintenance helper (Ollama + pinned `gemma4:e4b-it-qat`).

Show:

- Ollama and model status.
- Clear size / VRAM / gaming coexistence warnings (~10 GB pull; unload before gaming).
- **Install Ollama** — performs a non-interactive, user-level Homebrew install; no terminal copy/paste or sudo.
- **Pull and configure model** — starts the local Ollama server, pulls the pinned base model, and creates `arcalium-assistant` with the system prompt.
- Optional **Try assistant** (terminal session) after the model is ready.
- **Skip** — finish setup without Local AI; can configure later in Control Centre.
- **Continue** — mark the step complete without requiring a successful install.

Do not force the model pull for every user. Do not block completion if the user skips.

### Page 14 — Completion

Show:

- Open Steam.
- Open Arcalium Control Centre.
- Open Bazaar.
- View gaming compatibility guidance.
- View known limitations.
- Finish.

---

# 9. Arcalium Control Centre

## 9.1 Purpose

The Control Centre is Arcalium’s main differentiating application.

It should convert common Linux gaming setup and troubleshooting tasks into clear, safe workflows.

## 9.2 Navigation

The application should contain:

1. Overview.
2. Gaming.
3. Compatibility.
4. GPU and Display.
5. Applications.
6. Storage.
7. Network and VPN.
8. Controllers and Peripherals.
9. Streaming.
10. Updates and Recovery.
11. Diagnostics.
12. Local AI Assistant.
13. Settings.
14. About.

## 9.3 Overview dashboard

Show:

- Arcalium version.
- Update state.
- GPU.
- NVIDIA driver version.
- Vulkan status.
- CPU.
- RAM.
- Main storage free space.
- Game-storage free space.
- Steam state.
- Proton-GE state.
- VPN state.
- Controller state.
- Current warnings.

Quick actions:

- Launch Steam.
- Open Bazaar.
- Install Proton-GE.
- Add game drive.
- Check updates.
- Run gaming health check.

## 9.4 Gaming page

Show installed launchers and actions for:

- Steam.
- Heroic.
- Bottles.
- Prism Launcher.
- Other supported launchers.

Lutris is out of scope (Heroic is the non-Steam launcher).

Functions:

- Launch.
- Install.
- Uninstall.
- Repair permissions where a documented fix exists.
- Open data folder.
- Open relevant documentation.

Do not modify launcher configuration files without backups.

## 9.5 Compatibility page

Version 1 functions:

- Show installed Proton versions.
- Open ProtonPlus.
- Install the recommended Proton-GE version.
- Open Protontricks.
- Explain Steam per-game compatibility selection.
- Link to ProtonDB.
- Link to anti-cheat compatibility information.
- Explain common game categories:
  - Native Linux.
  - Proton-compatible.
  - Works with adjustments.
  - Blocked by anti-cheat.
  - Unsupported.

Future enhancement:

- Search game compatibility inside the Control Centre.
- Only implement after reviewing ProtonDB and other service terms and APIs.
- Cache results responsibly.
- Clearly label community reports.

## 9.6 GPU and Display page

Show:

- GPU model.
- GPU architecture when detectable.
- Driver version.
- Kernel module.
- VRAM.
- GPU utilisation.
- Temperature.
- Power use where available.
- Vulkan version.
- Active displays.
- Current refresh rate.
- Wayland session.
- VRR support status.
- HDR support status.
- Hardware encoding availability.

Actions:

- Copy GPU report.
- Open NVIDIA settings if suitable in the current Wayland environment.
- Open KDE display settings.
- Run Vulkan test.
- Run hardware-encoding test.
- Open known NVIDIA limitations.

Do not provide automatic overclocking in version 1.

## 9.7 Applications page

Use a declarative application catalogue.

Each entry should contain:

```json
{
  "id": "spotify",
  "name": "Spotify",
  "type": "flatpak",
  "sourceId": "com.spotify.Client",
  "required": false,
  "category": "media",
  "licenceNotice": "Community package",
  "website": "",
  "supported": true
}
```

The UI should read the catalogue rather than hardcoding every card.

## 9.8 Storage page

Show:

- Drives.
- Filesystems.
- Mount points.
- Capacity.
- Free space.
- SMART state when safely available.
- Steam libraries.
- Unsupported filesystem warnings.

Actions:

- Create library folder.
- Open Steam storage settings.
- Open disk utility.
- Mount supported drive.
- Copy diagnostic information.
- Explain migration from NTFS.

Do not automatically move game libraries in version 1.

## 9.9 Network and VPN page

Show:

- Active connection.
- Local IP.
- Internet state.
- VPN state.
- Current DNS servers where available.
- Optional latency test.

Actions:

- Open KDE network settings.
- Import VPN configuration.
- Install or open ProtonVPN client.
- Disconnect VPN.
- Test latency with and without VPN.

Do not claim a VPN improves game performance.

## 9.10 Controllers and peripherals page

Version 1:

- Detect connected controllers.
- Show device name and connection type.
- Link to Steam Input settings.
- Show Bluetooth settings.
- Detect common Xbox, PlayStation and generic controllers.
- Show basic troubleshooting.
- Provide a controller-input test if practical.

Future:

- OpenRGB integration.
- Razer integration.
- Fan-control integration.
- Per-device profiles.

Hardware-control integrations must remain optional and must not be included until tested.

## 9.11 Streaming page

Functions:

- Install Sunshine.
- Launch Sunshine.
- Explain firewall implications.
- Install Moonlight.
- Open Steam Remote Play settings.
- Show host IP.
- Disable streaming services.

Remote streaming must be opt-in.

## 9.12 Updates and Recovery page

Show:

- Current deployment.
- Previous deployment.
- Current image.
- Current tag/channel.
- Pending update.
- Last successful update.
- Pinned deployment state.

Actions:

- Check updates.
- Apply update.
- Reboot.
- View change log.
- Explain rollback.
- Pin current known-good deployment where supported.
- Launch rollback helper.
- Generate pre-update diagnostics.

Do not hide the fact that rollback changes the operating-system deployment but does not restore user files.

## 9.13 Diagnostics page

Health checks:

- Image identity.
- Bootc status.
- Kernel.
- NVIDIA modules.
- NVIDIA driver.
- `nvidia-smi`.
- Vulkan.
- OpenGL.
- Wayland.
- Steam.
- Flatpak.
- Proton-GE.
- Storage.
- Network.
- Audio.
- Controllers.
- Update services.
- Secure Boot state.
- SELinux state.

Support bundle contents:

- Arcalium version.
- Image digest.
- Hardware summary.
- Driver information.
- Relevant service statuses.
- Recent Arcalium logs.
- Failed setup actions.
- Redacted storage layout.
- Redacted network state.

Excluded by default:

- Usernames.
- Home-directory file names.
- Browser history.
- Steam credentials or tokens.
- VPN credentials.
- Wi-Fi passwords.
- Exact public IP.
- Personal documents.
- Full serial numbers.

The user must preview the bundle before exporting it.

## 9.14 Local AI Assistant page

Arcalium may include an **optional offline local AI assistant** for system-maintenance questions and troubleshooting guidance. It is a helper for interpreting diagnostics, updates, storage, drivers, and common Linux gaming issues — not a cloud chatbot and not a substitute for the Diagnostics support bundle.

### Purpose

- Answer maintenance and “what should I try next?” questions using local context where practical (for example: recent `arcaliumctl` health summaries, Arcalium docs excerpts, and redacted system facts the user opts to attach).
- Keep all inference on-device once the model is installed.
- Stay compatible with a gaming-first desktop: the model must not remain resident in GPU memory after the user finishes.

### Runtime and model

- Runtime: **Ollama** (local API / CLI).
- Base weights: **`gemma4:e4b-it-qat`** (Gemma 4 E4B instruction-tuned, QAT). Pin this tag in scripts; do not silently float to a larger or different tag.
- Session model: **`arcalium-assistant`**, created from the base via Modelfile with a fixed **Arcalium system prompt** (`/usr/lib/arcalium/ai/system-prompt.txt`) so replies assume Arcalium OS NVIDIA Edition (Bazzite/bootc), KDE Plasma, and **bash** — never Windows PowerShell/cmd or apt/pacman unless the user asks about another OS.
- First use may require a one-time model pull (~10 GB class). Do not force the pull during first-boot for every user; offer it from Control Centre with clear size, VRAM, and disk warnings.
- Offline after install: no Arcalium cloud endpoint, no third-party chat API, and no prompt/response telemetry.

### Control Centre launch behaviour

The Local AI Assistant page (and an optional Diagnostics quick action) must:

1. Show Ollama / model status (installed, pulling, ready, busy, error).
2. Offer **Launch assistant** as the primary action.
3. Open a **terminal session** (system terminal, e.g. Konsole) that runs an Arcalium-managed chat wrapper — not a permanent background GUI that keeps weights loaded.
4. On session start, load `arcalium-assistant` (system-prompted) for interactive use.
5. On terminal close / session exit (including Ctrl+C / shell exit), **unload the model** so GPU VRAM is freed for gaming (for example `ollama stop arcalium-assistant` / base tag and/or keep-alive zero for that run). Closing the terminal is the intended “I’m done — free the GPU” gesture.
6. Surface a clear notice before launch: gaming and the assistant should not share the GPU while the model is loaded; close the assistant terminal before launching demanding games.

### Non-goals for version 1 of this feature

- Always-on tray / daemon chat that keeps the model warm in VRAM.
- Automatic silent model upgrades to larger Gemma tags.
- Sending chat content off-device.
- Replacing Polkit, `bootc`, or privileged repair with AI-executed shell commands. The assistant may suggest commands; the user (or allowlisted `arcaliumctl`) executes them.

### Acceptance

- Assistant launches from Control Centre into a terminal.
- Chat works offline after the model is present and uses the Arcalium system prompt (Linux/bash/bootc context).
- Closing the terminal unloads the assistant/base models and returns the GPU to a gaming-usable free-VRAM state without a reboot.
- Failure modes (missing Ollama, pull incomplete, insufficient VRAM/disk) are explained in plain language with a retry path.

---

# 10. Backend Command Architecture

## 10.1 CLI

Create:

```text
/usr/bin/arcaliumctl
```

The UI must call `arcaliumctl` rather than constructing arbitrary shell commands.

Example interface:

```bash
arcaliumctl system summary --json
arcaliumctl gpu status --json
arcaliumctl gpu validate --json
arcaliumctl vulkan test --json
arcaliumctl apps list --json
arcaliumctl apps install spotify --json
arcaliumctl proton list --json
arcaliumctl proton install-recommended --json
arcaliumctl storage scan --json
arcaliumctl vpn import /path/to/config --json
arcaliumctl updates status --json
arcaliumctl diagnostics create --output /path/to/file
arcaliumctl ai status --json
arcaliumctl ai install-ollama --json
arcaliumctl ai ensure --json
arcaliumctl ai launch
arcaliumctl ai stop --json
```

`arcaliumctl ai launch` must open the terminal session described in §9.14 and guarantee model unload on exit. `arcaliumctl ai stop` must force-unload if a previous session left the model resident.

## 10.2 Command rules

- Every command must return a stable JSON schema.
- Human-readable terminal output may be added, but JSON is required for the UI.
- Exit code `0` means success.
- Non-zero exit codes must map to documented error types.
- Timeouts must be defined.
- Long-running actions must emit progress.
- User cancellation must be supported where safe.
- No command may execute user-provided shell fragments.
- File paths must be validated and canonicalised.
- Privileged commands must use a narrow, audited path.
- Do not run the entire GUI as root.

## 10.3 Privileged operations

Use one of these approaches after evaluation:

1. A minimal Polkit-authorised helper.
2. Approved `ujust` recipes invoked through an allowlisted wrapper.
3. A small D-Bus service with explicit methods.

Preferred long-term approach:

- Unprivileged Tauri frontend.
- Rust command layer.
- Minimal privileged helper.
- Polkit action definitions.
- No general-purpose privileged shell.

## 10.4 Logging

Write user-level logs to:

```text
~/.local/state/arcalium/
```

Use the journal for system services.

Log:

- Action name.
- Start time.
- End time.
- Result.
- Error code.
- Redacted diagnostic details.

Never log passwords, authentication tokens or VPN secrets.

---

# 11. Branding and Desktop Experience

## 11.1 Required branding

- Arcalium logo.
- Arcalium wallpaper.
- Lock-screen wallpaper.
- Installer branding where supported.
- Boot splash where safely customisable.
- Application launcher icon.
- About page.
- Release channel and version.
- Support and documentation links.

## 11.2 KDE defaults

Arcalium should provide a polished but conservative KDE layout.

Suggested defaults:

- Bottom panel.
- Application launcher at left.
- Pinned Steam.
- Pinned Bazaar.
- Pinned Arcalium Control Centre.
- System tray.
- Update visibility.
- Dark theme by default.
- Sensible scaling.
- No forced desktop widgets.
- No destructive removal of KDE functionality.

User changes must not be overwritten by updates.

Use skeleton defaults only for new users. Never reapply the full desktop layout on every boot.

## 11.3 Naming rules

Use **Arcalium OS** in product-facing UI.

Use **Bazzite-based** or **built on Bazzite** in legal/about documentation.

Do not represent Arcalium as:

- Officially endorsed by Bazzite.
- Officially endorsed by Universal Blue.
- Officially endorsed by Valve.
- Officially endorsed by NVIDIA.
- Officially endorsed by Spotify.
- Officially endorsed by Proton.

---

# 12. Repository Architecture

Start from the current official Universal Blue `image-template`.

Suggested repository:

```text
arcalium-os/
├── .github/
│   ├── workflows/
│   │   ├── build.yml
│   │   ├── build-disk.yml
│   │   ├── checks.yml
│   │   ├── control-centre.yml
│   │   └── release.yml
│   └── dependabot.yml or renovate configuration
├── apps/
│   └── control-centre/
│       ├── src/
│       ├── src-tauri/
│       ├── public/
│       ├── package.json
│       ├── Cargo.toml
│       └── tests/
├── build_files/
│   ├── build.sh
│   ├── install-arcalium.sh
│   ├── install-branding.sh
│   ├── install-control-centre.sh
│   ├── install-cli.sh
│   ├── install-flatpak-manifest.sh
│   └── validate-image.sh
├── config/
│   ├── applications.json
│   ├── proton.json
│   ├── diagnostics.json
│   └── release.json
├── disk_config/
│   ├── iso.toml
│   └── disk.toml
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── IMPLEMENTATION_STATUS.md
│   ├── ARCHITECTURE.md
│   ├── BUILDING.md
│   ├── TESTING.md
│   ├── RELEASE.md
│   ├── LICENSING.md
│   ├── PRIVACY.md
│   ├── KNOWN_LIMITATIONS.md
│   └── SUPPORT_BUNDLE.md
├── system_files/
│   ├── etc/
│   │   ├── polkit-1/
│   │   ├── systemd/
│   │   └── arcalium/
│   └── usr/
│       ├── bin/
│       │   └── arcaliumctl
│       ├── lib/
│       │   └── arcalium/
│       └── share/
│           ├── applications/
│           ├── arcalium/
│           ├── backgrounds/
│           ├── icons/
│           └── metainfo/
├── tests/
│   ├── image/
│   ├── cli/
│   ├── integration/
│   └── vm/
├── Containerfile
├── image-template.env
├── cosign.pub
├── Justfile
├── LICENSE
└── README.md
```

Cursor must adjust paths to match the current upstream template instead of forcing this exact structure when the template has changed.

---

# 13. Container Image Build

## 13.1 Containerfile

Initial intent:

```dockerfile
FROM ghcr.io/ublue-os/bazzite-nvidia-open:stable
```

The Containerfile should:

1. Copy build files.
2. Install Arcalium system files.
3. Build or install the Control Centre package.
4. Install branding.
5. Install the Arcalium CLI.
6. Install declarative configuration.
7. Add first-boot integration.
8. Run validation.
9. Clean build-only files.
10. Add image labels.

Do not replace the Bazzite kernel or NVIDIA stack.

## 13.2 Image metadata

Set:

```text
IMAGE_NAME=arcalium-os-nvidia
IMAGE_DESC=Arcalium OS NVIDIA Edition
IMAGE_KEYWORDS=gaming,linux,bazzite,nvidia,bootc,kde,proton
DEFAULT_TAG=dev
```

Use the actual GitHub organisation or username for `REPO_ORGANIZATION`.

## 13.3 Tags and channels

Use:

```text
dev
testing
stable
versioned tags such as 0.1.0-alpha.1
date/build tags
```

Rules:

- `dev` builds from active development.
- `testing` is manually promoted after automated checks.
- `stable` is manually promoted after hardware validation.
- Do not build public stable tags directly from unreviewed commits.
- Record the resolved upstream base digest in each release.

## 13.4 Image signing

- Generate a Cosign key pair.
- Store the private key only in GitHub Actions secrets.
- Commit only the public key.
- Sign every published image.
- Verify the signature in CI.
- Document verification commands.
- Rotate keys through a documented process if compromised.

## 13.5 Reproducibility

- Pin GitHub Actions by commit SHA.
- Commit lockfiles.
- Record dependency versions.
- Generate an SBOM.
- Store image digest in release metadata.
- Store base-image digest in release metadata.
- Keep release build logs.
- Avoid downloading unsigned binaries during builds.
- Verify checksums for downloaded release archives.

---

# 14. ISO and Disk Image Build

Use the current `build-disk.yml` supplied by Universal Blue’s image template.

Expected outputs:

- Anaconda installer ISO.
- QCOW2 test image.
- Optional raw disk image later.
- SHA-256 checksum.
- Build metadata.

The current template may require creating `disk_config/iso.toml` from the KDE example. Cursor must inspect the version copied into the repository and ensure the workflow points to the real file.

The ISO configuration must reference:

```text
ghcr.io/<organisation>/arcalium-os-nvidia:<channel>
```

Release flow:

1. Build OCI image.
2. Sign OCI image.
3. Run image validation.
4. Build QCOW2.
5. Boot-test QCOW2.
6. Build ISO.
7. Generate checksum.
8. Publish private alpha artifact.
9. Test on RTX 3090.
10. Test on RTX 2060 system one.
11. Test on RTX 2060 system two.
12. Promote only after required results pass.

---

# 15. Updates and Rollback

## 15.1 Update model

Arcalium inherits the atomic image update model.

The operating system should update by receiving a new signed Arcalium image.

Flatpaks should update through the supported Bazzite update mechanism.

## 15.2 Requirements

- Users must not manually update NVIDIA drivers outside the image.
- Driver updates arrive with tested image updates.
- The previous deployment should remain available.
- The Control Centre should clearly distinguish:
  - Operating-system update.
  - Flatpak update.
  - Compatibility-tool update.
  - Application update.
- The UI must show when a reboot is required.
- Failed updates must not delete the known-good deployment.
- A recovery guide must exist before alpha release.

## 15.3 Rollback

The Control Centre should explain and expose supported rollback mechanisms.

Rollback acceptance test:

1. Install build A.
2. Update to build B.
3. Confirm B boots.
4. Roll back to A.
5. Confirm A boots.
6. Confirm user files remain.
7. Confirm the user can return to B or update forward.

Do not describe rollback as a backup of personal data.

---

# 16. Security

## 16.1 Baseline

- Keep SELinux enforcing.
- Keep Wayland.
- Keep the immutable/atomic system model.
- Do not expose a root shell through the UI.
- Use signed images.
- Verify downloaded artefacts.
- Use least privilege.
- Audit privileged helper code.
- Do not ship default passwords.
- Do not open network ports automatically.
- Do not enable SSH automatically.
- Do not enable Sunshine automatically.
- Do not weaken Secure Boot checks.

## 16.2 Secure Boot

Version 1 should follow the supported upstream Bazzite/Universal Blue process.

The setup wizard should detect Secure Boot state and link to accurate guidance.

Do not promise a custom Arcalium Secure Boot key until the complete boot chain has been implemented and tested.

## 16.3 Privacy

Arcalium telemetry is disabled because no telemetry service will exist in version 1.

The Control Centre may perform local diagnostics.

The optional Local AI Assistant (§9.14) must keep prompts and responses on-device. It must not upload chat content, attach full home-directory trees, or include secrets (VPN credentials, Steam tokens, Wi-Fi passwords) in model context by default.

Any future crash-report submission must be:

- Opt-in.
- Previewable.
- Redacted.
- Sent only after explicit confirmation.
- Documented in the privacy policy.

---

# 17. Licensing and Release Gates

## 17.1 Open-source compliance

Before public distribution:

- Preserve all required Bazzite and Universal Blue notices.
- Include Arcalium’s own licence.
- Include source code for Arcalium modifications.
- Include notices for included software.
- Include Proton-GE licence obligations if bundled.
- Include wallpaper, icon and font licensing records.
- Do not include assets without redistribution rights.

## 17.2 Steam release gate

Valve’s published Steam client terms prohibit redistribution or preinstallation without a separate licence.

Because the Bazzite base includes Steam, public Arcalium distribution requires a specific legal and project-policy review.

Before a public ISO:

- Determine whether Arcalium can lawfully redistribute the inherited Steam client.
- Seek Valve permission where required.
- Consult Bazzite/Universal Blue maintainers about their distribution model.
- Keep private test images private until this is resolved.
- If necessary, create a public-release variant that installs Steam only after the user accepts Valve’s terms.

This gate does not prevent private development and testing on personally controlled systems, but it must block a public commercial release until resolved.

## 17.3 Trademark rules

Use third-party names only to describe compatibility.

Include a statement similar to:

> Arcalium OS is an independent project built on Bazzite and is not affiliated with or endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite project.

Have final wording reviewed before release.

## 17.4 ProtonVPN and Spotify disclosures

- Mark the Spotify Flatpak appropriately if it is community-maintained.
- Mark an unofficial ProtonVPN Flatpak as unofficial.
- Do not use third-party logos in ways their trademark policies prohibit.
- Prefer user-installed applications over rebundled binaries when rights are unclear.

---

# 18. NVIDIA Test Plan

## 18.1 Test system A — RTX 3090

Record:

- CPU.
- Motherboard.
- Firmware version.
- RAM.
- Storage.
- Display configuration.
- Refresh rate.
- Secure Boot state.
- Network hardware.
- Controller hardware.
- Audio hardware.

Tests:

1. ISO boots.
2. Installer displays correctly.
3. Installation completes.
4. First boot completes.
5. Wayland session.
6. NVIDIA driver loads.
7. `nvidia-smi` succeeds.
8. Vulkan sees RTX 3090.
9. Hardware decoding works.
10. Hardware encoding works.
11. Steam launches.
12. Native Linux game launches.
13. Proton DX11 game launches.
14. Proton DX12 game launches.
15. Proton-GE game launches.
16. Fullscreen works.
17. Multi-monitor works if present.
18. High-refresh-rate mode works if present.
19. VRR works if supported by display.
20. HDR is tested if supported.
21. Suspend and resume.
22. Shutdown and reboot.
23. System update.
24. Rollback.
25. Secondary game drive.
26. Spotify.
27. VPN import.
28. Controller.
29. Sunshine, if selected.
30. Support bundle.

## 18.2 Test systems B and C — RTX 2060

Repeat the same core tests on both systems.

Additional emphasis:

- 1080p and/or 1440p performance.
- Turing open-kernel-module compatibility.
- Older motherboard firmware.
- Different displays.
- Different controllers.
- Wi-Fi and Ethernet differences.
- Reproducibility of first-boot provisioning.
- Family-user usability without terminal intervention.

## 18.3 Gaming test categories

Use games legally owned by the testers.

Test at least:

- One native Linux game.
- One DX11 Windows game through Proton.
- One DX12 Windows game through Proton.
- One game known to benefit from Proton-GE.
- One controller-focused game.
- One multiplayer game whose anti-cheat supports Linux/Proton.
- One game with an external launcher.
- One game installed on a secondary Btrfs or Ext4 drive.

Record:

- Game.
- Store.
- Proton version.
- Launch options.
- Resolution.
- Result.
- Known issue.
- Workaround.
- GPU.
- Arcalium build.

Do not claim universal game compatibility from this test set.

---

# 19. Automated Testing

## 19.1 Static checks

- ShellCheck.
- shfmt.
- JSON validation.
- TOML validation.
- YAML validation.
- Rust formatting.
- Rust clippy.
- Rust tests.
- TypeScript lint.
- TypeScript type check.
- Frontend tests.
- Licence-file presence.
- Forbidden-secrets scan.
- Flatpak ID validation where possible.

## 19.2 Image checks

After building the OCI image, verify:

- Correct base.
- Correct image name.
- Required files exist.
- `arcaliumctl` is executable.
- Desktop entry exists.
- First-boot unit exists.
- Required configuration parses.
- No build secret is present.
- No private Cosign key is present.
- SELinux remains enabled.
- Expected app manifests exist.
- Image labels are correct.
- Control Centre starts in a container-safe smoke test where practical.

## 19.3 VM checks

Use QCOW2 for:

- Boot.
- Installer smoke test where possible.
- Desktop login.
- First-boot wizard.
- Branding.
- Application UI.
- Update status.
- Support-bundle generation.

GPU functionality cannot be accepted solely from VM tests.

---

# 20. Delivery Phases

## Phase 0 — Repository and research

Deliverables:

- Repository created from current `ublue-os/image-template`.
- `PRODUCT_SPEC.md`.
- `IMPLEMENTATION_STATUS.md`.
- Licence inventory.
- Confirmed image tag.
- Confirmed build workflow.
- Cosign setup.
- Private GHCR image.

Acceptance:

- Unmodified derived image builds.
- Image signature verifies.
- Test machine can switch to the image or a QCOW2 can boot.

## Phase 1 — Minimal Arcalium NVIDIA image

Deliverables:

- NVIDIA-open Bazzite base.
- Arcalium image metadata.
- Basic branding.
- Arcalium wallpaper.
- Control Centre placeholder.
- First-boot placeholder.
- ISO and QCOW2 workflow.

Acceptance:

- OCI image builds.
- QCOW2 boots.
- ISO installs.
- RTX 3090 boots.
- RTX 2060 boots.

## Phase 2 — Hardware validation

Deliverables:

- `arcaliumctl system summary`.
- `arcaliumctl gpu status`.
- NVIDIA validation.
- Vulkan validation.
- Wayland validation.
- Diagnostics JSON schemas.

Acceptance:

- Accurate results on RTX 3090.
- Accurate results on both RTX 2060 systems.
- Failure states are distinguishable.
- No arbitrary command execution.

## Phase 3 — Setup wizard

Deliverables:

- First-run service.
- Resume state.
- Hardware page.
- Update page.
- App selection.
- Proton-GE page.
- Storage page.
- VPN page.
- Completion page.

Acceptance:

- Runs once.
- Can resume after failure.
- Can be relaunched manually.
- Does not require running the GUI as root.

## Phase 4 — Application provisioning

Deliverables:

- Declarative app catalogue.
- Spotify.
- ProtonPlus.
- Optional launchers.
- Progress and retry.
- Uninstall path.
- Source disclosures.

Acceptance:

- Apps install on all three systems.
- Partial failure does not break setup.
- Re-running is idempotent.

## Phase 5 — Proton-GE

Deliverables:

- Recommended-version manifest.
- Installation action.
- Detection.
- Steam restart guidance.
- ProtonPlus integration.

Acceptance:

- Proton-GE is visible to Steam.
- A selected test game runs.
- Existing newer versions are not overwritten.

## Phase 6 — Storage and VPN

Deliverables:

- Drive scan.
- Filesystem warnings.
- Steam-library guidance.
- ProtonVPN configuration import.
- Optional client disclosure flow.

Acceptance:

- Btrfs or Ext4 game drive works.
- NTFS receives a warning.
- No drive is formatted accidentally.
- VPN configuration imports successfully.

## Phase 7 — Control Centre completion

Deliverables:

- All version 1 pages.
- Update and recovery.
- Diagnostics bundle.
- Streaming setup.
- Controller detection.
- About and licences.
- Optional Local AI Assistant page (§9.14) may ship in this phase or immediately after private-alpha Control Centre polish; it must not block gaming or Diagnostics acceptance.

Acceptance:

- No routine feature requires terminal use, except the Local AI Assistant, which intentionally uses a terminal session so closing it unloads the GPU-resident model.
- Privileged operations are narrow and audited.
- Support bundle is redacted.

## Phase 8 — Private alpha

Deliverables:

- Version `0.1.0-alpha.1`.
- Signed image.
- ISO.
- QCOW2.
- SHA-256 checksum.
- SBOM.
- Release notes.
- Known limitations.
- Test report.

Acceptance:

- Required test matrix passes on RTX 3090 and both RTX 2060 systems.
- Update and rollback pass.
- Clean installation is repeatable.

## Phase 9 — Public-release preparation

Deliverables:

- Steam licensing decision.
- Trademark review.
- Third-party notices.
- Privacy policy.
- Support process.
- Download page.
- Signed stable release.

This phase is blocked until licensing gates are satisfied.

## Phase 10 — AMD/Intel edition

Create:

```dockerfile
FROM ghcr.io/ublue-os/bazzite:stable
```

Share:

- Branding.
- Control Centre.
- First-boot wizard.
- Application manifests.
- Storage.
- VPN.
- Updates.
- Diagnostics.

Replace NVIDIA-specific checks with a GPU-provider abstraction.

---

# 21. GPU Provider Abstraction

Although NVIDIA is first, the Control Centre must not hardcode every feature around NVIDIA.

Create a provider interface:

```text
GpuProvider
├── identify()
├── driverStatus()
├── vulkanStatus()
├── telemetry()
├── displayCapabilities()
├── encoderStatus()
├── healthCheck()
└── supportBundle()
```

Initial implementation:

```text
NvidiaGpuProvider
```

Future implementations:

```text
AmdGpuProvider
IntelGpuProvider
```

Common UI components should consume provider-neutral data.

Example result:

```json
{
  "vendor": "nvidia",
  "model": "NVIDIA GeForce RTX 3090",
  "driver": {
    "loaded": true,
    "version": "detected version",
    "module": "nvidia"
  },
  "vulkan": {
    "available": true,
    "version": "detected version",
    "device": "NVIDIA GeForce RTX 3090"
  },
  "session": {
    "type": "wayland"
  },
  "health": "ready",
  "warnings": []
}
```

---

# 22. Error Handling

Every user-facing error must include:

- What failed.
- Whether the system is still safe.
- What the user can retry.
- What logs are available.
- A copyable error code.
- A support-bundle action when appropriate.

Example error categories:

```text
ARC-IMG-001 Incorrect image
ARC-GPU-001 NVIDIA GPU not detected
ARC-GPU-002 NVIDIA module not loaded
ARC-GPU-003 Software rendering detected
ARC-VLK-001 Vulkan unavailable
ARC-FPK-001 Flathub unavailable
ARC-FPK-002 Application install failed
ARC-PRT-001 Proton-GE download failed
ARC-PRT-002 Proton-GE install failed
ARC-STO-001 Unsupported filesystem
ARC-STO-002 Unsafe disk operation blocked
ARC-VPN-001 Invalid VPN configuration
ARC-UPD-001 Update check failed
ARC-DIA-001 Support bundle failed
```

Do not show raw stack traces as the primary message. Make them available under technical details.

---

# 23. Accessibility

- Keyboard-navigable setup and Control Centre.
- Visible focus indicators.
- Scalable text.
- High-contrast support.
- Screen-reader labels.
- Captions or text for any tutorial video.
- Do not rely on colour alone.
- Avoid timed steps.
- Persist progress.
- Use plain language first and technical details second.
- Support 125%, 150% and 200% display scaling.
- Ensure dialogs fit on 1080p displays.

---

# 24. Documentation

Required before private alpha:

- Installation guide.
- Secure Boot guide.
- Dual-boot guide.
- NVIDIA hardware support guide.
- First-boot guide.
- Steam and Proton guide.
- Proton-GE guide.
- Secondary-drive guide.
- NTFS migration warning.
- ProtonVPN guide.
- Update guide.
- Rollback guide.
- Diagnostics guide.
- Known limitations.
- Uninstall/rebase guide.
- Licence notices.

Documentation must use screenshots from Arcalium builds, not copied third-party screenshots without permission.

---

# 25. Known Limitations to Communicate

Version 1 must state clearly:

- Not every Windows game works on Linux.
- Some anti-cheat systems block Linux or Proton.
- Xbox PC Game Pass games cannot generally be installed locally as they are on Windows; cloud gaming may be an alternative.
- NVIDIA Steam Gaming Mode is not the version 1 target.
- HDR and VRR depend on the GPU, display, connection and game.
- Proton-GE is not automatically better for every game.
- VPN use can increase latency.
- NTFS game libraries are unsupported for the intended Bazzite gaming workflow.
- Rollback does not restore deleted personal files.
- Community Flatpaks may not be supported by the original application vendor.
- Arcalium is an independent Bazzite-derived project.

---

# 26. Future Backlog

After the stable NVIDIA desktop release:

1. AMD/Intel edition.
2. Optional NVIDIA console/HTPC experiment.
3. Game compatibility search.
4. Anti-cheat status integration.
5. Per-game recommended Proton profiles.
6. Automatic but reversible launch-option suggestions.
7. Backup and restore of launcher configurations.
8. Game-save backup integrations.
9. Family gaming profiles.
10. Optional parental controls using supported desktop mechanisms.
11. OpenRGB integration.
12. Razer peripheral integration.
13. Fan-control integrations.
14. Mod-manager integrations.
15. One-click Sunshine/Moonlight pairing.
16. Remote support bundle upload.
17. Offline application cache.
18. Arcalium recovery USB.
19. OEM installation workflow.
20. Hardware certification matrix.
21. Handheld edition.
22. Living-room controller-only interface.
23. Arcalium hardware appliances.
24. Optional local AI game troubleshooting assistant.

Each future feature requires its own specification and must not be casually added to version 1.

---

# 27. Definition of Done

Arcalium OS NVIDIA Edition version 1 is done only when:

- The current official Bazzite NVIDIA-open base is used.
- The image builds from GitHub Actions.
- The image is signed.
- The ISO installs.
- The QCOW2 boots.
- RTX 3090 validation passes.
- Both RTX 2060 validation passes.
- Steam launches.
- Vulkan passes.
- Proton gaming passes.
- Proton-GE setup works.
- Spotify provisioning works.
- Bazaar works.
- ProtonVPN setup works.
- Storage warnings work.
- Update works.
- Rollback works.
- Setup runs once and resumes safely.
- The Control Centre uses an allowlisted backend.
- Support bundles are redacted.
- Documentation exists.
- Licence inventory exists.
- Known limitations are published.
- No critical issue remains open.
- Public release gates are resolved before public distribution.

---

# 28. Immediate Cursor Task List

Cursor should begin with these tasks only:

1. Create the repository from the latest Universal Blue `image-template`.
2. Set the base to `ghcr.io/ublue-os/bazzite-nvidia-open:stable`.
3. Set image metadata for `arcalium-os-nvidia`.
4. Add `docs/PRODUCT_SPEC.md` using this document.
5. Add `docs/IMPLEMENTATION_STATUS.md`.
6. Configure Cosign without committing the private key.
7. Build and publish a private `dev` image to GHCR.
8. Verify the image signature.
9. Build a QCOW2 image.
10. Boot-test the unbranded image.
11. Build an installer ISO.
12. Install the minimal image on the RTX 3090 test machine.
13. Install the same image on one RTX 2060 test machine.
14. Record all commands, failures and upstream changes.
15. Do not begin the Control Centre until the base image and ISO workflow are proven.

The first milestone is not a polished interface. The first milestone is a reproducible, signed Arcalium NVIDIA image and ISO that boots correctly on both RTX 3090 and RTX 2060 hardware.

---

# 29. Verified Platform Assumptions

The following assumptions were verified against current upstream documentation during specification preparation:

- Universal Blue recommends its official image template for custom Bazzite-derived images.
- The template builds custom bootc images and can produce installer ISO and QCOW2 artefacts.
- Bazzite’s modern `nvidia-open` image supports Turing-and-newer NVIDIA cards, including GTX 16-series and all RTX cards.
- The legacy NVIDIA image is for older Pascal, Maxwell and Volta hardware.
- NVIDIA drivers are included in NVIDIA Bazzite images and update with the system image.
- Bazzite uses an atomic bootable-container model with rollback deployments.
- Bazaar and Flatpak are the recommended graphical application path.
- Bazzite’s current gaming guidance expects UEFI, Vulkan-capable graphics and SSD storage.
- Btrfs and Ext4 are the intended filesystems for game storage; NTFS and exFAT are not part of the supported gaming-storage path.
- Secure Boot requires the supported upstream key-enrolment process.
- ProtonVPN Flatpak support requires clear disclosure because the documented package may be unofficial.
- Steam redistribution requires separate legal attention before a public Arcalium ISO is distributed.

Revalidate these assumptions before each major release because upstream images, drivers, workflows and policies change.
