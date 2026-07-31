import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, JsonValue } from "../api";
import { copyText, pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function UpdatesPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

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

  const booted = pick(data, "bootc.booted") as JsonValue | null;
  const staged = pick(data, "bootc.staged") as JsonValue | null;
  const rollback = pick(data, "bootc.rollback") as JsonValue | null;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Updates and Recovery</h1>
          <p className="muted">bootc deployments — apply and rollback stay in the terminal for now.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()}>
          Check status
        </button>
      </header>
      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {msg && <p className="banner ok">{msg}</p>}
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
                  <dd className="mono small">{str(pick(rollback, "image"), "none")}</dd>
                </div>
              </dl>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                {str(pick(data, "guidance.note"))}
              </p>
            </article>
          </div>
          <article className="card">
            <h2>Commands (copy into Konsole)</h2>
            <ul className="plain-list mono small">
              <li>{str(pick(data, "guidance.check"))}</li>
              <li>{str(pick(data, "guidance.apply"))}</li>
              <li>{str(pick(data, "guidance.rollback"))}</li>
            </ul>
            <div className="btn-row" style={{ marginTop: "0.75rem" }}>
              <button
                type="button"
                className="btn"
                onClick={async () => {
                  await copyText(
                    [
                      str(pick(data, "guidance.check")),
                      str(pick(data, "guidance.apply")),
                      str(pick(data, "guidance.rollback")),
                    ].join("\n"),
                  );
                  setMsg("Update commands copied.");
                }}
              >
                Copy commands
              </button>
            </div>
          </article>
        </>
      )}
    </div>
  );
}
