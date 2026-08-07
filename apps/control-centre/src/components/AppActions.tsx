import { useEffect, useRef, useState } from "react";
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
  description?: string | null;
  licenceNotice?: string | null;
  website?: string | null;
  dataDir?: string | null;
  launchable?: boolean;
  category?: string;
};

const POLL_INTERVAL_MS = 4000;
const POLL_MAX_MS = 30 * 60 * 1000;

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

/** True once the catalogue reports this app as installed. */
async function isInstalled(id: string): Promise<boolean> {
  const list = await arcaliumctl(["apps", "list", "--json"]);
  const rows = (list.apps as AppRow[] | undefined) ?? [];
  return rows.some((row) => (row.id === id || row.sourceId === id) && Boolean(row.installed));
}

export function AppActions({
  app,
  onChanged,
}: {
  app: AppRow;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState<"install" | "uninstall" | "launch" | "steam-install" | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const cancelled = useRef(false);
  const id = str(app.id, "");
  const desktop = str(app.desktopId, "");
  const name = str(app.name, id);
  const isSteam = id === "steam";

  useEffect(() => {
    cancelled.current = false;
    return () => {
      cancelled.current = true;
    };
  }, []);

  const installSteam = async () => {
    setBusy("steam-install");
    setMsg(null);
    setErr(null);
    try {
      const result = await arcaliumctl(["steam", "install", "--visible", "--json"]);
      setMsg(
        str(
          result.message,
          "Installing Steam — a progress window opens. Valve’s agreement appears on first launch.",
        ),
      );
      if (str(result.action) === "terminal" || str(result.action) === "opened") {
        const started = Date.now();
        let done = false;
        while (!cancelled.current && Date.now() - started < POLL_MAX_MS) {
          await sleep(POLL_INTERVAL_MS);
          if (await isInstalled(id)) {
            done = true;
            break;
          }
        }
        if (cancelled.current) return;
        setMsg(
          done
            ? "Steam installed. Launch it to accept Valve’s agreement."
            : "Steam is still installing in the progress window. This page updates when it finishes.",
        );
      }
      onChanged();
    } catch (e) {
      if (!cancelled.current) setErr(e instanceof Error ? e.message : String(e));
    } finally {
      if (!cancelled.current) setBusy(null);
    }
  };

  const install = async () => {
    setBusy("install");
    setMsg(null);
    setErr(null);
    try {
      const result = await arcaliumctl(["apps", "install", id, "--visible", "--json"]);
      setMsg(str(result.message, `Installing ${name}…`));

      if (str(result.action) === "terminal") {
        const started = Date.now();
        let done = false;
        while (!cancelled.current && Date.now() - started < POLL_MAX_MS) {
          await sleep(POLL_INTERVAL_MS);
          if (await isInstalled(id)) {
            done = true;
            break;
          }
        }
        if (cancelled.current) return;
        setMsg(
          done
            ? `${name} installed.`
            : `${name} is still installing in the progress window. This page updates when it finishes.`,
        );
      }
      onChanged();
    } catch (e) {
      if (!cancelled.current) setErr(e instanceof Error ? e.message : String(e));
    } finally {
      if (!cancelled.current) setBusy(null);
    }
  };

  const uninstall = async () => {
    setBusy("uninstall");
    setMsg(null);
    setErr(null);
    try {
      const result = await arcaliumctl(["apps", "uninstall", id, "--json"]);
      setMsg(str(result.message, `${name} uninstalled.`));
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const launch = async () => {
    setBusy("launch");
    setMsg(null);
    setErr(null);
    try {
      await openDesktop(desktop);
      setMsg(`Starting ${name}… it can take a few seconds to appear.`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="app-actions">
      {app.description ? <p className="muted small">{app.description}</p> : null}
      <div className="btn-row">
        {app.launchable && desktop ? (
          <button
            type="button"
            className={`btn primary${busy === "launch" ? " working" : ""}`}
            disabled={busy !== null}
            onClick={() => void launch()}
          >
            {busy === "launch" ? "Launching…" : "Launch"}
          </button>
        ) : null}
        {app.type === "flatpak" && !app.installed && !isSteam ? (
          <button
            type="button"
            className={`btn${busy === "install" ? " working" : ""}`}
            disabled={busy !== null}
            onClick={() => void install()}
          >
            {busy === "install" ? "Installing…" : "Install"}
          </button>
        ) : null}
        {isSteam && !app.installed ? (
          <button
            type="button"
            className={`btn primary${busy === "steam-install" ? " working" : ""}`}
            disabled={busy !== null}
            onClick={() => void installSteam()}
          >
            {busy === "steam-install" ? "Installing…" : "Install Steam"}
          </button>
        ) : null}
        {app.type === "flatpak" && app.installed && app.installScope === "user" ? (
          <button
            type="button"
            className={`btn${busy === "uninstall" ? " working" : ""}`}
            disabled={busy !== null}
            onClick={() => void uninstall()}
          >
            {busy === "uninstall" ? "Removing…" : "Uninstall"}
          </button>
        ) : null}
        {app.type === "flatpak" && app.installed && app.installScope === "system" ? (
          <span className="muted small">Included with the system — remove it from Discover/Bazaar if you need to</span>
        ) : null}
        {app.type === "desktop" && !app.installed && !isSteam ? (
          <span className="muted small">Included with Arcalium</span>
        ) : null}
      </div>
      {app.licenceNotice ? <p className="muted small">{app.licenceNotice}</p> : null}
      {msg ? <p className="banner ok">{msg}</p> : null}
      {err ? <p className="banner bad">{err}</p> : null}
    </div>
  );
}
