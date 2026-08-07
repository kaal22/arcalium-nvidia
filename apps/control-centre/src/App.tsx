import { useEffect, useState } from "react";
import brandMark from "../../../assets/arccleanSVG.svg";
import { launchMode } from "./api";
import { NAV, PageId } from "./nav";
import { NavIcon } from "./navIcons";
import { OverviewPage } from "./pages/Overview";
import { GamingPage } from "./pages/Gaming";
import { CompatibilityPage } from "./pages/Compatibility";
import { GpuPage } from "./pages/Gpu";
import { ApplicationsPage } from "./pages/Applications";
import { StoragePage } from "./pages/Storage";
import { NetworkPage } from "./pages/Network";
import { ControllersPage } from "./pages/Controllers";
import { StreamingPage } from "./pages/Streaming";
import { UpdatesPage } from "./pages/Updates";
import { DiagnosticsPage } from "./pages/Diagnostics";
import { AssistantPage } from "./pages/Assistant";
import { SettingsPage } from "./pages/Settings";
import { AboutPage } from "./pages/About";
import { WizardApp } from "./wizard/WizardApp";

const LAST_PAGE_KEY = "arcalium.cc.lastPage";

function isPageId(v: string | null): v is PageId {
  return !!v && NAV.some((n) => n.id === v);
}

function ShellClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);
  return (
    <span className="accent">
      {now.toLocaleDateString(undefined, { weekday: "short", day: "2-digit", month: "short" })}{" "}
      {now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
    </span>
  );
}

export default function App() {
  const [mode, setMode] = useState<"loading" | "setup" | "control-centre">("loading");
  const [page, setPage] = useState<PageId>("overview");

  useEffect(() => {
    void launchMode()
      .then(setMode)
      .catch(() => setMode("control-centre"));
  }, []);

  useEffect(() => {
    if (mode !== "control-centre") return;
    if (localStorage.getItem("arcalium.cc.rememberPage") === "0") return;
    const saved = localStorage.getItem(LAST_PAGE_KEY);
    if (isPageId(saved)) setPage(saved);
  }, [mode]);

  const go = (id: PageId) => {
    setPage(id);
    if (localStorage.getItem("arcalium.cc.rememberPage") !== "0") {
      localStorage.setItem(LAST_PAGE_KEY, id);
    }
  };

  if (mode === "loading") {
    return (
      <div className="shell" style={{ gridTemplateColumns: "1fr" }}>
        <div className="content-wrap" style={{ gridColumn: 1 }}>
          <main className="content">
            <p className="muted">Starting…</p>
          </main>
        </div>
      </div>
    );
  }

  if (mode === "setup") {
    return <WizardApp />;
  }

  return (
    <div className="shell">
      <aside className="nav">
        <div className="brand">
          <img className="brand-mark" src={brandMark} alt="" aria-hidden />
          <div>
            <div className="brand-name">Arcalium</div>
            <div className="brand-sub">Control Centre</div>
          </div>
        </div>
        <nav>
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={page === item.id ? "nav-item active" : "nav-item"}
              onClick={() => go(item.id)}
            >
              <NavIcon id={item.id} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>
      <div className="content-wrap">
        <main className="content">
          {page === "overview" && <OverviewPage onNavigate={go} />}
          {page === "gaming" && <GamingPage />}
          {page === "compatibility" && <CompatibilityPage />}
          {page === "gpu" && <GpuPage />}
          {page === "applications" && <ApplicationsPage />}
          {page === "storage" && <StoragePage />}
          {page === "network" && <NetworkPage />}
          {page === "controllers" && <ControllersPage />}
          {page === "streaming" && <StreamingPage />}
          {page === "updates" && <UpdatesPage />}
          {page === "diagnostics" && <DiagnosticsPage />}
          {page === "assistant" && <AssistantPage />}
          {page === "settings" && (
            <SettingsPage currentPage={page} onRestorePage={go} />
          )}
          {page === "about" && <AboutPage />}
        </main>
      </div>
      <footer className="shell-footer">
        <span>Arcalium Control Centre</span>
        <ShellClock />
      </footer>
    </div>
  );
}
