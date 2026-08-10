# Channel runbook: test `:dev`, then promote `:stable`

**Never forget:** day-to-day work lands on `:dev`. Only promote to `:stable` after RTX **3060** smoke. Flipping GHCR **public** is a separate, irreversible step — not part of promote.

```text
push main → CI Build container image → :dev
        ↓
3060: bootc upgrade + reboot + smoke
        ↓
happy? → Promote stable (version + :stable)
        ↓
public media? → rebuild Live ISO from that digest
        ↓
site hosts ISO + SHA? → then GHCR_PUBLIC_FLIP (optional, later)
```

Primary tester stays on **`:dev`** until you intentionally switch it.

---

## 1. Land changes on `:dev`

1. Commit and push to `main` (or run **Build container image** `workflow_dispatch` on `main` if a push build was skipped/cancelled).
2. Wait for CI green: [Actions → Build container image](https://github.com/kaal22/arcalium-nvidia/actions/workflows/build.yml).
3. Confirm the tip:

```bash
# optional: inspect digest
skopeo inspect --format '{{.Digest}}' docker://ghcr.io/kaal22/arcalium-os-nvidia:dev
```

## 2. Smoke on the 3060 (`:dev`)

Machine must track `ghcr.io/kaal22/arcalium-os-nvidia:dev` (private GHCR may need `/etc/ostree/auth.json` — see [`BUILDING.md`](BUILDING.md)).

```bash
sudo bootc upgrade && sudo systemctl reboot
```

Minimum smoke (adapt to the change):

- [ ] Boots, Plasma Wayland
- [ ] `nvidia-smi` OK
- [ ] Control Centre opens; Overview / changed pages look sane
- [ ] If Flatpak / GL related: `flatpak list | grep GL.nvidia`; Heroic or Steam not “no OpenGL”
- [ ] If updates path touched: Updates page still shows deployments

Rollback if bad: use Control Centre → Updates and Recovery, or `sudo bootc rollback` (terminal path). Do **not** promote a digests you just rolled back from.

Version-specific RC checklists (when cutting a numbered release): e.g. [`RC_SMOKE_0.2.0.md`](RC_SMOKE_0.2.0.md).

## 3. Promote `:stable` (only when happy)

GitHub Actions → **Promote stable** (`promote-stable.yml`) → `workflow_dispatch`:

| Input | Typical value |
|-------|----------------|
| `source_tag` | `dev` (or a pinned tag like `iso-0.2.1` if you must match an exact digest) |
| `version` | Next version, e.g. `0.2.2` |
| `also_tag_stable` | `true` |

That **retags the same digest** — no rebuild. Both `:0.x.y` and `:stable` should point at the digest you smoked on `:dev`.

**Risk:** promoting `:dev` *after* CI moved past the digests you tested. If in doubt, promote from a digest you froze (temporary tag) or re-smoke the tip first.

After promote:

```bash
# On a machine that tracks stable (or after switch):
sudo bootc upgrade && sudo systemctl reboot
# or first time:
sudo bootc switch ghcr.io/kaal22/arcalium-os-nvidia:stable
sudo systemctl reboot
```

Publish matching GitHub Release notes + `.sha256` when there is a public ISO for that version.

## 4. ISO (milestone, not every promote)

`:stable` image updates ≠ new installer media. Rebuild Live ISO when clean installs / getarcalium.com must match the promoted digest (Flatpak store, Anaconda payload, etc.). See [`BUILDING.md`](BUILDING.md).

Keep ISO digest === promoted `:stable` digest. Do not claim “public 0.x.y ISO” if the site still hosts an older cut.

## 5. GHCR public (separate gate)

Promote does **not** open the registry. Public visibility is irreversible and waits on a real download page.

→ [`GHCR_PUBLIC_FLIP.md`](GHCR_PUBLIC_FLIP.md)

---

## Related docs

| Doc | Role |
|-----|------|
| [`BUILDING.md`](BUILDING.md) | Build, ISO, private GHCR auth |
| [`REPIN_BASE.md`](REPIN_BASE.md) | Upstream Bazzite re-pin, then this same smoke → promote path |
| [`GHCR_PUBLIC_FLIP.md`](GHCR_PUBLIC_FLIP.md) | Make package public after site gate |
| [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) | Current channel / digests |

## Hard rules

1. **No promote without 3060 smoke** on the digest you intend to ship.
2. **No auto-promote** every `:dev` push.
3. **Do not** conflate promote with “flip public.”
4. **Do not** rebase installed machines onto `bazzite-nvidia-open` — only Arcalium tags.
