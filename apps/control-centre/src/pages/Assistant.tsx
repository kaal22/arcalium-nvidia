import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, JsonValue } from "../api";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function AssistantPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<"install" | "ensure" | "launch" | "stop" | null>(null);

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
      const result = await arcaliumctl(["ai", "install-ollama", "--json"]);
      setData(await arcaliumctl(["ai", "status", "--json"]));
      if (!pick(result, "ok")) throw new Error(str(pick(result, "message"), "Could not install Ollama."));
      setMsg(str(pick(result, "message"), "Ollama installed. Pull the model next."));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const runEnsure = async () => {
    setBusy("ensure");
    setMsg(null);
    setError(null);
    try {
      const result = await arcaliumctl(["ai", "ensure", "--json"]);
      setData(await arcaliumctl(["ai", "status", "--json"]));
      if (!pick(result, "ok")) throw new Error(str(pick(result, "message"), "Could not configure model."));
      setMsg(str(pick(result, "message"), pick(result, "ok") ? "Model ready." : "Could not ensure model."));
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
            Offline Ollama helper for maintenance questions. Assistant{" "}
            <span className="mono">{str(pick(data, "model.id"), "arcalium-assistant")}</span>{" "}
            (base <span className="mono">{str(pick(data, "model.baseModel"), "gemma4:e4b-it-qat")}</span>
            ) with an Arcalium OS / bash system prompt.
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
                    {busy === "install" ? "Installing Ollama…" : "1. Install Ollama"}
                  </button>
                )}
                {ollamaOk && !modelOk && (
                  <button
                    type="button"
                    className="btn primary"
                    disabled={busy !== null}
                    onClick={() => void runEnsure()}
                  >
                    {busy === "ensure" ? "Pulling model…" : "2. Pull and configure model"}
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
                {str(pick(data, "guidance.note"))}
              </p>
            </article>
          </div>
        </>
      )}
    </div>
  );
}
