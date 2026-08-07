import type { ReactNode } from "react";
import type { PageId } from "./nav";

type IconProps = { className?: string };

function svg(props: IconProps, paths: ReactNode) {
  return (
    <svg
      className={props.className}
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {paths}
    </svg>
  );
}

export function NavIcon({ id, className }: { id: PageId; className?: string }) {
  const p: IconProps = { className };
  switch (id) {
    case "overview":
      return svg(p, (
        <>
          <rect x="3" y="3" width="7" height="7" rx="1.2" />
          <rect x="14" y="3" width="7" height="7" rx="1.2" />
          <rect x="3" y="14" width="7" height="7" rx="1.2" />
          <rect x="14" y="14" width="7" height="7" rx="1.2" />
        </>
      ));
    case "gaming":
      return svg(p, (
        <>
          <rect x="2" y="8" width="20" height="10" rx="3" />
          <path d="M8 13h0.01M11 13h0.01M7 11v4M9 11v4" />
          <circle cx="16" cy="12" r="1" />
          <circle cx="18.5" cy="14" r="1" />
        </>
      ));
    case "compatibility":
      return svg(p, (
        <>
          <path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4z" />
          <path d="M9 12l2 2 4-4" />
        </>
      ));
    case "gpu":
      return svg(p, (
        <>
          <rect x="3" y="6" width="18" height="12" rx="2" />
          <circle cx="8" cy="12" r="2" />
          <circle cx="14" cy="12" r="2" />
          <path d="M19 10v4" />
        </>
      ));
    case "applications":
      return svg(p, (
        <>
          <rect x="4" y="4" width="6" height="6" rx="1" />
          <rect x="14" y="4" width="6" height="6" rx="1" />
          <rect x="4" y="14" width="6" height="6" rx="1" />
          <rect x="14" y="14" width="6" height="6" rx="1" />
        </>
      ));
    case "storage":
      return svg(p, (
        <>
          <ellipse cx="12" cy="6" rx="7" ry="2.5" />
          <path d="M5 6v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6" />
          <path d="M5 12v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6" />
        </>
      ));
    case "network":
      return svg(p, (
        <>
          <path d="M5 16a9 9 0 0 1 14 0" />
          <path d="M8.5 13a5 5 0 0 1 7 0" />
          <circle cx="12" cy="18" r="1.2" fill="currentColor" stroke="none" />
        </>
      ));
    case "controllers":
      return svg(p, (
        <>
          <path d="M7 10h10l1.5 7a2 2 0 0 1-2 2.5H7.5a2 2 0 0 1-2-2.5L7 10z" />
          <circle cx="9" cy="14" r="0.8" fill="currentColor" stroke="none" />
          <circle cx="15" cy="14" r="0.8" fill="currentColor" stroke="none" />
          <path d="M12 4v6" />
        </>
      ));
    case "streaming":
      return svg(p, (
        <>
          <circle cx="12" cy="12" r="2" />
          <path d="M7 7a7 7 0 0 1 10 0" />
          <path d="M4.5 4.5a11 11 0 0 1 15 0" />
          <path d="M7 17a7 7 0 0 0 10 0" />
        </>
      ));
    case "updates":
      return svg(p, (
        <>
          <path d="M4 12a8 8 0 0 1 14-5.3" />
          <path d="M18 4v5h-5" />
          <path d="M20 12a8 8 0 0 1-14 5.3" />
          <path d="M6 20v-5h5" />
        </>
      ));
    case "diagnostics":
      return svg(p, (
        <>
          <path d="M10 3h4l1 4h4v4l-3 2 3 2v4h-4l-1 4h-4l-1-4H5v-4l3-2-3-2V7h4l1-4z" />
        </>
      ));
    case "assistant":
      return svg(p, (
        <>
          <circle cx="12" cy="12" r="3.5" />
          <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
        </>
      ));
    case "settings":
      return svg(p, (
        <>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2.5v2.2M12 19.3v2.2M4.6 6.5l1.6 1.6M17.8 15.9l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 17.5l1.6-1.6M17.8 8.1l1.6-1.6" />
        </>
      ));
    case "about":
      return svg(p, (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 10v6" />
          <circle cx="12" cy="7.2" r="0.8" fill="currentColor" stroke="none" />
        </>
      ));
    default:
      return svg(p, <circle cx="12" cy="12" r="4" />);
  }
}
