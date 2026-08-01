import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, JsonValue } from "../api";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";
type BusyAction = "check" | "apply" | "rollback" | "reboot" | null;

export function UpdatesPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<BusyAction>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      setData(await arcaliumctl(["updates", "status", "--json"]));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const run = async (action: Exclude<BusyAction, null>) => {
    setBusy(action);
    setMsg(null);
    setError(null);
    try {
      const result = await arcaliumctl(["updates", action, "--json"]);
      if (!pick(result, "ok")) {
        throw new Error(str(pick(result, "message"), `Could not start ${action}.`));
      }
      setMsg(str(pick(result, "message")));
      if (action === "check") {
        void refresh();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const booted = pick(data, "bootc.booted") as JsonValue | null;
  const staged = pick(data, "bootc.staged") as JsonValue | null;
  const rollbackDep = pick(data, "bootc.rollback") as JsonValue | null;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Updates and Recovery</h1>
          <p className="muted">
            bootc deployments — Check, Apply, and Rollback open a terminal so sudo can ask for your
            password and show progress.
          </p>
        </div>
        <button type="button" className="btn" disabled={busy !== null} onClick={() => void refresh()}>
          Refresh status
        </button>
      </header>
      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {msg && <p className="banner ok">{msg}</p>}
      {error && state === "ready" && <p className="banner bad">{error}</p>}
      {state === "ready" && (
        <>
          <div className="grid two">
            <article className="card">
              <h2>Current image</h2>
              <dl className="kv">
                <div>
                  <dt>Product</dt>
                  <dd>{str(pick(data, "product"))}</dd>
                </div>
                <div>
                  <dt>Image</dt>
                  <dd className="mono">
                    {str(pick(data, "imageName"))}:{str(pick(data, "channel"))}
                  </dd>
                </div>
                <div>
                  <dt>Kernel</dt>
                  <dd className="mono">{str(pick(data, "kernel"))}</dd>
                </div>
                <div>
                  <dt>Booted</dt>
                  <dd className="mono small">{str(pick(booted, "image"))}</dd>
                </div>
                <div>
                  <dt>Digest</dt>
                  <dd className="mono small">{str(pick(booted, "digest"))}</dd>
                </div>
                <div>
                  <dt>Pinned</dt>
                  <dd>{pick(booted, "pinned") ? "yes" : "no"}</dd>
                </div>
              </dl>
            </article>
            <article className="card">
              <h2>Other deployments</h2>
              <dl className="kv">
                <div>
                  <dt>Staged</dt>
                  <dd className="mono small">{str(pick(staged, "image"), "none")}</dd>
                </div>
                <div>
                  <dt>Rollback</dt>
                  <dd className="mono small">{str(pick(rollbackDep, "image"), "none")}</dd>
                </div>
              </dl>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                {str(pick(data, "guidance.note"))}
              </p>
            </article>
          </div>
          <article className="card">
            <h2>Actions</h2>
            <div className="btn-row">
              <button
                type="button"
                className={`btn primary${busy === "check" ? " working" : ""}`}
                disabled={busy !== null}
                onClick={() => void run("check")}
              >
                {busy === "check" ? "Opening…" : "Check for updates"}
              </button>
              <button
                type="button"
                className={`btn primary${busy === "apply" ? " working" : ""}`}
                disabled={busy !== null}
                onClick={() => void run("apply")}
              >
                {busy === "apply" ? "Opening…" : "Apply update and reboot"}
              </button>
              <button
                type="button"
                className={`btn${busy === "rollback" ? " working" : ""}`}
                disabled={busy !== null}
                onClick={() => void run("rollback")}
              >
                {busy === "rollback" ? "Opening…" : "Rollback and reboot"}
              </button>
              <button
                type="button"
                className={`btn${busy === "reboot" ? " working" : ""}`}
                disabled={busy !== null}
                onClick={() => void run("reboot")}
              >
                {busy === "reboot" ? "Opening…" : "Reboot"}
              </button>
            </div>
            <p className="muted small" style={{ marginTop: "0.5rem" }}>
              Apply and rollback ask you to type <span className="mono">yes</span> in the terminal
              before running. Commands used:
            </p>
            <ul className="plain-list mono small">
              <li>{str(pick(data, "guidance.check"))}</li>
              <li>{str(pick(data, "guidance.apply"))}</li>
              <li>{str(pick(data, "guidance.rollback"))}</li>
              <li>{str(pick(data, "guidance.reboot"))}</li>
            </ul>
          </article>
        </>
      )}
    </div>
  );
}
