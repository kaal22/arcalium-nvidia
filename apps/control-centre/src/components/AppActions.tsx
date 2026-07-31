import { useState } from "react";
import { arcaliumctl, openDesktop } from "../api";
import { str } from "../lib/json";

export type AppRow = {
  id?: string;
  name?: string;
  type?: string;
  sourceId?: string | null;
  desktopId?: string | null;
  installed?: boolean;
  installScope?: string | null;
  licenceNotice?: string | null;
  website?: string | null;
  dataDir?: string | null;
  launchable?: boolean;
  category?: string;
};

export function AppActions({
  app,
  onChanged,
}: {
  app: AppRow;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const id = str(app.id, "");
  const desktop = str(app.desktopId, "");

  const install = async () => {
    setBusy(true);
    setMsg(null);
    setErr(null);
    try {
      const result = await arcaliumctl(["apps", "install", id, "--json"]);
      setMsg(`${str(result.action)} ${str(result.sourceId || id)}`);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const uninstall = async () => {
    setBusy(true);
    setMsg(null);
    setErr(null);
    try {
      const result = await arcaliumctl(["apps", "uninstall", id, "--json"]);
      setMsg(`${str(result.action)} ${str(result.sourceId || id)}`);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="btn-row">
        {app.launchable && desktop ? (
          <button type="button" className="btn primary" onClick={() => void openDesktop(desktop)}>
            Launch
          </button>
        ) : null}
        {app.type === "flatpak" && !app.installed ? (
          <button type="button" className="btn" disabled={busy} onClick={() => void install()}>
            {busy ? "Working…" : "Install (user)"}
          </button>
        ) : null}
        {app.type === "flatpak" && app.installed && app.installScope === "user" ? (
          <button type="button" className="btn" disabled={busy} onClick={() => void uninstall()}>
            {busy ? "Working…" : "Uninstall"}
          </button>
        ) : null}
        {app.type === "flatpak" && app.installed && app.installScope === "system" ? (
          <span className="muted small">System install — uninstall via Flatpak/Bazaar if needed</span>
        ) : null}
        {app.type === "desktop" && !app.installed ? (
          <span className="muted small">Ships with the OS image</span>
        ) : null}
      </div>
      {app.licenceNotice ? <p className="muted small">{app.licenceNotice}</p> : null}
      {app.dataDir ? (
        <p className="muted small mono">
          Data: {app.dataDir}
        </p>
      ) : null}
      {msg ? <p className="banner ok">{msg}</p> : null}
      {err ? <p className="banner bad">{err}</p> : null}
    </div>
  );
}
