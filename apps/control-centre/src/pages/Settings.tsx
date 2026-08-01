import { useEffect, useState } from "react";
import { arcaliumctl, openDesktop } from "../api";
import { pick } from "../lib/json";
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
  const [setupCompleted, setSetupCompleted] = useState<boolean | null>(null);
  const [setupMsg, setSetupMsg] = useState<string | null>(null);
  const [setupErr, setSetupErr] = useState<string | null>(null);

  useEffect(() => {
    const pref = localStorage.getItem("arcalium.cc.rememberPage");
    setRemember(pref !== "0");
    setSaved(localStorage.getItem(LAST_PAGE_KEY));
    void arcaliumctl(["setup", "status", "--json"])
      .then((st) => setSetupCompleted(Boolean(pick(st, "completed"))))
      .catch(() => setSetupCompleted(null));
  }, []);

  useEffect(() => {
    if (!remember) return;
    localStorage.setItem(LAST_PAGE_KEY, currentPage);
    localStorage.setItem("arcalium.cc.rememberPage", "1");
    setSaved(currentPage);
  }, [currentPage, remember]);

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
                  "Restart setup from the beginning? This clears your setup progress marker.",
                )
              ) {
                return;
              }
              setSetupErr(null);
              setSetupMsg(null);
              try {
                await arcaliumctl(["setup", "reset", "--json"]);
                setSetupCompleted(false);
                setSetupMsg("Setup progress cleared. Use Resume setup to start again.");
              } catch (e) {
                setSetupErr(e instanceof Error ? e.message : String(e));
              }
            }}
          >
            Restart setup…
          </button>
        </div>
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
