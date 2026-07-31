import { useEffect, useState } from "react";
import { openDesktop } from "../api";
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

  useEffect(() => {
    const pref = localStorage.getItem("arcalium.cc.rememberPage");
    setRemember(pref !== "0");
    setSaved(localStorage.getItem(LAST_PAGE_KEY));
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
