import { useCallback, useEffect, useState } from "react";
import { arcaliumctl } from "../api";
import { AppActions, AppRow } from "../components/AppActions";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function GamingPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [apps, setApps] = useState<AppRow[]>([]);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const data = await arcaliumctl(["apps", "list", "--json"]);
      const list = (pick(data, "apps") as AppRow[]) || [];
      setApps(list.filter((a) => ((a as { roles?: string[] }).roles || []).includes("gaming") || a.category === "gaming"));
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
          <h1>Gaming</h1>
          <p className="muted">Launchers for Steam, Epic/GOG/Amazon, Bottles and Minecraft.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>
      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {state === "ready" && (
        <div className="grid two">
          {apps.map((app) => (
            <article className="card" key={str(app.id)}>
              <h2>{str(app.name)}</h2>
              <p className="muted small">
                {app.installed ? `Installed (${str(app.installScope, "local")})` : "Not installed"}
                {app.type === "flatpak" ? ` · ${str(app.sourceId)}` : " · OS package / desktop entry"}
              </p>
              <AppActions app={app} onChanged={() => void refresh()} />
            </article>
          ))}
        </div>
      )}
      <article className="card">
        <h2>Notes</h2>
        <p className="muted small">
          Flatpak installs use <span className="mono">--user</span> so they do not need root. System-bundled
          apps (from the ISO) stay system-scoped. Arcalium does not edit launcher configs without a backup.
          Lutris is not offered — use Heroic for non-Steam stores.
        </p>
      </article>
    </div>
  );
}
