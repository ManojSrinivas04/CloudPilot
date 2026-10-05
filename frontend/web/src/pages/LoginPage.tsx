import { Link } from "react-router-dom";

export function LoginPage() {
  return (
    <section className="account-panel">
      <p className="eyebrow">Your workspace</p>
      <h1>Sign in</h1>
      <p className="page-copy">Account access will connect to the CloudPilot API in a later step.</p>
      <div className="account-switch">
        New to CloudPilot? <Link to="/register">Create an account</Link>
      </div>
    </section>
  );
}