import { pick, str } from "../lib/json";
import type { JsonValue } from "../api";

/** Shared Local AI minimum hardware copy (PRODUCT_SPEC §9.14). */
export const AI_MIN_RAM_GIB = 16;
export const AI_MIN_VRAM_GIB = 8;

export function AiMinSpec({ status }: { status: JsonValue | null }) {
  const ramReq = Number(pick(status, "requirements.ramGiB") ?? AI_MIN_RAM_GIB);
  const vramReq = Number(pick(status, "requirements.vramGiB") ?? AI_MIN_VRAM_GIB);
  const ramHave = pick(status, "hardware.ramGiB");
  const vramHave = pick(status, "hardware.vramGiB");
  const ok = Boolean(pick(status, "hardwareOk"));
  const warnings = (pick(status, "hardwareWarnings") as string[] | undefined) || [];
  const note = str(
    pick(status, "requirements.note"),
    `Minimum ${ramReq} GiB system RAM and ${vramReq} GiB GPU VRAM. Smaller PCs will struggle or fail — Skip if unsure.`,
  );

  return (
    <div style={{ marginTop: "0.75rem" }}>
      <p className="muted small">
        <strong>Minimum:</strong> {ramReq} GiB RAM · {vramReq} GiB GPU VRAM · ~10 GiB free disk for the
        first model download.
      </p>
      <p className="muted small">
        This PC:{" "}
        {ramHave != null ? `${str(ramHave)} GiB RAM` : "RAM unknown"} ·{" "}
        {vramHave != null ? `${str(vramHave)} GiB VRAM` : "VRAM unknown"}
        {ok ? (
          <span className="badge ok" style={{ marginLeft: "0.5rem" }}>
            meets minimum
          </span>
        ) : (
          <span className="badge warn" style={{ marginLeft: "0.5rem" }}>
            below minimum
          </span>
        )}
      </p>
      <p className="muted small">{note}</p>
      <p className="muted small">
        AI can be wrong — double-check before changing your system. Mutating tools still ask for yes.
      </p>
      {!ok &&
        warnings.map((w) => (
          <p className="banner bad" key={w}>
            {w}
          </p>
        ))}
    </div>
  );
}
