import { useCallback, useEffect, useMemo, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { AppActions, AppRow } from "../components/AppActions";
import { AiMinSpec } from "../components/AiMinSpec";
import { GpuDriverUpdates } from "../components/GpuDriverUpdates";
import { copyText, pick, str } from "../lib/json";
import { WIZARD_STEPS, WizardStepId } from "./steps";

type StepState = "pending" | "complete" | "skipped" | "in_progress";

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollAiStatus(
  ready: (status: JsonValue) => boolean,
  opts: { intervalMs?: number; maxMs?: number; onTick?: (status: JsonValue) => void } = {},
): Promise<{ ok: boolean; status: JsonValue | null }> {
  const intervalMs = opts.intervalMs ?? 4000;
  const maxMs = opts.maxMs ?? 60 * 60 * 1000;
  const started = Date.now();
  let last: JsonValue | null = null;
  while (Date.now() - started < maxMs) {
    last = await arcaliumctl(["ai", "status", "--json"]);
    opts.onTick?.(last);
    if (ready(last)) return { ok: true, status: last };
    await sleep(intervalMs);
  }
  return { ok: false, status: last };
}

export function WizardApp() {
  const [stepIndex, setStepIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [summary, setSummary] = useState<JsonValue | null>(null);
  const [gpuVal, setGpuVal] = useState<JsonValue | null>(null);
  const [vulkan, setVulkan] = useState<JsonValue | null>(null);
  const [updates, setUpdates] = useState<JsonValue | null>(null);
  const [apps, setApps] = useState<AppRow[]>([]);
  const [proton, setProton] = useState<JsonValue | null>(null);
  const [storage, setStorage] = useState<JsonValue | null>(null);
  const [network, setNetwork] = useState<JsonValue | null>(null);
  const [diag, setDiag] = useState<JsonValue | null>(null);
  const [aiStatus, setAiStatus] = useState<JsonValue | null>(null);
  const [installingProton, setInstallingProton] = useState(false);
  const [installingOllama, setInstallingOllama] = useState(false);
  const [ensuringAi, setEnsuringAi] = useState(false);

  const step = WIZARD_STEPS[stepIndex];

  const persist = useCallback(async (stepId: WizardStepId, state?: StepState) => {
    await arcaliumctl(["setup", "save", stepId, "--json"]);
    if (state) {
      await arcaliumctl(["setup", "mark", stepId, state, "--json"]);
    }
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const st = await arcaliumctl(["setup", "status", "--json"]);
        if (pick(st, "liveSession")) {
          setError("Setup does not run in the live installer. Finish installing, then reboot.");
          return;
        }
        const current = str(pick(st, "currentStep"), "welcome") as WizardStepId;
        const idx = WIZARD_STEPS.findIndex((s) => s.id === current);
        if (idx >= 0 && !pick(st, "completed")) {
          setStepIndex(idx);
        }
        await arcaliumctl(["setup", "save", WIZARD_STEPS[idx >= 0 ? idx : 0].id, "--json"]);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, []);

  const loadHardware = useCallback(async () => {
    const [s, g, v] = await Promise.all([
      arcaliumctl(["system", "summary", "--json"]),
      arcaliumctl(["gpu", "validate", "--json"]),
      arcaliumctl(["vulkan", "test", "--json"]),
    ]);
    setSummary(s);
    setGpuVal(g);
    setVulkan(v);
  }, []);

  const loadUpdates = useCallback(async () => {
    setUpdates(await arcaliumctl(["updates", "status", "--json"]));
  }, []);

  const loadApps = useCallback(async () => {
    const data = await arcaliumctl(["apps", "list", "--json"]);
    setApps((pick(data, "apps") as AppRow[]) || []);
  }, []);

  const loadProton = useCallback(async () => {
    setProton(await arcaliumctl(["proton", "list", "--json"]));
  }, []);

  const loadStorage = useCallback(async () => {
    setStorage(await arcaliumctl(["storage", "scan", "--json"]));
  }, []);

  const loadNetwork = useCallback(async () => {
    setNetwork(await arcaliumctl(["network", "status", "--json"]));
  }, []);

  const loadValidation = useCallback(async () => {
    setDiag(await arcaliumctl(["diagnostics", "run", "--json"]));
  }, []);

  const loadAi = useCallback(async () => {
    setAiStatus(await arcaliumctl(["ai", "status", "--json"]));
  }, []);

  useEffect(() => {
    setError(null);
    setMsg(null);
    const id = step.id;
    void (async () => {
      try {
        setBusy(true);
        await persist(id);
        if (id === "hardware" || id === "nvidia") await loadHardware();
        if (id === "updates") await loadUpdates();
        if (id === "applications" || id === "steam" || id === "streaming" || id === "vpn") {
          await loadApps();
        }
        if (id === "protonGe") await loadProton();
        if (id === "storage") await loadStorage();
        if (id === "vpn") await loadNetwork();
        if (id === "validation") await loadValidation();
        if (id === "localAi") await loadAi();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    })();
  }, [
    step.id,
    persist,
    loadHardware,
    loadUpdates,
    loadApps,
    loadProton,
    loadStorage,
    loadNetwork,
    loadValidation,
    loadAi,
  ]);

  const goNext = async (mark: StepState = "complete") => {
    setBusy(true);
    setError(null);
    try {
      await persist(step.id, mark);
      if (step.id === "completion") {
        await arcaliumctl(["setup", "complete", "--json"]);
        setMsg("Setup complete. You can close this window.");
        return;
      }
      setStepIndex((i) => Math.min(i + 1, WIZARD_STEPS.length - 1));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const goBack = () => setStepIndex((i) => Math.max(i - 1, 0));

  const skip = () => void goNext("skipped");

  const gamingApps = useMemo(
    () => apps.filter((a) => ((a as { roles?: string[] }).roles || []).includes("gaming")),
    [apps],
  );
  const optionalApps = useMemo(
    () =>
      apps.filter((a) =>
        ((a as { roles?: string[] }).roles || []).some((r) =>
          ["applications", "compatibility"].includes(r),
        ),
      ),
    [apps],
  );
  const streamingApps = useMemo(
    () => apps.filter((a) => ((a as { roles?: string[] }).roles || []).includes("streaming")),
    [apps],
  );
  const vpnApp = useMemo(() => apps.find((a) => a.id === "protonvpn") || null, [apps]);
  const steamApp = useMemo(() => apps.find((a) => a.id === "steam") || null, [apps]);

  const checks = (pick(gpuVal, "checks") as { title?: string; status?: string; detail?: string }[]) || [];
  const diagChecks =
    (pick(diag, "checks") as { title?: string; status?: string; detail?: string }[]) || [];
  const warnings = (pick(storage, "warnings") as { message?: string }[]) || [];

  return (
    <div className="wizard">
      <aside className="wizard-rail">
        <div className="brand-name">Arcalium Setup</div>
        <div className="brand-sub">NVIDIA Edition</div>
        <ol className="wizard-steps">
          {WIZARD_STEPS.map((s, i) => (
            <li key={s.id} className={i === stepIndex ? "active" : i < stepIndex ? "done" : ""}>
              {s.label}
            </li>
          ))}
        </ol>
      </aside>
      <main className="wizard-main">
        <header className="page-header">
          <div>
            <h1>{step.label}</h1>
            <p className="muted">
              Step {stepIndex + 1} of {WIZARD_STEPS.length}
            </p>
          </div>
        </header>
        {error && <p className="banner bad">{error}</p>}
        {msg && <p className="banner ok">{msg}</p>}
        {busy && <p className="muted">Working…</p>}

        {step.id === "welcome" && (
          <article className="card">
            <p>
              Welcome to <strong>Arcalium OS</strong> — an independent gaming-focused desktop built on
              Bazzite for NVIDIA GPUs (RTX / GTX 16-series).
            </p>
            <p className="muted">
              This short setup checks hardware, optional apps, Proton-GE and game storage. It does not
              collect personal data. Optional app installs need Internet access. Arcalium is not
              affiliated with Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or Bazzite.
            </p>
          </article>
        )}

        {step.id === "hardware" && summary && (
          <article className="card">
            <dl className="kv">
              <div>
                <dt>CPU</dt>
                <dd>{str(pick(summary, "cpuModel"))}</dd>
              </div>
              <div>
                <dt>RAM</dt>
                <dd>{str(pick(summary, "memoryGiB"))} GiB</dd>
              </div>
              <div>
                <dt>GPU</dt>
                <dd>{str(pick(gpuVal, "gpu.name"))}</dd>
              </div>
              <div>
                <dt>Driver</dt>
                <dd>{str(pick(gpuVal, "gpu.driverVersion"))}</dd>
              </div>
              <div>
                <dt>Kernel</dt>
                <dd className="mono">{str(pick(summary, "kernel"))}</dd>
              </div>
              <div>
                <dt>Image</dt>
                <dd className="mono">
                  {str(pick(summary, "imageName"))}:{str(pick(summary, "channel"))}
                </dd>
              </div>
              <div>
                <dt>Session</dt>
                <dd>{str(pick(summary, "sessionType"))}</dd>
              </div>
              <div>
                <dt>Vulkan NVIDIA</dt>
                <dd>{pick(vulkan, "hasNvidiaDevice") ? "yes" : "no"}</dd>
              </div>
            </dl>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              Display resolution and refresh rate are configured in Plasma Display settings on the next
              optional page. Storage and network are covered later in this wizard.
            </p>
          </article>
        )}

        {step.id === "nvidia" && (
          <article className="card">
            <p>
              Overall: <strong>{str(pick(gpuVal, "overall"))}</strong>
            </p>
            <ul className="plain-list">
              {checks.map((c, i) => (
                <li key={i}>
                  <span className={`badge ${c.status === "ready" ? "ok" : c.status === "unsupported" || c.status === "fail" ? "bad" : "warn"}`}>
                    {str(c.status)}
                  </span>{" "}
                  {str(c.title)}
                  {c.detail ? <span className="muted small"> — {c.detail}</span> : null}
                </li>
              ))}
            </ul>
            <div className="btn-row" style={{ marginTop: "0.75rem" }}>
              <button
                type="button"
                className="btn"
                onClick={async () => {
                  try {
                    const result = await arcaliumctl(["diagnostics", "bundle", "--json"]);
                    setMsg(`Support bundle: ${str(pick(result, "path"))}`);
                  } catch (e) {
                    setError(e instanceof Error ? e.message : String(e));
                  }
                }}
              >
                Generate support bundle
              </button>
            </div>
            <h3 style={{ marginTop: "1rem" }}>Driver updates</h3>
            <GpuDriverUpdates
              driverVersion={str(pick(gpuVal, "gpu.driverVersion"), "")}
              disabled={busy}
            />
          </article>
        )}

        {step.id === "display" && (
          <article className="card">
            <p className="muted">
              Use Plasma System Settings for resolution, refresh rate, scaling, VRR/HDR, and audio
              devices. Arcalium does not duplicate those controls.
            </p>
            <div className="btn-row">
              <button type="button" className="btn" onClick={() => void openDesktop("systemsettings.desktop")}>
                Open System Settings
              </button>
            </div>
          </article>
        )}

        {step.id === "updates" && updates && (
          <article className="card">
            <dl className="kv">
              <div>
                <dt>Image</dt>
                <dd className="mono">
                  {str(pick(updates, "imageName"))}:{str(pick(updates, "channel"))}
                </dd>
              </div>
              <div>
                <dt>Booted</dt>
                <dd className="mono small">{str(pick(updates, "bootc.booted.image"))}</dd>
              </div>
            </dl>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              Applying updates needs a terminal for now. Network failure here will not block setup —
              you can update later from Control Centre → Updates.
            </p>
            <ul className="plain-list mono small">
              <li>{str(pick(updates, "guidance.check"))}</li>
              <li>{str(pick(updates, "guidance.apply"))}</li>
            </ul>
            <div className="btn-row">
              <button
                type="button"
                className="btn"
                onClick={async () => {
                  await copyText(
                    [str(pick(updates, "guidance.check")), str(pick(updates, "guidance.apply"))].join(
                      "\n",
                    ),
                  );
                  setMsg("Update commands copied.");
                }}
              >
                Copy update commands
              </button>
            </div>
          </article>
        )}

        {step.id === "applications" && (
          <div className="grid two">
            {optionalApps.map((app) => (
              <article className="card" key={str(app.id)}>
                <h2>{str(app.name)}</h2>
                <p className="muted small">{app.installed ? "Installed" : "Optional"}</p>
                <AppActions app={app} onChanged={() => void loadApps()} />
              </article>
            ))}
          </div>
        )}

        {step.id === "protonGe" && (
          <article className="card">
            <p>
              Proton lets Steam and Heroic run many Windows games on Linux. Proton-GE is a community
              build that helps specific titles — it should not replace Steam&apos;s default for every
              game.
            </p>
            <p className="muted">
              Installed GE-Proton builds:{" "}
              {((pick(proton, "installed") as { name?: string }[]) || [])
                .map((i) => i.name)
                .join(", ") || "none"}
            </p>
            <div className="btn-row">
              <button
                type="button"
                className={`btn primary${installingProton ? " working" : ""}`}
                disabled={installingProton}
                onClick={async () => {
                  setInstallingProton(true);
                  setError(null);
                  try {
                    const result = await arcaliumctl([
                      "proton",
                      "install-recommended",
                      "--visible",
                      "--json",
                    ]);
                    const action = str(pick(result, "action"));
                    if (action === "terminal") {
                      setMsg(
                        str(
                          pick(result, "message"),
                          "Installing GE-Proton in a terminal — watch progress there.",
                        ),
                      );
                      const started = Date.now();
                      while (Date.now() - started < 30 * 60 * 1000) {
                        await sleep(4000);
                        await loadProton();
                        const list = await arcaliumctl(["proton", "list", "--json"]);
                        if (pick(list, "recommendedPresent") === true) break;
                      }
                      setMsg("GE-Proton install finished (or still running in the terminal).");
                    } else {
                      setMsg(`${action}: ${str(pick(result, "name"))}`);
                    }
                    await loadProton();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : String(e));
                  } finally {
                    setInstallingProton(false);
                  }
                }}
              >
                {installingProton ? "Installing in terminal…" : "Install recommended GE-Proton"}
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => void openDesktop("com.vysp3r.ProtonPlus.desktop")}
              >
                Open ProtonPlus
              </button>
            </div>
          </article>
        )}

        {step.id === "steam" && (
          <article className="card">
            <p>
              Steam status:{" "}
              <strong>{steamApp?.installed ? "installed" : "not installed"}</strong>
            </p>
            <p className="muted">
              Arcalium does not ship Steam. Install pulls Valve&apos;s Flatpak from Flathub in a
              terminal. Steam shows the Steam Subscriber Agreement on first launch. A Steam account is
              required. Arcalium never captures or stores Steam credentials.
            </p>
            <div className="btn-row">
              {steamApp ? <AppActions app={steamApp} onChanged={() => void loadApps()} /> : null}
              <button type="button" className="btn" onClick={() => void loadApps()}>
                Refresh status
              </button>
            </div>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              Per-game Proton: Steam → game Properties → Compatibility → Force a specific Steam Play
              tool.
            </p>
          </article>
        )}

        {step.id === "storage" && storage && (
          <article className="card">
            <dl className="kv">
              <div>
                <dt>Root free</dt>
                <dd>{str(pick(storage, "root.freeGiB"))} GiB</dd>
              </div>
              <div>
                <dt>Home free</dt>
                <dd>{str(pick(storage, "home.freeGiB"))} GiB</dd>
              </div>
            </dl>
            {warnings.length > 0 && (
              <ul className="plain-list" style={{ marginTop: "0.75rem" }}>
                {warnings.map((w, i) => (
                  <li key={i}>{w.message}</li>
                ))}
              </ul>
            )}
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              Prefer Btrfs or Ext4 for game libraries. This wizard will not format disks. Add folders
              in Steam → Settings → Storage after creating them in Files.
            </p>
            <div className="btn-row">
              <button type="button" className="btn" onClick={() => void openDesktop("org.kde.dolphin.desktop")}>
                Open Files
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => {
                  void openDesktop("org.kde.partitionmanager.desktop").catch((e) => {
                    setError(
                      e instanceof Error
                        ? e.message
                        : "Could not open KDE Partition Manager.",
                    );
                  });
                }}
              >
                Open disk utility
              </button>
            </div>
          </article>
        )}

        {step.id === "vpn" && (
          <article className="card">
            <p className="muted">
              Optional. Control Centre does not import WireGuard/OpenVPN secrets — use Proton VPN&apos;s
              client or Plasma Network settings. A VPN does not improve game performance.
            </p>
            <p className="muted small">
              Network: {str(pick(network, "primaryIpv4"))} · Internet:{" "}
              {pick(network, "internetReachable") ? "reachable" : "not detected"}
            </p>
            {vpnApp && <AppActions app={vpnApp} onChanged={() => void loadApps()} />}
          </article>
        )}

        {step.id === "streaming" && (
          <>
            <article className="card">
              <p className="muted">
                Remote streaming is opt-in. Nothing is enabled automatically, and firewall ports are not
                opened for you.
              </p>
              <div className="btn-row">
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    void (async () => {
                      const st = await arcaliumctl(["steam", "status", "--json"]);
                      const desktop = str(pick(st, "desktopId"), "");
                      if (pick(st, "launchable") && desktop) {
                        await openDesktop(desktop);
                      } else {
                        await arcaliumctl(["steam", "open-download", "--json"]);
                      }
                    })();
                  }}
                >
                  Steam Remote Play guidance (open Steam)
                </button>
              </div>
            </article>
            <div className="grid two">
              {streamingApps.map((app) => (
                <article className="card" key={str(app.id)}>
                  <h2>{str(app.name)}</h2>
                  <AppActions app={app} onChanged={() => void loadApps()} />
                </article>
              ))}
            </div>
          </>
        )}

        {step.id === "validation" && diag && (
          <article className="card">
            <p>
              Result: <strong>{str(pick(diag, "overall"))}</strong>
              {pick(diag, "overall") === "ready"
                ? " — ready to game"
                : pick(diag, "overall") === "warning"
                  ? " — ready with warnings"
                  : " — action required"}
            </p>
            <ul className="plain-list">
              {diagChecks.map((c) => (
                <li key={c.title}>
                  <span className={`badge ${c.status === "ready" ? "ok" : c.status === "fail" ? "bad" : "warn"}`}>
                    {str(c.status)}
                  </span>{" "}
                  {str(c.title)}
                  {c.detail ? <span className="muted small"> — {c.detail}</span> : null}
                </li>
              ))}
            </ul>
          </article>
        )}

        {step.id === "localAi" && (
          <article className="card">
            <p>
              Optional offline helper for system maintenance questions. Uses Ollama assistant{" "}
              <span className="mono">{str(pick(aiStatus, "model.id"), "arcalium-assistant")}</span>{" "}
              (base <span className="mono">{str(pick(aiStatus, "model.baseModel"), "gemma4:e4b-it-qat")}</span>
              ) with an Arcalium OS / bash system prompt. Skip if you prefer to set this up later in
              Control Centre.
            </p>
            <dl className="kv" style={{ marginTop: "0.75rem" }}>
              <div>
                <dt>Ollama</dt>
                <dd>
                  <span className={`badge ${pick(aiStatus, "ollama.available") ? "ok" : "warn"}`}>
                    {pick(aiStatus, "ollama.available") ? "found" : "not installed"}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Model</dt>
                <dd>
                  <span className={`badge ${pick(aiStatus, "model.installed") ? "ok" : "warn"}`}>
                    {pick(aiStatus, "model.installed") ? "installed" : "not pulled"}
                  </span>
                </dd>
              </div>
            </dl>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              First pull is roughly 10 GB. Install and pull open a progress window; this step
              refreshes when they finish. When ready, a Desktop shortcut is added. Close the
              assistant window before gaming so GPU memory is freed. Chat stays on this PC — no
              cloud API.
            </p>
            <AiMinSpec status={aiStatus} />
            <div className="btn-row" style={{ marginTop: "0.75rem" }}>
              {!pick(aiStatus, "ollama.available") && (
                <button
                  type="button"
                  className="btn primary"
                  disabled={installingOllama || ensuringAi}
                  onClick={async () => {
                    setInstallingOllama(true);
                    setError(null);
                    try {
                      const result = await arcaliumctl(["ai", "install-ollama", "--visible", "--json"]);
                      if (!pick(result, "ok")) {
                        throw new Error(str(pick(result, "message"), "Could not install Ollama."));
                      }
                      setMsg(str(pick(result, "message"), "Ollama install started — watch the terminal."));
                      if (str(pick(result, "action")) === "terminal") {
                        const polled = await pollAiStatus(
                          (status) => Boolean(pick(status, "ollama.available")),
                          { onTick: setAiStatus },
                        );
                        if (polled.status) setAiStatus(polled.status);
                        setMsg(
                          polled.ok
                            ? "Ollama installed. Pull the model next."
                            : "Still waiting on the install terminal. When brew finishes, continue or Refresh.",
                        );
                      } else {
                        await loadAi();
                        setMsg(str(pick(result, "message"), "Ollama installed. Pull the model next."));
                      }
                    } catch (e) {
                      setError(e instanceof Error ? e.message : String(e));
                    } finally {
                      setInstallingOllama(false);
                    }
                  }}
                >
                  {installingOllama ? "Installing in terminal…" : "1. Install Ollama"}
                </button>
              )}
              {Boolean(pick(aiStatus, "ollama.available")) && (
              <button
                type="button"
                className="btn primary"
                disabled={
                  installingOllama ||
                  ensuringAi ||
                  Boolean(pick(aiStatus, "model.installed"))
                }
                onClick={async () => {
                  setEnsuringAi(true);
                  setError(null);
                  try {
                    const result = await arcaliumctl(["ai", "ensure", "--visible", "--json"]);
                    if (!pick(result, "ok")) {
                      throw new Error(
                        str(pick(result, "message"), "Could not pull and configure the model."),
                      );
                    }
                    setMsg(str(pick(result, "message"), "Model download started — watch the terminal."));
                    if (str(pick(result, "action")) === "terminal") {
                      const polled = await pollAiStatus(
                        (status) => Boolean(pick(status, "model.installed")),
                        { onTick: setAiStatus },
                      );
                      if (polled.status) setAiStatus(polled.status);
                      setMsg(
                        polled.ok
                          ? "Model ready — Desktop shortcut added. You can Continue, or Skip if you changed your mind."
                          : "Still waiting on the download. When the pull finishes, Continue or Refresh.",
                      );
                    } else {
                      await loadAi();
                      setMsg(
                        `${str(pick(result, "message"))} You can Continue, or Skip if you changed your mind.`,
                      );
                    }
                  } catch (e) {
                    setError(e instanceof Error ? e.message : String(e));
                  } finally {
                    setEnsuringAi(false);
                  }
                }}
              >
                {ensuringAi
                  ? "Downloading in terminal…"
                  : pick(aiStatus, "model.installed")
                    ? "Model already installed"
                    : "2. Pull and configure model"}
              </button>
              )}
              <button
                type="button"
                className="btn"
                disabled={
                  !pick(aiStatus, "ready") || ensuringAi || installingOllama
                }
                onClick={async () => {
                  try {
                    const result = await arcaliumctl(["ai", "launch", "--json"]);
                    setMsg(str(pick(result, "message")));
                  } catch (e) {
                    setError(e instanceof Error ? e.message : String(e));
                  }
                }}
              >
                Try assistant
              </button>
            </div>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              Use <strong>Skip</strong> to finish setup without Local AI, or <strong>Continue</strong> after
              installing (or if you will finish later in Control Centre).
            </p>
          </article>
        )}

        {step.id === "completion" && (
          <article className="card">
            <p>You&apos;re set. Open these when you need them:</p>
            <div className="btn-row">
              {steamApp?.installed && steamApp.desktopId ? (
                <button
                  type="button"
                  className="btn primary"
                  onClick={() => void openDesktop(String(steamApp.desktopId))}
                >
                  Open Steam
                </button>
              ) : (
                <button
                  type="button"
                  className="btn primary"
                  onClick={() =>
                    void arcaliumctl(["steam", "install", "--visible", "--json"]).then(() =>
                      void loadApps(),
                    )
                  }
                >
                  Install Steam
                </button>
              )}
              <button
                type="button"
                className="btn"
                onClick={() => void openDesktop("io.arcalium.ControlCentre.desktop")}
              >
                Open Control Centre
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => void openDesktop("io.github.kolunmi.Bazaar.desktop")}
              >
                Open Bazaar
              </button>
            </div>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              Compatibility: ProtonDB and Are We Anti-Cheat Yet? — linked from Control Centre →
              Compatibility. Known limitations live in the project docs on GitHub.
            </p>
          </article>
        )}

        {step.id === "applications" && gamingApps.length > 0 && (
          <article className="card">
            <h2>Also available: game launchers</h2>
            <p className="muted small">Steam, Heroic, Bottles and Prism are listed under Gaming in Control Centre too.</p>
          </article>
        )}

        <footer className="wizard-footer">
          <button type="button" className="btn" disabled={stepIndex === 0 || busy} onClick={goBack}>
            Back
          </button>
          <div className="btn-row">
            {step.skippable && (
              <button type="button" className="btn" disabled={busy} onClick={skip}>
                Skip
              </button>
            )}
            <button
              type="button"
              className="btn primary"
              disabled={busy}
              onClick={() => void goNext("complete")}
            >
              {step.id === "completion" ? "Finish" : step.id === "welcome" ? "Begin" : "Continue"}
            </button>
          </div>
        </footer>
      </main>
    </div>
  );
}
