import { useEffect, useState } from "react";
import { arcaliumctl, JsonValue } from "../api";

export function AboutPage() {
  const [summary, setSummary] = useState<JsonValue | null>(null);

  useEffect(() => {
    void arcaliumctl(["system", "summary", "--json"])
      .then(setSummary)
      .catch(() => setSummary(null));
  }, []);

  const image = summary
    ? `${String(summary.imageName ?? "arcalium-os-nvidia")}:${String(summary.channel ?? "dev")}`
    : "arcalium-os-nvidia:dev";

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>About</h1>
          <p className="muted">Arcalium OS NVIDIA Edition</p>
        </div>
      </header>
      <article className="card">
        <dl>
          <div>
            <dt>Control Centre</dt>
            <dd>0.1.0 — Overview + Compatibility</dd>
          </div>
          <div>
            <dt>Image</dt>
            <dd>{image}</dd>
          </div>
          <div>
            <dt>App ID</dt>
            <dd>io.arcalium.ControlCentre</dd>
          </div>
          <div>
            <dt>Backend</dt>
            <dd>/usr/bin/arcaliumctl (allowlisted JSON only)</dd>
          </div>
        </dl>
        <p className="muted">
          Arcalium OS is an independent project built on Bazzite and is not affiliated with or
          endorsed by Valve, NVIDIA, Spotify, Proton AG, Fedora, Universal Blue or the Bazzite
          project. Repository tooling retains the Apache-2.0 licence from Universal Blue’s
          image-template.
        </p>
        <p className="muted">
          Docs and support:{" "}
          <a href="https://github.com/kaal22/arcalium-nvidia" target="_blank" rel="noreferrer">
            github.com/kaal22/arcalium-nvidia
          </a>
        </p>
      </article>
    </div>
  );
}
