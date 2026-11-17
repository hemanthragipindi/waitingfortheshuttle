import { useState } from "react";
import { ArrowRight, BusFront } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (form.password.length < 12) {
      setError("Use a password with at least 12 characters.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("The passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await register({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
      });
      navigate("/student/dashboard", { replace: true });
    } catch (requestError) {
      if (requestError.response?.status === 409) {
        setError("An account with this email already exists.");
      } else if (requestError.response?.status === 422) {
        setError("Check your name, email, and password and try again.");
      } else {
        setError(requestError.response?.data?.detail || "Account creation failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="register-title">
        <div className="auth-card__mark" aria-hidden="true"><BusFront size={23} /></div>
        <p className="eyebrow">STUDENT ACCESS</p>
        <h1 id="register-title">Create your account</h1>
        <p className="auth-card__intro">Registration creates a student account. Administrator access is provisioned separately.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="full_name">Full name</label>
          <input
            id="full_name"
            name="full_name"
            autoComplete="name"
            value={form.full_name}
            onChange={updateField}
            required
            maxLength={120}
          />
          <label htmlFor="email">University email</label>
          <input
            id="email"
            name="email"
            autoComplete="email"
            type="email"
            value={form.email}
            onChange={updateField}
            required
            maxLength={320}
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            autoComplete="new-password"
            type="password"
            minLength={12}
            maxLength={128}
            value={form.password}
            onChange={updateField}
            required
          />
          <label htmlFor="confirmPassword">Confirm password</label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            autoComplete="new-password"
            type="password"
            minLength={12}
            maxLength={128}
            value={form.confirmPassword}
            onChange={updateField}
            required
          />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button--primary auth-form__submit" disabled={submitting}>
            {submitting ? "Creating account…" : "Create student account"}
            {!submitting && <ArrowRight size={17} aria-hidden="true" />}
          </button>
        </form>
        <p className="auth-card__footer">
          Already registered? <Link to="/login">Student sign in</Link>
        </p>
      </section>
    </main>
  );
}
