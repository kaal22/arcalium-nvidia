import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";
import { copyText, pick, str } from "../lib/json";

type LoadState = "loading" | "ready" | "error";

function gib(bytes: unknown): string {
  if (typeof bytes !== "number") return "—";
  return `${(bytes / 1024 ** 3).toFixed(1)} GiB`;
}

export function StoragePage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JsonValue | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      setData(await arcaliumctl(["storage", "scan", "--json"]));
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const warnings = (pick(data, "warnings") as { message?: string }[]) || [];
  const steamLibs = (pick(data, "steamLibraries") as { root?: string; paths?: string[] }[]) || [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Storage</h1>
          <p className="muted">Drives, free space and game-library locations (read-only).</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>
      {state === "loading" && <p className="muted">Loading…</p>}
      {state === "error" && <p className="banner bad">{error}</p>}
      {msg && <p className="banner ok">{msg}</p>}
      {state === "ready" && (
        <>
          <div className="grid two">
            <article className="card">
              <h2>System free space</h2>
              <dl className="kv">
                <div>
                  <dt>Root (/)</dt>
                  <dd>
                    {str(pick(data, "root.freeGiB"))} / {str(pick(data, "root.totalGiB"))} GiB free
                  </dd>
                </div>
                <div>
                  <dt>Home</dt>
                  <dd>
                    {str(pick(data, "home.freeGiB"))} / {str(pick(data, "home.totalGiB"))} GiB free
                  </dd>
                </div>
              </dl>
            </article>
            <article className="card">
              <h2>Actions</h2>
              <div className="btn-row">
                <button type="button" className="btn" onClick={() => void openDesktop("org.kde.dolphin.desktop")}>
                  Open Files
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => void openDesktop("org.kde.partitionmanager.desktop").catch(() => openDesktop("systemsettings.desktop"))}
                >
                  Open disk utility
                </button>
                <button type="button" className="btn" onClick={() => void openDesktop("steam.desktop")}>
                  Open Steam
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={async () => {
                    await copyText(JSON.stringify(data, null, 2));
                    setMsg("Storage report copied.");
                  }}
                >
                  Copy diagnostic info
                </button>
              </div>
              <p className="muted small" style={{ marginTop: "0.75rem" }}>
                Arcalium never formats drives from Control Centre. Prefer Btrfs or Ext4 for game libraries.
                Migrating from NTFS: copy libraries to a Linux filesystem, then add the folder in Steam →
                Settings → Storage.
              </p>
            </article>
          </div>

          {warnings.length > 0 && (
            <article className="card">
              <h2>Warnings</h2>
              <ul className="plain-list">
                {warnings.map((w, i) => (
                  <li key={i}>{w.message}</li>
                ))}
              </ul>
            </article>
          )}

          <article className="card">
            <h2>Block devices</h2>
            <ul className="plain-list mono small">
              {((pick(data, "devices") as { name?: string; fstype?: string; mountpoint?: string; size?: number; type?: string }[]) || [])
                .filter((d) => d.mountpoint || d.fstype || d.type === "disk")
                .map((d, i) => (
                  <li key={i}>
                    {str(d.name)} · {str(d.type)} · {str(d.fstype, "—")} · {gib(d.size)}
                    {d.mountpoint ? ` · ${d.mountpoint}` : ""}
                  </li>
                ))}
            </ul>
          </article>

          <article className="card">
            <h2>Steam libraries</h2>
            {steamLibs.length === 0 ? (
              <p className="muted">No Steam libraryfolders.vdf found yet.</p>
            ) : (
              <ul className="plain-list small">
                {steamLibs.map((lib, i) => (
                  <li key={i}>
                    <span className="mono">{lib.root}</span>
                    <ul className="plain-list mono">
                      {(lib.paths || []).map((p) => (
                        <li key={p}>{p}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </>
      )}
    </div>
  );
}
