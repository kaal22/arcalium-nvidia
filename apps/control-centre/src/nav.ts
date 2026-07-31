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

export const NAV: { id: PageId; label: string; stubNote?: string }[] = [
  { id: "overview", label: "Overview" },
  {
    id: "gaming",
    label: "Gaming",
    stubNote: "Phase 4+ — launcher install/launch actions not in this build.",
  },
  {
    id: "compatibility",
    label: "Compatibility",
    stubNote: "Phase 5 — Proton-GE and ProtonPlus workflows not in this build.",
  },
  {
    id: "gpu",
    label: "GPU and Display",
    stubNote: "Live GPU summary is on Overview; full page arrives after ISO.",
  },
  {
    id: "applications",
    label: "Applications",
    stubNote: "Phase 4 — declarative Flatpak catalogue UI not in this build.",
  },
  {
    id: "storage",
    label: "Storage",
    stubNote: "Phase 6 — drive scan and library guidance not in this build.",
  },
  {
    id: "network",
    label: "Network and VPN",
    stubNote: "Phase 6 — ProtonVPN import not in this build.",
  },
  {
    id: "controllers",
    label: "Controllers",
    stubNote: "Phase 7 — controller detection not in this build.",
  },
  {
    id: "streaming",
    label: "Streaming",
    stubNote: "Phase 7 — Sunshine/Moonlight setup not in this build.",
  },
  {
    id: "updates",
    label: "Updates and Recovery",
    stubNote: "Phase 7 — bootc status UI not in this build.",
  },
  {
    id: "diagnostics",
    label: "Diagnostics",
    stubNote: "Phase 7 — diagnostics bundle not in this build.",
  },
  {
    id: "settings",
    label: "Settings",
    stubNote: "Phase 7 — Control Centre settings not in this build.",
  },
  { id: "about", label: "About" },
];
