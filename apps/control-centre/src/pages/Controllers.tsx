import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function ControllersPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      setData(await arcaliumctl(["controllers", "list", "--json"]));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const pads =
    (pick(data, "controllers") as {
      name?: string;
      connection?: string;
      family?: string;
      path?: string;
    }[]) || [];
  const hints = (pick(data, "hints") as string[]) || [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Controllers</h1>
          <p className="muted">Connected gamepads and basic setup links.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>
      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {state === "ready" && (
        <>
          <article className="card">
            <h2>Detected ({str(pick(data, "count"), "0")})</h2>
            {pads.length === 0 ? (
              <p className="muted">No joysticks/gamepads found under /dev/input.</p>
            ) : (
              <ul className="plain-list">
                {pads.map((p, i) => (
                  <li key={i}>
                    <strong>{str(p.name)}</strong> · {str(p.family)} · {str(p.connection)}
                    <div className="muted small mono">{str(p.path)}</div>
                  </li>
                ))}
              </ul>
            )}
          </article>
          <article className="card">
            <h2>Actions</h2>
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
                  Open Steam (Controller / Steam Input)
                </button>
              <button
                type="button"
                className="btn"
                onClick={() => void openDesktop("systemsettings.desktop")}
              >
                Open System Settings (Bluetooth)
              </button>
            </div>
            <ul className="plain-list muted small" style={{ marginTop: "0.75rem" }}>
              {hints.map((h) => (
                <li key={h}>{h}</li>
              ))}
              <li>If a pad is missing: reseat USB, re-pair Bluetooth, then Refresh.</li>
              <li>Test buttons in Steam → Settings → Controller → Test Device Inputs when available.</li>
            </ul>
          </article>
        </>
      )}
    </div>
  );
}
