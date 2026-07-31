import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, JsonValue } from "../api";
import { copyText, pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function DiagnosticsPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      setData(await arcaliumctl(["diagnostics", "run", "--json"]));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const writeBundle = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const result = await arcaliumctl(["diagnostics", "bundle", "--json"]);
      setMsg(`Support bundle written to ${str(pick(result, "path"))}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const checks =
    (pick(data, "checks") as { id?: string; title?: string; status?: string; detail?: string }[]) || [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Diagnostics</h1>
          <p className="muted">
            Overall: <strong>{str(pick(data, "overall"), state === "loading" ? "…" : "—")}</strong>
          </p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()}>
          Re-run
        </button>
      </header>
      {state === "loading" && <p className="muted">Running checks…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {msg && <p className="banner ok">{msg}</p>}
      {state === "ready" && (
        <>
          <article className="card">
            <h2>Health checks</h2>
            <ul className="plain-list">
              {checks.map((c) => (
                <li key={c.id}>
                  <span className={`badge ${c.status === "ready" ? "ok" : c.status === "fail" ? "bad" : "warn"}`}>
                    {str(c.status)}
                  </span>{" "}
                  {str(c.title)}
                  {c.detail ? <span className="muted small"> — {c.detail}</span> : null}
                </li>
              ))}
            </ul>
          </article>
          <article className="card">
            <h2>Support bundle</h2>
            <p className="muted small">
              Writes a redacted JSON report under <span className="mono">~/.local/state/arcalium/</span>. No
              passwords or tokens are intentionally included.
            </p>
            <div className="btn-row">
              <button type="button" className="btn primary" disabled={busy} onClick={() => void writeBundle()}>
                {busy ? "Writing…" : "Generate support bundle"}
              </button>
              <button
                type="button"
                className="btn"
                onClick={async () => {
                  await copyText(JSON.stringify(data, null, 2));
                  setMsg("Full diagnostics JSON copied.");
                }}
              >
                Copy report
              </button>
            </div>
          </article>
        </>
      )}
    </div>
  );
}
