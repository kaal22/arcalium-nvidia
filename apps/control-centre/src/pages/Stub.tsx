export function StubPage({ title, note }: { title: string; note: string }) {
  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          <p className="muted">Not in this Overview MVP build.</p>
        </div>
      </header>
      <article className="card">
        <p>{note}</p>
      </article>
    </div>
  );
}
