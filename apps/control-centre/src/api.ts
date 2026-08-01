import { invoke } from "@tauri-apps/api/core";

export type JsonValue = Record<string, unknown>;

export async function arcaliumctl(args: string[]): Promise<JsonValue> {
  return invoke<JsonValue>("arcaliumctl", { args });
}

export async function openDesktop(desktopId: string): Promise<void> {
  return invoke("open_desktop", { desktopId });
}

export async function launchMode(): Promise<"setup" | "control-centre"> {
  const mode = await invoke<string>("launch_mode");
  return mode === "setup" ? "setup" : "control-centre";
}
