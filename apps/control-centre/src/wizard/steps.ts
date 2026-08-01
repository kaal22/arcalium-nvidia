export type WizardStepId =
  | "welcome"
  | "hardware"
  | "nvidia"
  | "display"
  | "updates"
  | "applications"
  | "protonGe"
  | "steam"
  | "storage"
  | "vpn"
  | "streaming"
  | "validation"
  | "completion";

export const WIZARD_STEPS: { id: WizardStepId; label: string; skippable: boolean }[] = [
  { id: "welcome", label: "Welcome", skippable: false },
  { id: "hardware", label: "Hardware", skippable: false },
  { id: "nvidia", label: "NVIDIA", skippable: false },
  { id: "display", label: "Display & audio", skippable: true },
  { id: "updates", label: "Updates", skippable: true },
  { id: "applications", label: "Applications", skippable: true },
  { id: "protonGe", label: "Proton-GE", skippable: true },
  { id: "steam", label: "Steam", skippable: true },
  { id: "storage", label: "Storage", skippable: true },
  { id: "vpn", label: "VPN", skippable: true },
  { id: "streaming", label: "Streaming", skippable: true },
  { id: "validation", label: "Validation", skippable: false },
  { id: "completion", label: "Finish", skippable: false },
];
