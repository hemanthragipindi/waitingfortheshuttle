import { useState } from "react";
import { ArrowRight, BusFront } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

function apiErrorMessage(error) {
  if (error.response?.status === 401) return "Email or password is incorrect.";
  if (error.response?.status === 422) return "Check the email and password fields and try again.";
  return error.response?.data?.detail || "Sign in failed. Please try again.";
}

export default function LoginPage({ isAdmin = false }) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const user = await login({ email, password }, isAdmin);
      const defaultPath = user.role === "ADMIN" ? "/admin" : "/student/dashboard";
      navigate(location.state?.from || defaultPath, { replace: true });
    } catch (requestError) {
      setError(apiErrorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="auth-card__mark" aria-hidden="true"><BusFront size={23} /></div>
        <p className="eyebrow">{isAdmin ? "TRANSPORT TEAM" : "STUDENT ACCESS"}</p>
        <h1 id="login-title">{isAdmin ? "Administrator sign in" : "Welcome back"}</h1>
        <p className="auth-card__intro">
          {isAdmin
            ? "Sign in with your administrator account."
            : "Sign in to view campus shuttle information."}
        </p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="email">University email</label>
          <input
            id="email"
            autoComplete="username"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            maxLength={320}
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            autoComplete="current-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            maxLength={128}
          />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button--primary auth-form__submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
            {!submitting && <ArrowRight size={17} aria-hidden="true" />}
          </button>
        </form>
        {!isAdmin && (
          <p className="auth-card__footer">
            New to P05? <Link to="/register">Create a student account</Link>
          </p>
        )}
      </section>
    </main>
  );
}
