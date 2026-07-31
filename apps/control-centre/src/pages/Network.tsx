import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { AppActions, AppRow } from "../components/AppActions";
import { pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

export function NetworkPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [net, setNet] = useState<JsonValue | null>(null);
  const [vpnApp, setVpnApp] = useState<AppRow | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const [n, apps] = await Promise.all([
        arcaliumctl(["network", "status", "--json"]),
        arcaliumctl(["apps", "list", "--json"]),
      ]);
      setNet(n);
      const list = (pick(apps, "apps") as AppRow[]) || [];
      setVpnApp(list.find((a) => a.id === "protonvpn") || null);
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const conns = (pick(net, "networkManager.activeConnections") as { name?: string; type?: string; device?: string }[]) || [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Network and VPN</h1>
          <p className="muted">Connection status and optional Proton VPN client.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>
      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {state === "ready" && (
        <>
          <div className="grid two">
            <article className="card">
              <h2>Status</h2>
              <dl className="kv">
                <div>
                  <dt>Hostname</dt>
                  <dd>{str(pick(net, "hostname"))}</dd>
                </div>
                <div>
                  <dt>IPv4</dt>
                  <dd className="mono">{str(pick(net, "primaryIpv4"))}</dd>
                </div>
                <div>
                  <dt>Internet</dt>
                  <dd>{pick(net, "internetReachable") ? "reachable" : "not detected"}</dd>
                </div>
                <div>
                  <dt>DNS</dt>
                  <dd className="mono small">{((pick(net, "dnsServers") as string[]) || []).join(", ") || "—"}</dd>
                </div>
                <div>
                  <dt>VPN</dt>
                  <dd>{pick(net, "vpn.active") ? "active (hint)" : "not detected"}</dd>
                </div>
              </dl>
              <p className="muted small">{str(pick(net, "vpn.note"))}</p>
            </article>
            <article className="card">
              <h2>Actions</h2>
              <div className="btn-row">
                <button type="button" className="btn" onClick={() => void openDesktop("systemsettings.desktop")}>
                  Open Network settings
                </button>
              </div>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                Control Centre does not import VPN secrets or <span className="mono">.ovpn</span> files.
                Use Proton VPN&apos;s own client or Plasma Network settings for configuration and disconnect.
              </p>
            </article>
          </div>

          <article className="card">
            <h2>Active connections</h2>
            {conns.length === 0 ? (
              <p className="muted">No NetworkManager active connections reported.</p>
            ) : (
              <ul className="plain-list">
                {conns.map((c, i) => (
                  <li key={i}>
                    {str(c.name)} · {str(c.type)} · {str(c.device)}
                  </li>
                ))}
              </ul>
            )}
          </article>

          {vpnApp && (
            <article className="card">
              <h2>Proton VPN</h2>
              <AppActions app={vpnApp} onChanged={() => void refresh()} />
            </article>
          )}
        </>
      )}
    </div>
  );
}
