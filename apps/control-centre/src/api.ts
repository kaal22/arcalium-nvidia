import { invoke } from "@tauri-apps/api/core";

export type JsonValue = Record<string, unknown>;

// Every backend call flips a busy flag so the pointer shows progress; without it
// clicking Install or Launch looks like nothing happened.
let pending = 0;

function setBusy(active: boolean) {
  pending += active ? 1 : -1;
  if (pending < 0) pending = 0;
  if (typeof document !== "undefined") {
    document.body.dataset.busy = pending > 0 ? "true" : "false";
  }
}

async function withBusy<T>(run: () => Promise<T>, holdMs = 0): Promise<T> {
  setBusy(true);
  try {
    return await run();
  } finally {
    if (holdMs > 0) {
      setTimeout(() => setBusy(false), holdMs);
    } else {
      setBusy(false);
    }
  }
}

export async function arcaliumctl(args: string[]): Promise<JsonValue> {
  return withBusy(() => invoke<JsonValue>("arcaliumctl", { args }));
}

// Spawning the .desktop entry returns long before the window appears, so the
// pointer keeps showing progress for a moment rather than blinking once.
const LAUNCH_FEEDBACK_MS = 2500;

export async function openDesktop(desktopId: string): Promise<void> {
  return withBusy(() => invoke("open_desktop", { desktopId }), LAUNCH_FEEDBACK_MS);
}

export async function launchMode(): Promise<"setup" | "control-centre"> {
  const mode = await invoke<string>("launch_mode");
  return mode === "setup" ? "setup" : "control-centre";
}
