import { useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { pick, str } from "../lib/json";
import type { PageId } from "../nav";

const LAST_PAGE_KEY = "arcalium.cc.lastPage";

export function SettingsPage({
  currentPage,
  onRestorePage,
}: {
  currentPage: PageId;
  onRestorePage: (id: PageId) => void;
}) {
  const [remember, setRemember] = useState(true);
  const [saved, setSaved] = useState<string | null>(null);
  const [setup, setSetup] = useState<JsonValue | null>(null);
  const [setupMsg, setSetupMsg] = useState<string | null>(null);
  const [setupErr, setSetupErr] = useState<string | null>(null);
  const [busyAutostart, setBusyAutostart] = useState(false);

  const refreshSetup = async () => {
    const st = await arcaliumctl(["setup", "status", "--json"]);
    setSetup(st);
    return st;
  };

  useEffect(() => {
    const pref = localStorage.getItem("arcalium.cc.rememberPage");
    setRemember(pref !== "0");
    setSaved(localStorage.getItem(LAST_PAGE_KEY));
    void refreshSetup().catch(() => setSetup(null));
  }, []);

  useEffect(() => {
    if (!remember) return;
    localStorage.setItem(LAST_PAGE_KEY, currentPage);
    localStorage.setItem("arcalium.cc.rememberPage", "1");
    setSaved(currentPage);
  }, [currentPage, remember]);

  const setupCompleted = setup ? Boolean(pick(setup, "completed")) : null;
  const showOnStartup = setup ? Boolean(pick(setup, "showOnStartup")) : true;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="muted">Local Control Centre preferences only — no privileged toggles.</p>
        </div>
      </header>
      <article className="card">
        <h2>Session</h2>
        <label className="check-row">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => {
              const on = e.target.checked;
              setRemember(on);
              localStorage.setItem("arcalium.cc.rememberPage", on ? "1" : "0");
            }}
          />
          Remember last page between launches
        </label>
        <p className="muted small">Last saved page: {saved || "—"}</p>
        {saved ? (
          <button
            type="button"
            className="btn"
            onClick={() => onRestorePage(saved as PageId)}
          >
            Go to last page
          </button>
        ) : null}
      </article>
      <article className="card">
        <h2>Setup wizard</h2>
        <p className="muted small">
          Status:{" "}
          {setupCompleted === null
            ? "unknown"
            : setupCompleted
              ? "complete"
              : "not finished"}
        </p>
        <label className="check-row" style={{ marginTop: "0.75rem" }}>
          <input
            type="checkbox"
            checked={showOnStartup}
            disabled={busyAutostart || setup === null}
            onChange={(e) => {
              const on = e.target.checked;
              setBusyAutostart(true);
              setSetupErr(null);
              setSetupMsg(null);
              void (async () => {
                try {
                  await arcaliumctl(["setup", "set-autostart", on ? "on" : "off", "--json"]);
                  await refreshSetup();
                  setSetupMsg(
                    on
                      ? "Setup will open on the next login until you finish or turn this off."
                      : "Setup will not open automatically on login.",
                  );
                } catch (err) {
                  setSetupErr(err instanceof Error ? err.message : String(err));
                } finally {
                  setBusyAutostart(false);
                }
              })();
            }}
          />
          Show Setup on startup
        </label>
        <p className="muted small">
          Language, keyboard, and timezone come from the installer. Plasma Welcome runs before
          login (Wi‑Fi and desktop setup). On first login this wizard opens shortly after the
          session starts when this toggle is on. Finishing setup turns the toggle off; Restart
          setup turns it back on.
        </p>
        {setupMsg && <p className="banner ok">{setupMsg}</p>}
        {setupErr && <p className="banner bad">{setupErr}</p>}
        <div className="btn-row">
          <button
            type="button"
            className="btn"
            onClick={() => {
              // Resume / relaunch uses the dedicated setup launcher.
              void openDesktop("io.arcalium.Setup.desktop").catch(async () => {
                // Fallback: spawn via Control Centre entry is not enough; tell the user.
                setSetupErr(
                  "Could not open the Setup launcher. From a terminal: arcalium-setup",
                );
              });
            }}
          >
            {setupCompleted ? "Open setup again" : "Resume setup"}
          </button>
          <button
            type="button"
            className="btn"
            onClick={async () => {
              if (
                !window.confirm(
                  "Restart setup from the beginning? This clears your setup progress marker and turns Show on startup back on.",
                )
              ) {
                return;
              }
              setSetupErr(null);
              setSetupMsg(null);
              try {
                await arcaliumctl(["setup", "reset", "--json"]);
                await refreshSetup();
                setSetupMsg("Setup progress cleared. Autostart is on again — use Resume setup to start.");
              } catch (e) {
                setSetupErr(e instanceof Error ? e.message : String(e));
              }
            }}
          >
            Restart setup…
          </button>
        </div>
        {setup ? (
          <p className="muted small" style={{ marginTop: "0.75rem" }}>
            Will autostart next login:{" "}
            <strong>{pick(setup, "shouldAutostart") ? "yes" : "no"}</strong>
            {pick(setup, "liveSession") ? " (live session)" : ""}
            {" · "}
            Current step: <span className="mono">{str(pick(setup, "currentStep"))}</span>
          </p>
        ) : null}
      </article>
      <article className="card">
        <h2>System</h2>
        <div className="btn-row">
          <button type="button" className="btn" onClick={() => void openDesktop("systemsettings.desktop")}>
            Open System Settings
          </button>
        </div>
        <p className="muted small" style={{ marginTop: "0.75rem" }}>
          Desktop theme, displays, network and Bluetooth are managed by Plasma System Settings, not
          Arcalium Control Centre.
        </p>
      </article>
    </div>
  );
}
