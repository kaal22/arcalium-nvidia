import { useState } from "react";
// Repo-root brand asset, the same source the OS icons are generated from, so the
// UI mark cannot drift from the taskbar/menu icon.
import brandMark from "../../../assets/arccleanSVG.svg";
import { NAV, PageId } from "./nav";
import { OverviewPage } from "./pages/Overview";
import { CompatibilityPage } from "./pages/Compatibility";
import { AboutPage } from "./pages/About";
import { StubPage } from "./pages/Stub";

export default function App() {
  const [page, setPage] = useState<PageId>("overview");
  const current = NAV.find((n) => n.id === page)!;

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
        {page === "compatibility" && <CompatibilityPage />}
        {page === "about" && <AboutPage />}
        {page !== "overview" && page !== "compatibility" && page !== "about" && (
          <StubPage title={current.label} note={current.stubNote || ""} />
        )}
      </main>
    </div>
  );
}
