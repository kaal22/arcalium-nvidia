import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { copyText, pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function GpuPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [gpu, setGpu] = useState<JsonValue | null>(null);
  const [validate, setValidate] = useState<JsonValue | null>(null);
  const [vulkan, setVulkan] = useState<JsonValue | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);
  const [testingVk, setTestingVk] = useState(false);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const [g, v, vk] = await Promise.all([
        arcaliumctl(["gpu", "status", "--json"]),
        arcaliumctl(["gpu", "validate", "--json"]),
        arcaliumctl(["vulkan", "test", "--json"]),
      ]);
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

  const copyReport = useCallback(async () => {
    setActionMsg(null);
    setActionErr(null);
    try {
      await copyText(JSON.stringify({ gpu, validate, vulkan }, null, 2));
      setActionMsg("GPU report copied to the clipboard.");
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    }
  }, [gpu, validate, vulkan]);

  const runVulkan = useCallback(async () => {
    setTestingVk(true);
    setActionMsg(null);
    setActionErr(null);
    try {
      const vk = await arcaliumctl(["vulkan", "test", "--json"]);
      setVulkan(vk);
      setActionMsg(
        pick(vk, "hasNvidiaDevice")
          ? "Vulkan test OK — NVIDIA device visible."
          : "Vulkan test finished — see details below.",
      );
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setTestingVk(false);
    }
  }, []);

  const nvidiaDesktop = str(pick(gpu, "nvidiaSettingsDesktop"), "");

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>GPU and Display</h1>
          <p className="muted">Driver, session and Vulkan status for this NVIDIA edition.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()} disabled={state === "loading"}>
          Refresh
        </button>
      </header>

      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {actionMsg && <p className="banner ok">{actionMsg}</p>}
      {actionErr && <p className="banner bad">{actionErr}</p>}

      {state === "ready" && (
        <>
          <div className="grid two">
            <article className="card">
              <h2>GPU</h2>
              <dl className="kv">
                <div>
                  <dt>Model</dt>
                  <dd>{str(pick(gpu, "primaryGpuName"))}</dd>
                </div>
                <div>
                  <dt>Driver</dt>
                  <dd>{str(pick(gpu, "driverVersion"))}</dd>
                </div>
                <div>
                  <dt>Modules</dt>
                  <dd className="mono">
                    {((pick(gpu, "nvidiaModulesLoaded") as string[]) || []).join(", ") || "—"}
                  </dd>
                </div>
                <div>
                  <dt>VRAM</dt>
                  <dd>
                    {str(pick(gpu, "memoryUsed"))} / {str(pick(gpu, "memoryTotal"))} MiB
                  </dd>
                </div>
                <div>
                  <dt>Utilisation</dt>
                  <dd>{str(pick(gpu, "utilizationGpu"))}%</dd>
                </div>
                <div>
                  <dt>Temperature</dt>
                  <dd>{str(pick(gpu, "temperatureC"))} °C</dd>
                </div>
                <div>
                  <dt>Power</dt>
                  <dd>{str(pick(gpu, "powerDrawW"))} W</dd>
                </div>
                <div>
                  <dt>Validation</dt>
                  <dd>{str(pick(validate, "overall"))}</dd>
                </div>
              </dl>
            </article>

            <article className="card">
              <h2>Display session</h2>
              <dl className="kv">
                <div>
                  <dt>Session</dt>
                  <dd>{str(pick(gpu, "sessionType"))}</dd>
                </div>
                <div>
                  <dt>Wayland</dt>
                  <dd>{pick(gpu, "waylandDisplay") ? "yes" : "no"}</dd>
                </div>
                <div>
                  <dt>Vulkan available</dt>
                  <dd>{pick(vulkan, "available") ? "yes" : "no"}</dd>
                </div>
                <div>
                  <dt>NVIDIA Vulkan</dt>
                  <dd>{pick(vulkan, "hasNvidiaDevice") ? "yes" : "no"}</dd>
                </div>
                <div>
                  <dt>Vulkan devices</dt>
                  <dd className="mono small">
                    {((pick(vulkan, "nvidiaDevices") as string[]) || []).join(", ") ||
                      ((pick(vulkan, "devices") as string[]) || []).slice(0, 3).join(", ") ||
                      "—"}
                  </dd>
                </div>
              </dl>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                VRR and HDR depend on the panel and Plasma display settings. Use Display settings
                below to inspect refresh rate and colour profile. Hardware encoding availability is
                reflected by active encoder sessions when games or streamers are running.
              </p>
            </article>
          </div>

          <article className="card">
            <h2>Actions</h2>
            <div className="btn-row">
              <button type="button" className="btn" onClick={() => void copyReport()}>
                Copy GPU report
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => void openDesktop("systemsettings.desktop")}
              >
                Open Display settings
              </button>
              <button
                type="button"
                className="btn"
                disabled={testingVk}
                onClick={() => void runVulkan()}
              >
                {testingVk ? "Running Vulkan…" : "Run Vulkan test"}
              </button>
              {nvidiaDesktop ? (
                <button
                  type="button"
                  className="btn"
                  onClick={() => void openDesktop(nvidiaDesktop)}
                >
                  Open NVIDIA settings
                </button>
              ) : null}
            </div>
            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              On Wayland, legacy <span className="mono">nvidia-settings</span> may be limited or
              absent. Prefer Plasma Display settings for monitors. Automatic overclocking is not
              offered.
            </p>
            <p className="muted small">
              Known NVIDIA + Wayland notes:{" "}
              <a
                href="https://wiki.archlinux.org/title/NVIDIA"
                target="_blank"
                rel="noreferrer"
              >
                ArchWiki NVIDIA
              </a>
              .
            </p>
          </article>
        </>
      )}
    </div>
  );
}
