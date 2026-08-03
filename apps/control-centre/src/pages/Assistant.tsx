import { useCallback, useEffect, useRef, useState } from "react";
import { arcaliumctl, JsonValue } from "../api";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

/** Poll ai status until a condition is met or the budget expires. */
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

export function AssistantPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<"install" | "ensure" | "launch" | "stop" | null>(null);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    return () => {
      cancelled.current = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      setData(await arcaliumctl(["ai", "status", "--json"]));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const runInstall = async () => {
    setBusy("install");
    setMsg(null);
    setError(null);
    try {
      const result = await arcaliumctl(["ai", "install-ollama", "--visible", "--json"]);
      if (!pick(result, "ok")) throw new Error(str(pick(result, "message"), "Could not install Ollama."));
      setMsg(str(pick(result, "message"), "Ollama install started — watch the terminal."));

      if (str(pick(result, "action")) === "terminal") {
        const polled = await pollAiStatus((status) => Boolean(pick(status, "ollama.available")), {
          onTick: (status) => {
            if (!cancelled.current) setData(status);
          },
        });
        if (cancelled.current) return;
        if (polled.status) {
          setData(polled.status);
          setState("ready");
        }
        if (polled.ok) {
          setMsg("Ollama installed. Next, pull and configure the model.");
        } else {
          setMsg(
            "Still waiting on the install terminal. When brew finishes, click Refresh — or pull the model if Ollama already shows as found.",
          );
        }
      } else {
        setData(await arcaliumctl(["ai", "status", "--json"]));
        setMsg(str(pick(result, "message"), "Ollama installed. Pull the model next."));
        setState("ready");
      }
    } catch (e) {
      if (!cancelled.current) setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (!cancelled.current) setBusy(null);
    }
  };

  const runEnsure = async () => {
    setBusy("ensure");
    setMsg(null);
    setError(null);
    try {
      const result = await arcaliumctl(["ai", "ensure", "--visible", "--json"]);
      if (!pick(result, "ok")) throw new Error(str(pick(result, "message"), "Could not configure model."));
      setMsg(str(pick(result, "message"), "Model download started — watch the terminal."));

      if (str(pick(result, "action")) === "terminal") {
        const polled = await pollAiStatus((status) => Boolean(pick(status, "model.installed")), {
          onTick: (status) => {
            if (!cancelled.current) setData(status);
          },
        });
        if (cancelled.current) return;
        if (polled.status) {
          setData(polled.status);
          setState("ready");
        }
        if (polled.ok) {
          setMsg("Model ready. You can Launch assistant.");
        } else {
          setMsg(
            "Still waiting on the download terminal. When the pull finishes, click Refresh.",
          );
        }
      } else {
        setData(await arcaliumctl(["ai", "status", "--json"]));
        setMsg(str(pick(result, "message"), "Model ready."));
        setState("ready");
      }
    } catch (e) {
      if (!cancelled.current) setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (!cancelled.current) setBusy(null);
    }
  };

  const runRefreshAgent = async () => {
    setBusy("ensure");
    setMsg(null);
    setError(null);
    try {
      // Silent ensure recreates arcalium-assistant with the current system prompt.
      const result = await arcaliumctl(["ai", "ensure", "--json"]);
      if (!pick(result, "ok")) {
        throw new Error(str(pick(result, "message"), "Could not refresh assistant."));
      }
      setData(await arcaliumctl(["ai", "status", "--json"]));
      setMsg(str(pick(result, "message"), "Assistant agent prompt refreshed."));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const runLaunch = async () => {
    setBusy("launch");
    setMsg(null);
    setError(null);
    try {
      const result = await arcaliumctl(["ai", "launch", "--json"]);
      setMsg(str(pick(result, "message"), "Assistant terminal opened."));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
      void refresh();
    }
  };

  const runStop = async () => {
    setBusy("stop");
    setMsg(null);
    setError(null);
    try {
      const result = await arcaliumctl(["ai", "stop", "--json"]);
      setData(await arcaliumctl(["ai", "status", "--json"]));
      setMsg(str(pick(result, "message"), "Model unload requested."));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const ollamaOk = Boolean(pick(data, "ollama.available"));
  const modelOk = Boolean(pick(data, "model.installed"));
  const loaded = Boolean(pick(data, "model.loaded"));
  const ready = Boolean(pick(data, "ready"));

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Local AI Assistant</h1>
          <p className="muted">
            Offline agentic helper. Assistant{" "}
            <span className="mono">{str(pick(data, "model.id"), "arcalium-assistant")}</span>{" "}
            (base <span className="mono">{str(pick(data, "model.baseModel"), "gemma4:e4b-it-qat")}</span>
            ) can run allowlisted <span className="mono">arcaliumctl</span> checks itself and asks
            before installs or updates.
          </p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()} disabled={busy !== null}>
          Refresh
        </button>
      </header>
      {state === "loading" && <p className="muted">Checking Ollama…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {msg && <p className="banner ok">{msg}</p>}
      {error && state === "ready" && <p className="banner bad">{error}</p>}
      {state === "ready" && (
        <>
          <div className="grid two">
            <article className="card">
              <h2>Status</h2>
              <dl className="kv">
                <div>
                  <dt>Ollama</dt>
                  <dd>
                    <span className={`badge ${ollamaOk ? "ok" : "warn"}`}>{ollamaOk ? "found" : "missing"}</span>
                    {ollamaOk ? (
                      <span className="muted small mono"> {str(pick(data, "ollama.path"))}</span>
                    ) : null}
                  </dd>
                </div>
                <div>
                  <dt>Local server</dt>
                  <dd>
                    <span className={`badge ${pick(data, "ollama.serverRunning") ? "ok" : "warn"}`}>
                      {pick(data, "ollama.serverRunning") ? "running" : "stopped"}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>Model</dt>
                  <dd>
                    <span className={`badge ${modelOk ? "ok" : "warn"}`}>
                      {modelOk ? "installed" : "not pulled"}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>In GPU memory</dt>
                  <dd>
                    <span className={`badge ${loaded ? "warn" : "ok"}`}>{loaded ? "loaded" : "unloaded"}</span>
                  </dd>
                </div>
                <div>
                  <dt>Ready</dt>
                  <dd>
                    <span className={`badge ${ready ? "ok" : "warn"}`}>{ready ? "yes" : "no"}</span>
                  </dd>
                </div>
              </dl>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                {str(pick(data, "gamingNotice"))}
              </p>
            </article>
            <article className="card">
              <h2>Actions</h2>
              <div className="btn-row" style={{ flexWrap: "wrap" }}>
                {!ollamaOk && (
                  <button
                    type="button"
                    className="btn primary"
                    disabled={busy !== null}
                    onClick={() => void runInstall()}
                  >
                    {busy === "install" ? "Installing in terminal…" : "1. Install Ollama"}
                  </button>
                )}
                {ollamaOk && !modelOk && (
                  <button
                    type="button"
                    className="btn primary"
                    disabled={busy !== null}
                    onClick={() => void runEnsure()}
                  >
                    {busy === "ensure" ? "Downloading in terminal…" : "2. Pull and configure model"}
                  </button>
                )}
                {ollamaOk && modelOk && (
                  <button
                    type="button"
                    className="btn"
                    disabled={busy !== null}
                    onClick={() => void runRefreshAgent()}
                  >
                    {busy === "ensure" ? "Refreshing…" : "Refresh agent prompt"}
                  </button>
                )}
                <button
                  type="button"
                  className="btn primary"
                  disabled={busy !== null || !ready}
                  onClick={() => void runLaunch()}
                >
                  {busy === "launch" ? "Opening…" : "Launch assistant"}
                </button>
                <button
                  type="button"
                  className="btn"
                  disabled={busy !== null || !ollamaOk}
                  onClick={() => void runStop()}
                >
                  {busy === "stop" ? "Stopping…" : "Unload model"}
                </button>
              </div>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                Install and pull open a progress window (~10 GB for the first model). When the model
                is ready, a Desktop shortcut with the pixel-art invader icon is added for quick
                launch. Closing the assistant window frees the GPU.{" "}
                {str(pick(data, "guidance.note"))}
              </p>
            </article>
          </div>
        </>
      )}
    </div>
  );
}
