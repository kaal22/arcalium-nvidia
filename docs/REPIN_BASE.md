# Re-pin Bazzite base (agent runbook)

**Trigger phrases:** “check for base updates”, “re-pin base”, “update Bazzite digest”, “newer nvidia-open / drivers from upstream”.

**Source of truth for this procedure:** this file. Background: [`BUILDING.md`](BUILDING.md) (“Taking a Bazzite update”).

## Hard rules

1. **Never** rebase installed machines onto `bazzite-nvidia-open` directly. Re-pin → rebuild **Arcalium** → users `bootc upgrade`.
2. **`just build` does not re-pin.** Only changing the `Containerfile` digest moves the base.
3. Do **not** re-pin and promote `:stable` in the same breath without hardware smoke on the RTX **3060**.
4. Do **not** invent digests — resolve from GHCR only.
5. Ask before push / promote if the user did not already request ship.

## Cadence (advice to the user)

- Habit: every **2–4 weeks**, or before a stable/ISO cut.
- Sooner for known driver/kernel/security fixes.
- A “check only” (compare digests, update “Last checked”) is valuable even when **not** re-pinning.

---

## Phase A — Check only (always start here)

### A1. Read the current pin

From [`Containerfile`](../Containerfile):

```dockerfile
FROM ghcr.io/ublue-os/bazzite-nvidia-open:stable@sha256:…
```

Record `PINNED_DIGEST` (full `sha256:…`).

Also note the date comment above the `FROM` line and “Last checked” in [`BUILDING.md`](BUILDING.md).

### A2. Resolve upstream `:stable`

Prefer WSL Ubuntu / Git Bash (PowerShell Accept headers are awkward):

```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:ublue-os/bazzite-nvidia-open:pull&service=ghcr.io" | jq -r .token)
curl -sI -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
  https://ghcr.io/v2/ublue-os/bazzite-nvidia-open/manifests/stable \
  | grep -i docker-content-digest
```

Record `REMOTE_DIGEST`.

If the registry returns an OCI index, the `Docker-Content-Digest` on that response **is** the index digest Bazzite publishes for `:stable` — that is what we pin (same form as the existing pin).

### A3. Compare and report

| Result | Action |
|---|---|
| Digests **equal** | Report “base is current.” Update **Last checked** date in `BUILDING.md` + `Containerfile` comment date if present. Commit only if the user wants that bookkeeping committed. |
| Digests **differ** | Report both digests (shorten middle for chat: `sha256:abcd…wxyz`). Ask: **re-pin now?** Do **not** edit `Containerfile` until they say yes (unless they already said “re-pin”). |

Stop after Phase A if the user only asked to **check**.

---

## Phase B — Re-pin (only when asked)

### B1. Edit the pin

1. Update `Containerfile` `FROM` to `@${REMOTE_DIGEST}`.
2. Update the comment date above `FROM` (“Digest resolved YYYY-MM-DD for :stable”).
3. Update `docs/BUILDING.md` “Last checked …” and any digest mentioned in `docs/IMPLEMENTATION_STATUS.md` base line if present.

### B2. Commit message style

```text
Re-pin bazzite-nvidia-open:stable to sha256:<12hex>….

Pick up upstream kernel/NVIDIA stack; requires bootc upgrade + 3060 smoke after CI.
```

Commit/push only when the user asked (or they said “re-pin and ship”).

### B3. CI

Push to `main` → wait for **Build container image** success. Confirm `:dev` moved and Cosign signed.

### B4. Hardware smoke (owner / instruct clearly)

On the 3060 (private GHCR may need ostree auth):

```bash
sudo bootc upgrade && sudo systemctl reboot
nvidia-smi
# quick game or Vulkan path via Control Centre
```

Checklist minimum: boots, `nvidia-smi` OK, Plasma Wayland, Control Centre opens, optional Drivers check still coherent. Also confirm Flatpak GL matched the new driver (`flatpak list | grep GL.nvidia` and/or wait for `arcalium-flatpak-nvidia.service` — it auto-pulls matching GL on first boot with network). Smoke: Heroic launches a game without an OpenGL error; optional Firefox `about:support` GPU line; escape hatch `arcaliumctl steam harden`.

**Branding (re-pin sensitive):** Plasma splash shows Arcalium wordmark (not Bazzite); login greeter uses Arcalium wallpaper; Konsole opens with Arcalium `fastfetch` (ASCII mark + `Arcalium OS NVIDIA Edition`), not Bazzite tips/logo. If login looks stock after upgrade, check host override:

```bash
sudo grep -n Image /etc/plasmalogin.conf /etc/plasmalogin.conf.d/* 2>/dev/null || true
# If Image= points at default.jxl / convergence / backgrounds/, clear or fix, then restart greeter / reboot.
```

Quick Konsole check after upgrade:

```bash
grep -E '^(NAME|PRETTY_NAME)=' /etc/os-release
head -n5 /etc/profile.d/user-motd.sh
fastfetch -c /usr/share/arcalium/fastfetch.jsonc | head
```

### B5. Promote (only if asked)

After smoke passes, use **Promote stable** (`promote-stable.yml`) for version/`stable` tags — see public release notes. Do not auto-promote every re-pin during `:dev` iteration.

### B6. ISO (only if asked / milestone)

Full `just build` then `just build-iso-live` in WSL — base re-pin does **not** require an ISO for installed testers; ISO for clean installs / getarcalium.com.

**Flatpak NVIDIA GL:** each image build stamps `/usr/share/arcalium/flatpak-nvidia-gl.tag` from the NVIDIA RPMs. ISO builds install matching `GL.nvidia-*` / `GL32` into the bundled `/var/lib/flatpak` store (offline Heroic/Firefox). Existing installs get the new tag via `bootc upgrade` + `arcalium-flatpak-nvidia.service` (network). Rebuild the ISO when you want offline GL for that driver on fresh media — `bootc upgrade` alone does not refresh the Flatpak store from the ISO bundle.

---

## Phase C — What not to do

- Do not layer NVIDIA RPMs or run GeForce/`.run` installers on the machine.
- Do not change `IMAGE_NAME` or track Bazzite GHCR as the update remote.
- Do not skip digest verify “because skopeo isn’t installed” — use the curl API above.
- Do not re-pin `bazzite` (non-NVIDIA) for this edition.

---

## One-shot agent checklist

```text
[ ] Read Containerfile pin
[ ] Resolve GHCR :stable digest
[ ] Report equal / newer
[ ] Update Last checked if check-only and user wants it
[ ] If re-pin: edit Containerfile + BUILDING (+ IMPLEMENTATION_STATUS)
[ ] Commit/push only if asked
[ ] Wait CI / tell user bootc upgrade + nvidia-smi smoke (+ Flatpak GL via auto harden)
[ ] Promote/ISO only if asked (ISO carries matching GL.nvidia for offline installs)
```
