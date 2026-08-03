import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop } from "../api";
import { AppActions, AppRow } from "../components/AppActions";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function StreamingPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [hostIp, setHostIp] = useState<string>("—");
  const [apps, setApps] = useState<AppRow[]>([]);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const [net, list] = await Promise.all([
        arcaliumctl(["network", "status", "--json"]),
        arcaliumctl(["apps", "list", "--json"]),
      ]);
      setHostIp(str(pick(net, "primaryIpv4")));
      const all = (pick(list, "apps") as AppRow[]) || [];
      setApps(all.filter((a) => ((a as { roles?: string[] }).roles || []).includes("streaming")));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Streaming</h1>
          <p className="muted">Opt-in game streaming tools. Nothing is enabled automatically.</p>
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
            <h2>Host address</h2>
            <p className="mono">{hostIp}</p>
            <p className="muted small">
              Give this address to Moonlight clients on your LAN. Opening firewall ports is a manual,
              opt-in step — Control Centre will not change firewall rules.
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
                  Open Steam (Remote Play)
                </button>
            </div>
          </article>
          <div className="grid two">
            {apps.map((app) => (
              <article className="card" key={str(app.id)}>
                <h2>{str(app.name)}</h2>
                <p className="muted small">{app.installed ? "Installed" : "Not installed"}</p>
                <AppActions app={app} onChanged={() => void refresh()} />
              </article>
            ))}
          </div>
          <article className="card">
            <h2>Sunshine notes</h2>
            <p className="muted small">
              After installing Sunshine, check its documentation for one extra setup step some
              systems need. Prefer keeping streaming off when you are not using it, and avoid exposing
              a streaming host on public networks.
            </p>
          </article>
        </>
      )}
    </div>
  );
}
