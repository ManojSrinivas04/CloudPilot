import { Link } from "react-router-dom";

export function RegisterPage() {
  return (
    <section className="account-panel">
      <p className="eyebrow">Get started</p>
      <h1>Create account</h1>
      <p className="page-copy">Account registration will connect to the CloudPilot API in a later step.</p>
      <div className="account-switch">
        Already registered? <Link to="/login">Sign in</Link>
      </div>
    </section>
  );
}