export function DashboardPage() {
  return (
    <section className="welcome-panel">
      <div className="welcome-copy">
        <p className="eyebrow">FinOps workspace</p>
        <h1>Cloud spend, in focus.</h1>
        <p className="page-copy">
          Your CloudPilot workspace is ready for its first connection.
        </p>
      </div>
      <div className="welcome-index" aria-hidden="true">
        <span>CP</span>
        <span className="index-rule" />
        <small>01 / 03</small>
      </div>
    </section>
  );
}