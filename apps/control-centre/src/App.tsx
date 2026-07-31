import { useEffect, useState } from "react";
import brandMark from "../../../assets/arccleanSVG.svg";
import { NAV, PageId } from "./nav";
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
import { SettingsPage } from "./pages/Settings";
import { AboutPage } from "./pages/About";

const LAST_PAGE_KEY = "arcalium.cc.lastPage";

function isPageId(v: string | null): v is PageId {
  return !!v && NAV.some((n) => n.id === v);
}

export default function App() {
  const [page, setPage] = useState<PageId>("overview");

  useEffect(() => {
    if (localStorage.getItem("arcalium.cc.rememberPage") === "0") return;
    const saved = localStorage.getItem(LAST_PAGE_KEY);
    if (isPageId(saved)) setPage(saved);
  }, []);

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
              onClick={() => setPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="content">
        {page === "overview" && <OverviewPage />}
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
        {page === "settings" && (
          <SettingsPage currentPage={page} onRestorePage={setPage} />
        )}
        {page === "about" && <AboutPage />}
      </main>
    </div>
  );
}
