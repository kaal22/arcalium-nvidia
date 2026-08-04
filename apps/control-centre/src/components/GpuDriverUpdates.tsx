import { useState } from "react";
import { arcaliumctl } from "../api";
import { pick, str } from "../lib/json";

type DriverAction = "check" | "apply" | null;

/**
 * NVIDIA drivers ship inside the Arcalium bootc image (nvidia-open from the
 * pinned Bazzite base). Newer drivers arrive via OS update after a maintainer
 * re-pin — not via GeForce Experience / .run installers.
 */
export function GpuDriverUpdates({
  driverVersion,
  disabled = false,
}: {
  driverVersion?: string | null;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState<DriverAction>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const version = str(driverVersion, "").trim() || "unknown";

  const run = async (action: Exclude<DriverAction, null>) => {
    setBusy(action);
    setMsg(null);
    setErr(null);
    try {
      const result = await arcaliumctl(["updates", action, "--json"]);
      if (!pick(result, "ok")) {
        throw new Error(str(pick(result, "message"), `Could not start ${action}.`));
      }
      setMsg(str(pick(result, "message")));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div style={{ marginTop: "0.75rem" }}>
      <p className="muted small">
        <strong>Current driver:</strong> <span className="mono">{version}</span>
      </p>
      <p className="muted small">
        NVIDIA drivers ship with the Arcalium OS image (nvidia-open). They are not
        downloaded from nvidia.com. Check for an OS update when a newer Arcalium
        image may include a newer driver; Apply opens a terminal (type yes, then
        sudo).
      </p>
      <div className="btn-row" style={{ marginTop: "0.5rem" }}>
        <button
          type="button"
          className="btn"
          disabled={disabled || busy !== null}
          onClick={() => void run("check")}
        >
          {busy === "check" ? "Opening…" : "Check for driver / OS updates"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={disabled || busy !== null}
          onClick={() => void run("apply")}
        >
          {busy === "apply" ? "Opening…" : "Apply update and reboot"}
        </button>
      </div>
      {msg ? <p className="banner ok">{msg}</p> : null}
      {err ? <p className="banner bad">{err}</p> : null}
    </div>
  );
}
