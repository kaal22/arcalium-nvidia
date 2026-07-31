import { useCallback, useEffect, useState } from "react";
import { arcaliumctl, openDesktop, JsonValue } from "../api";

type LoadState = "loading" | "ready" | "error";

function pick(obj: JsonValue | null | unknown, path: string): unknown {
  if (!obj || typeof obj !== "object") return undefined;
  return path.split(".").reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && key in (acc as object)) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

function str(v: unknown, fallback = "—"): string {
  if (v === null || v === undefined || v === "") return fallback;
  return String(v);
}

type InstalledProton = { name?: string; path?: string; bin?: string };

export function CompatibilityPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [list, setList] = useState<JsonValue | null>(null);
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState<string | null>(null);
  const [installErr, setInstallErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const data = await arcaliumctl(["proton", "list", "--json"]);
      setList(data);
      setState("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const installRecommended = useCallback(async () => {
    setInstalling(true);
    setInstallMsg(null);
    setInstallErr(null);
    try {
      const result = await arcaliumctl(["proton", "install-recommended", "--json"]);
      const action = str(pick(result, "action"), "done");
      const name = str(pick(result, "name"), "GE-Proton");
      if (action === "already_present") {
        setInstallMsg(`${name} is already installed.`);
      } else if (action === "updated") {
        setInstallMsg(`Updated to ${name}.`);
      } else {
        setInstallMsg(`Installed ${name}.`);
      }
      await refresh();
    } catch (e) {
      setInstallErr(e instanceof Error ? e.message : String(e));
    } finally {
      setInstalling(false);
    }
  }, [refresh]);

  const installed = (pick(list, "installed") as InstalledProton[] | undefined) || [];
  const recommendedPresent = pick(list, "recommendedPresent") === true;
  const count = Number(pick(list, "count") ?? installed.length);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Compatibility</h1>
          <p className="muted">GE-Proton for Heroic, and how to pick Proton in Steam.</p>
        </div>
        <button type="button" className="btn" onClick={() => void refresh()} disabled={state === "loading"}>
          {state === "loading" ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {state === "error" && (
        <div className="banner error">
          <strong>Could not list Proton builds.</strong>
          <div>{error}</div>
        </div>
      )}

      {installErr && (
        <div className="banner error">
          <strong>Install failed.</strong>
          <div>{installErr}</div>
        </div>
      )}

      {installMsg && (
        <div className="banner ok">
          <strong>{installMsg}</strong>
        </div>
      )}

      <section className="grid">
        <article className="card">
          <h2>GE-Proton (Heroic)</h2>
          <dl>
            <div>
              <dt>Installed</dt>
              <dd className={count > 0 ? "ok" : "warn"}>{state === "ready" ? String(count) : "—"}</dd>
            </div>
            <div>
              <dt>Recommended</dt>
              <dd className={recommendedPresent ? "ok" : "warn"}>
                {state !== "ready" ? "—" : recommendedPresent ? "Present" : "Not installed"}
              </dd>
            </div>
            <div>
              <dt>Tools dir</dt>
              <dd className="mono">{str(pick(list, "toolsDir"))}</dd>
            </div>
            <div>
              <dt>Games dir</dt>
              <dd className="mono">{str(pick(list, "gamesDir"))}</dd>
            </div>
          </dl>
          {installed.length > 0 && (
            <ul className="plain-list">
              {installed.map((item, i) => (
                <li key={item.name || i}>{str(item.name)}</li>
              ))}
            </ul>
          )}
          <div className="action-row" style={{ marginTop: "0.9rem" }}>
            <button
              type="button"
              className="btn primary"
              disabled={installing || state === "loading"}
              onClick={() => void installRecommended()}
            >
              {installing ? "Installing… (may take several minutes)" : "Install recommended GE-Proton"}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => void openDesktop("com.vysp3r.ProtonPlus.desktop")}
            >
              Open ProtonPlus
            </button>
          </div>
          <p className="muted small" style={{ marginTop: "0.75rem" }}>
            Downloads the latest GE-Proton release into Heroic&apos;s tools directory. First launch of
            Heroic can do the same automatically. Steam uses its own Proton builds separately.
          </p>
        </article>

        <article className="card">
          <h2>Steam per-game Proton</h2>
          <p className="muted small">
            In Steam, open a game&apos;s Properties → Compatibility → Force the use of a specific Steam
            Play compatibility tool, then pick a Proton version. Community reports help choose which
            version works for a title.
          </p>
          <ul className="plain-list">
            <li>
              <a href="https://www.protondb.com/" target="_blank" rel="noreferrer">
                ProtonDB
              </a>{" "}
              — community compatibility reports
            </li>
            <li>
              <a
                href="https://areweanticheatyet.com/"
                target="_blank"
                rel="noreferrer"
              >
                Are We Anti-Cheat Yet?
              </a>{" "}
              — anti-cheat status on Linux
            </li>
          </ul>
        </article>

        <article className="card">
          <h2>Game categories</h2>
          <dl>
            <div>
              <dt>Native</dt>
              <dd>Runs without Proton</dd>
            </div>
            <div>
              <dt>Proton</dt>
              <dd>Works with a Proton build</dd>
            </div>
            <div>
              <dt>Adjustments</dt>
              <dd>Needs tweaks (launch options, older Proton)</dd>
            </div>
            <div>
              <dt>Anti-cheat</dt>
              <dd>May be blocked by the game&apos;s anti-cheat</dd>
            </div>
            <div>
              <dt>Unsupported</dt>
              <dd>No practical path on Linux yet</dd>
            </div>
          </dl>
        </article>
      </section>
    </div>
  );
}
