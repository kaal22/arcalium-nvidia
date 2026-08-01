import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";

type LoadState = "loading" | "ready" | "error";

function pick(obj: JsonValue | null | unknown, path: string): unknown {
  if (!obj || typeof obj !== "object") return undefined;
  return path.split(".").reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && key in (acc as object)) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

function str(v: unknown, fallback = "—"): string {
  if (v === null || v === undefined || v === "") return fallback;
  return String(v);
}

function statusClass(overall: unknown): string {
  if (overall === "ready") return "ok";
  if (overall === "warning" || overall === "unknown") return "warn";
  return "bad";
}

export function OverviewPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<JsonValue | null>(null);
  const [gpu, setGpu] = useState<JsonValue | null>(null);
  const [validate, setValidate] = useState<JsonValue | null>(null);
  const [vulkan, setVulkan] = useState<JsonValue | null>(null);
  const [installingProton, setInstallingProton] = useState(false);
  const [protonActionMsg, setProtonActionMsg] = useState<string | null>(null);
  const [protonActionErr, setProtonActionErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const [s, g, v, vk] = await Promise.all([
        arcaliumctl(["system", "summary", "--json"]),
        arcaliumctl(["gpu", "status", "--json"]),
        arcaliumctl(["gpu", "validate", "--json"]),
        arcaliumctl(["vulkan", "test", "--json"]),
      ]);
      setSummary(s);
      setGpu(g);
      setValidate(v);
      setVulkan(vk);
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
    setProtonActionMsg(null);
    setProtonActionErr(null);
    try {
      const result = await arcaliumctl(["proton", "install-recommended", "--json"]);
      const action = str(pick(result, "action"), "done");
      const name = str(pick(result, "name"), "GE-Proton");
      if (action === "already_present") {
        setProtonActionMsg(`${name} is already installed.`);
      } else {
        setProtonActionMsg(`Installed ${name}. See Compatibility for details.`);
      }
    } catch (e) {
      setProtonActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setInstallingProton(false);
    }
  }, []);

  const smiGpus = (pick(gpu, "nvidiaSmi.gpus") as JsonValue[] | undefined) || [];
  const primarySmi = smiGpus[0] || null;
  const overall = pick(validate, "overall");
  const checks = (pick(validate, "checks") as JsonValue[] | undefined) || [];
  const failedChecks = checks.filter((c) => {
    const s = pick(c, "status");
    return s === "unsupported" || s === "fail";
  });
  const vulkanOk = pick(vulkan, "available") === true && pick(vulkan, "hasNvidiaDevice") === true;
  const nvidiaDevices = (pick(vulkan, "nvidiaDevices") as string[] | undefined) || [];
  const modules = (pick(gpu, "nvidiaModulesLoaded") as string[] | undefined) || [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Overview</h1>
          <p className="muted">Hardware and image status from arcaliumctl.</p>
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

      <section className="grid">
        <article className="card">
          <h2>System</h2>
          <dl>
            <div>
              <dt>Product</dt>
              <dd>
                {str(pick(summary, "product"))} ({str(pick(summary, "edition"))})
              </dd>
            </div>
            <div>
              <dt>Image</dt>
              <dd>
                {str(pick(summary, "imageName"))}:{str(pick(summary, "channel"))}
              </dd>
            </div>
            <div>
              <dt>Hostname</dt>
              <dd>{str(pick(summary, "hostname"))}</dd>
            </div>
            <div>
              <dt>Kernel</dt>
              <dd>{str(pick(summary, "kernel"))}</dd>
            </div>
            <div>
              <dt>CPU</dt>
              <dd>{str(pick(summary, "cpuModel"))}</dd>
            </div>
            <div>
              <dt>Memory</dt>
              <dd>{str(pick(summary, "memoryGiB"))} GiB</dd>
            </div>
            <div>
              <dt>Session</dt>
              <dd>{str(pick(summary, "sessionType"))}</dd>
            </div>
          </dl>
        </article>

        <article className="card">
          <h2>GPU</h2>
          <dl>
            <div>
              <dt>Name</dt>
              <dd>{str(pick(gpu, "primaryGpuName"))}</dd>
            </div>
            <div>
              <dt>Driver</dt>
              <dd>{str(pick(gpu, "driverVersion") ?? pick(primarySmi, "driverVersion"))}</dd>
            </div>
            <div>
              <dt>VRAM</dt>
              <dd>{str(pick(primarySmi, "memoryTotal"))}</dd>
            </div>
            <div>
              <dt>Modules</dt>
              <dd>{modules.length ? modules.join(", ") : "—"}</dd>
            </div>
            <div>
              <dt>Validate</dt>
              <dd className={statusClass(overall)}>{str(overall, "—")}</dd>
            </div>
          </dl>
          {failedChecks.length > 0 && (
            <ul className="errors">
              {failedChecks.map((c, i) => (
                <li key={i}>
                  {str(pick(c, "code"))}: {str(pick(c, "title"))}
                  {pick(c, "detail") ? ` — ${str(pick(c, "detail"))}` : ""}
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="card">
          <h2>Vulkan</h2>
          <dl>
            <div>
              <dt>Status</dt>
              <dd className={vulkanOk ? "ok" : "bad"}>{vulkanOk ? "OK" : "Failed"}</dd>
            </div>
            <div>
              <dt>API</dt>
              <dd>{str(pick(vulkan, "apiVersion"))}</dd>
            </div>
            <div>
              <dt>Device</dt>
              <dd>{nvidiaDevices[0] || str(pick(vulkan, "error") ?? pick(vulkan, "detail"))}</dd>
            </div>
          </dl>
          {Boolean(pick(vulkan, "error")) && (
            <ul className="errors">
              <li>{str(pick(vulkan, "error"))}</li>
            </ul>
          )}
        </article>
      </section>

      {(protonActionMsg || protonActionErr) && (
        <div className={protonActionErr ? "banner error" : "banner ok"}>
          <strong>{protonActionErr ? "Proton install failed." : protonActionMsg}</strong>
          {protonActionErr && <div>{protonActionErr}</div>}
        </div>
      )}

      <section className="actions">
        <h2>Quick actions</h2>
        <div className="action-row">
          <button type="button" className="btn" onClick={() => void openDesktop("steam.desktop")}>
            Launch Steam
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => void openDesktop("io.github.kolunmi.Bazaar.desktop")}
          >
            Open Bazaar
          </button>
          <button
            type="button"
            className="btn primary"
            disabled={installingProton}
            onClick={() => void installProton()}
          >
            {installingProton ? "Installing Proton-GE…" : "Install Proton-GE"}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => void openDesktop("systemsettings.desktop")}
          >
            System Settings
          </button>
        </div>
        <p className="muted small">
          Launches allowlisted apps via gio launch (not xdg-open — that opened
          the .desktop file in Kate). Install Proton-GE downloads the latest
          GE-Proton into Heroic&apos;s tools directory (same as Compatibility). Add
          game drive and health-check actions arrive with later pages.
        </p>
      </section>
    </div>
  );
}
