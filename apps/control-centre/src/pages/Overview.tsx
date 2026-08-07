import { useCallback, useEffect, useMemo, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { pick, str } from "../lib/json";
import type { PageId } from "../nav";

type LoadState = "loading" | "ready" | "error";

function statusClass(overall: unknown): string {
  if (overall === "ready") return "ok";
  if (overall === "warning" || overall === "unknown") return "warn";
  return "bad";
}

function num(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "") {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/** Decorative snapshot wave — shape from current value, not live telemetry. */
function Wave({ seed, amp = 0.55 }: { seed: number; amp?: number }) {
  const d = useMemo(() => {
    const pts: string[] = [];
    const steps = 24;
    const s = Math.abs(seed) + 1;
    for (let i = 0; i <= steps; i++) {
      const x = (i / steps) * 100;
      const t = i / steps;
      const y =
        14 +
        Math.sin(t * Math.PI * 2.4 + s * 0.17) * (6 * amp) +
        Math.sin(t * Math.PI * 5.1 + s * 0.09) * (3 * amp) +
        ((s % 7) / 7 - 0.5) * 2;
      pts.push(`${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`);
    }
    return pts.join(" ");
  }, [seed, amp]);

  return (
    <svg viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden>
      <path d={d} fill="none" stroke="currentColor" strokeWidth="1.4" opacity="0.85" />
    </svg>
  );
}

function clampPct(v: number | null): number {
  if (v === null) return 0;
  return Math.max(0, Math.min(100, v));
}

type Props = {
  onNavigate: (id: PageId) => void;
};

export function OverviewPage({ onNavigate }: Props) {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<JsonValue | null>(null);
  const [gpu, setGpu] = useState<JsonValue | null>(null);
  const [validate, setValidate] = useState<JsonValue | null>(null);
  const [vulkan, setVulkan] = useState<JsonValue | null>(null);
  const [storage, setStorage] = useState<JsonValue | null>(null);
  const [updates, setUpdates] = useState<JsonValue | null>(null);
  const [ai, setAi] = useState<JsonValue | null>(null);
  const [steam, setSteam] = useState<JsonValue | null>(null);
  const [installingProton, setInstallingProton] = useState(false);
  const [installingSteam, setInstallingSteam] = useState(false);
  const [rollingBack, setRollingBack] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const [s, g, v, vk, st, store, upd, aiSt] = await Promise.all([
        arcaliumctl(["system", "summary", "--json"]),
        arcaliumctl(["gpu", "status", "--json"]),
        arcaliumctl(["gpu", "validate", "--json"]),
        arcaliumctl(["vulkan", "test", "--json"]),
        arcaliumctl(["steam", "status", "--json"]).catch(() => null),
        arcaliumctl(["storage", "scan", "--json"]).catch(() => null),
        arcaliumctl(["updates", "status", "--json"]).catch(() => null),
        arcaliumctl(["ai", "status", "--json"]).catch(() => null),
      ]);
      setSummary(s);
      setGpu(g);
      setValidate(v);
      setVulkan(vk);
      setSteam(st);
      setStorage(store);
      setUpdates(upd);
      setAi(aiSt);
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const installProton = useCallback(async () => {
    setInstallingProton(true);
    setActionMsg(null);
    setActionErr(null);
    try {
      const result = await arcaliumctl(["proton", "install-recommended", "--visible", "--json"]);
      const action = str(pick(result, "action"), "done");
      const name = str(pick(result, "name"), "GE-Proton");
      if (action === "already_present") {
        setActionMsg(`${name} is already installed.`);
      } else if (action === "terminal") {
        setActionMsg(
          str(
            pick(result, "message"),
            "Installing GE-Proton in a terminal — watch progress there.",
          ),
        );
        const started = Date.now();
        let done = false;
        while (Date.now() - started < 30 * 60 * 1000) {
          await new Promise((r) => setTimeout(r, 4000));
          const list = await arcaliumctl(["proton", "list", "--json"]);
          if (pick(list, "recommendedPresent") === true) {
            done = true;
            break;
          }
        }
        setActionMsg(
          done
            ? "GE-Proton installed. See Compatibility for details."
            : "Still installing in the terminal. Refresh when it finishes.",
        );
      } else {
        setActionMsg(`Installed ${name}. See Compatibility for details.`);
      }
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setInstallingProton(false);
    }
  }, []);

  const installSteam = useCallback(async () => {
    setInstallingSteam(true);
    setActionMsg(null);
    setActionErr(null);
    try {
      const result = await arcaliumctl(["steam", "install", "--visible", "--json"]);
      setActionMsg(
        str(
          pick(result, "message"),
          "Installing Steam from Flathub in a terminal — Steam's agreement appears on first launch.",
        ),
      );
      if (str(pick(result, "action")) === "terminal" || str(pick(result, "action")) === "opened") {
        const started = Date.now();
        while (Date.now() - started < 30 * 60 * 1000) {
          await new Promise((r) => setTimeout(r, 4000));
          const st = await arcaliumctl(["steam", "status", "--json"]);
          setSteam(st);
          if (pick(st, "installed") === true) break;
        }
      }
      await refresh();
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setInstallingSteam(false);
    }
  }, [refresh]);

  const runRollback = useCallback(async () => {
    setRollingBack(true);
    setActionMsg(null);
    setActionErr(null);
    try {
      const result = await arcaliumctl(["updates", "rollback", "--json"]);
      if (!pick(result, "ok")) {
        throw new Error(str(pick(result, "message"), "Could not start rollback."));
      }
      setActionMsg(
        str(
          pick(result, "message"),
          "Rollback opened in a terminal — type yes to confirm, then the machine reboots.",
        ),
      );
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRollingBack(false);
    }
  }, []);

  const overall = pick(validate, "overall");
  const vulkanOk = pick(vulkan, "available") === true && pick(vulkan, "hasNvidiaDevice") === true;
  const util = num(pick(gpu, "utilizationGpu"));
  const temp = num(pick(gpu, "temperatureC"));
  const power = num(pick(gpu, "powerDrawW"));
  const memUsed = num(pick(gpu, "memoryUsed"));
  const memTotal = num(pick(gpu, "memoryTotal"));
  const rootFree = num(pick(storage, "root.freeGiB"));
  const rootTotal = num(pick(storage, "root.totalGiB"));
  const rootUsedPct =
    rootFree !== null && rootTotal !== null && rootTotal > 0
      ? clampPct(((rootTotal - rootFree) / rootTotal) * 100)
      : null;
  const vramPct =
    memUsed !== null && memTotal !== null && memTotal > 0
      ? clampPct((memUsed / memTotal) * 100)
      : null;

  const rollbackDep = pick(updates, "bootc.rollback") as JsonValue | null;
  const bootedDep = pick(updates, "bootc.booted") as JsonValue | null;
  const rollbackReady = Boolean(rollbackDep && pick(rollbackDep, "image"));
  const steamLaunchable = Boolean(pick(steam, "launchable"));

  const aiReady = Boolean(pick(ai, "ollama.available"));
  const aiHint = ai
    ? aiReady
      ? str(pick(ai, "model") ?? pick(ai, "ollama.model"), "Ollama available")
      : str(pick(ai, "message"), "Local AI not ready yet — open Assistant to set up.")
    : "Status unavailable";

  const memGiB = num(pick(summary, "memoryGiB"));

  return (
    <div className={`page${state === "ready" ? " ov-ready" : ""}`}>
      <header className="page-header">
        <div>
          <p className="eyebrow">Terminal // Overview</p>
          <h1>Control Centre</h1>
          <p className="muted">Your system at a glance.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()} disabled={state === "loading"}>
          {state === "loading" ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {state === "error" && (
        <div className="banner error">
          <strong>Could not load diagnostics.</strong>
          <div>{error}</div>
        </div>
      )}

      {(actionMsg || actionErr) && (
        <div className={actionErr ? "banner error" : "banner ok"}>
          <strong>{actionErr ? "Action failed." : actionMsg}</strong>
          {actionErr && <div>{actionErr}</div>}
        </div>
      )}

      <section className="stat-strip" aria-label="System summary">
        <article className="stat-tile">
          <p className="stat-label">OS</p>
          <p className="stat-value">
            {str(pick(summary, "product"), "Arcalium")}{" "}
            <span className="muted small">{str(pick(summary, "edition"))}</span>
          </p>
          <p className="stat-meta mono">
            {str(pick(summary, "imageName"))}:{str(pick(summary, "channel"))}
          </p>
          <p className="stat-meta mono">KERNEL {str(pick(summary, "kernel"))}</p>
        </article>

        <article className="stat-tile">
          <p className="stat-label">CPU</p>
          <p className="stat-value">{str(pick(summary, "cpuModel"))}</p>
          <p className="stat-meta">Session {str(pick(summary, "sessionType"))}</p>
        </article>

        <article className="stat-tile">
          <p className="stat-label">RAM</p>
          <p className="stat-value">{memGiB !== null ? `${memGiB} GiB` : "—"}</p>
          <p className="stat-meta">Host {str(pick(summary, "hostname"))}</p>
        </article>

        <article className="stat-tile">
          <p className="stat-label">Storage</p>
          <p className="stat-value">
            {rootFree !== null && rootTotal !== null
              ? `${rootFree.toFixed(0)} / ${rootTotal.toFixed(0)} GiB free`
              : "—"}
          </p>
          <p className="stat-meta">Root filesystem</p>
          {rootUsedPct !== null && (
            <div className="metric-bar" aria-hidden>
              <span style={{ width: state === "ready" ? `${rootUsedPct}%` : "0%" }} />
            </div>
          )}
        </article>
      </section>

      <section className="ov-mid" aria-label="GPU and recovery">
        <article className="card glow hero-card">
          <div className="gpu-glyph" aria-hidden />
          <div>
            <h2>GPU Status</h2>
            <p className="stat-value" style={{ marginBottom: "0.35rem" }}>
              {str(pick(gpu, "primaryGpuName"))}
            </p>
            <p className="stat-meta mono" style={{ marginBottom: "0.5rem" }}>
              Driver {str(pick(gpu, "driverVersion"))} · Validate{" "}
              <span className={statusClass(overall)}>{str(overall, "—")}</span>
            </p>
            <dl className="hero-metrics">
              <div className="hero-metric">
                <dt>Utilisation</dt>
                <dd>{util !== null ? `${util}%` : "—"}</dd>
              </div>
              <div className="hero-metric">
                <dt>Temp</dt>
                <dd>{temp !== null ? `${temp} °C` : "—"}</dd>
              </div>
              <div className="hero-metric">
                <dt>VRAM</dt>
                <dd>
                  {memUsed !== null && memTotal !== null
                    ? `${memUsed} / ${memTotal} MiB`
                    : "—"}
                </dd>
              </div>
              <div className="hero-metric">
                <dt>Power</dt>
                <dd>{power !== null ? `${power} W` : "—"}</dd>
              </div>
            </dl>
            {vramPct !== null && (
              <div className="metric-bar" aria-hidden>
                <span style={{ width: state === "ready" ? `${vramPct}%` : "0%" }} />
              </div>
            )}
            <div className="btn-row" style={{ marginTop: "0.9rem", marginBottom: 0 }}>
              <button type="button" className="btn primary" onClick={() => onNavigate("gpu")}>
                Open GPU and Display
              </button>
            </div>
          </div>
        </article>

        <article className="card cta-orb">
          <div className="orb" aria-hidden>
            STEAM
          </div>
          <h2>{steamLaunchable ? "Launch Steam" : "Install a Gaming Platform"}</h2>
          <p className="muted small">
            {steamLaunchable
              ? "Steam Flatpak is ready on this system."
              : "Install Valve’s Steam Flatpak from Flathub to access your games."}
          </p>
          {steamLaunchable ? (
            <button
              type="button"
              className="btn primary pulse"
              onClick={() =>
                void openDesktop(str(pick(steam, "desktopId"), "com.valvesoftware.Steam.desktop"))
              }
            >
              Launch Steam
            </button>
          ) : (
            <button
              type="button"
              className={`btn primary pulse${installingSteam ? " working" : ""}`}
              disabled={installingSteam}
              onClick={() => void installSteam()}
            >
              {installingSteam ? "Installing in terminal…" : "Install Steam"}
            </button>
          )}
        </article>

        <article className="card rollback-card">
          <h2>System Rollback</h2>
          <div className="rollback-icon" aria-hidden>
            BOOTC
          </div>
          <dl className="kv">
            <div>
              <dt>Booted</dt>
              <dd className="mono small">{str(pick(bootedDep, "image"), "—")}</dd>
            </div>
            <div>
              <dt>Rollback</dt>
              <dd className="mono small">{str(pick(rollbackDep, "image"), "none")}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span className={`badge ${rollbackReady ? "amber" : "warn"}`}>
                  {rollbackReady ? "Ready" : "Unavailable"}
                </span>
              </dd>
            </div>
          </dl>
          <button
            type="button"
            className={`btn danger-amber${rollingBack ? " working" : ""}`}
            disabled={rollingBack || !rollbackReady}
            onClick={() => void runRollback()}
          >
            {rollingBack ? "Opening…" : "Rollback System"}
          </button>
          <button type="button" className="btn" onClick={() => onNavigate("updates")}>
            Updates and Recovery
          </button>
        </article>
      </section>

      <section className="ov-bottom" aria-label="Metrics and assistant">
        <article className="card">
          <h2>System Overview</h2>
          <div className="metric-strip">
            <div className="metric-wave">
              <p className="mw-label">GPU Util</p>
              <p className="mw-value">{util !== null ? `${util}%` : "—"}</p>
              <Wave seed={util ?? 3} amp={clampPct(util) / 100 || 0.35} />
            </div>
            <div className="metric-wave">
              <p className="mw-label">GPU Temp</p>
              <p className="mw-value">{temp !== null ? `${temp} °C` : "—"}</p>
              <Wave seed={(temp ?? 40) * 1.7} amp={0.5} />
            </div>
            <div className="metric-wave">
              <p className="mw-label">Board Power</p>
              <p className="mw-value">{power !== null ? `${power} W` : "—"}</p>
              <Wave seed={(power ?? 50) * 2.1} amp={0.55} />
            </div>
            <div className="metric-wave">
              <p className="mw-label">Vulkan</p>
              <p className={`mw-value ${vulkanOk ? "ok" : "bad"}`}>{vulkanOk ? "OK" : "Fail"}</p>
              <Wave seed={vulkanOk ? 21 : 2} amp={vulkanOk ? 0.6 : 0.2} />
            </div>
          </div>
        </article>

        <article className="card ai-teaser">
          <div className="ai-head">
            <div className="ai-orb" aria-hidden />
            <div>
              <h2 style={{ margin: 0 }}>
                AI Assistant <span className="badge ok">Beta</span>
              </h2>
              <p className="muted small" style={{ marginTop: "0.35rem" }}>
                {aiHint}
              </p>
            </div>
          </div>
          <p className="muted small">
            Local models stay on this PC. Open the assistant to install Ollama, ensure a model, or
            launch a session.
          </p>
          <button type="button" className="btn primary" onClick={() => onNavigate("assistant")}>
            Open Local AI Assistant
          </button>
        </article>
      </section>

      <section className="actions">
        <h2>Quick actions</h2>
        <div className="quick-chip-row">
          <button
            type="button"
            className="btn"
            onClick={() => void openDesktop("io.github.kolunmi.Bazaar.desktop")}
          >
            Open Bazaar
          </button>
          <button
            type="button"
            className={`btn primary${installingProton ? " working" : ""}`}
            disabled={installingProton}
            onClick={() => void installProton()}
          >
            {installingProton ? "Installing in terminal…" : "Install Proton-GE"}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => void openDesktop("systemsettings.desktop")}
          >
            System Settings
          </button>
          <button type="button" className="btn" onClick={() => onNavigate("compatibility")}>
            Compatibility
          </button>
        </div>
        <p className="muted small">
          Launches allowlisted apps via gio launch. Install Proton-GE downloads the latest GE-Proton
          into Heroic&apos;s tools directory. Rollback opens a terminal and asks you to type{" "}
          <span className="mono">yes</span> before rebooting into the previous deployment.
        </p>
      </section>
    </div>
  );
}
