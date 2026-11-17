import { Link } from "react-router-dom";

export default function UnauthorizedPage() {
  return (
    <main className="message-page">
      <p className="eyebrow">ACCESS RESTRICTED</p>
      <h1>You don’t have permission to view this page.</h1>
      <p>Sign in with an account that has the required role, or return to the home page.</p>
      <Link className="button button--primary" to="/">Return home</Link>
    </main>
  );
}
