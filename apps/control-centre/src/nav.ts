export type PageId =
  | "overview"
  | "gaming"
  | "compatibility"
  | "gpu"
  | "applications"
  | "storage"
  | "network"
  | "controllers"
  | "streaming"
  | "updates"
  | "diagnostics"
  | "settings"
  | "about";

export const NAV: { id: PageId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "gaming", label: "Gaming" },
  { id: "compatibility", label: "Compatibility" },
  { id: "gpu", label: "GPU and Display" },
  { id: "applications", label: "Applications" },
  { id: "storage", label: "Storage" },
  { id: "network", label: "Network and VPN" },
  { id: "controllers", label: "Controllers" },
  { id: "streaming", label: "Streaming" },
  { id: "updates", label: "Updates and Recovery" },
  { id: "diagnostics", label: "Diagnostics" },
  { id: "settings", label: "Settings" },
  { id: "about", label: "About" },
];
