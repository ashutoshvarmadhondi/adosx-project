import { useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowRight,
  LockKeyhole,
  ShieldCheck,
  User,
} from "lucide-react";
import {
  Navigate,
  useNavigate,
} from "react-router-dom";

import AppHeader from "../components/AppHeader";
import { login } from "../lib/api";

export default function LoginPage() {
  const navigate = useNavigate();

  const token = localStorage.getItem("auth_token");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      const response = await login(username, password);

      localStorage.setItem("auth_token", response.token);
      localStorage.setItem(
        "auth_user",
        JSON.stringify(response.user),
      );

      navigate("/dashboard", { replace: true });
    } catch (loginError) {
      setError(
        loginError instanceof Error
          ? loginError.message
          : "Unable to sign in.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <AppHeader />

      <main className="login-main">
        <section className="login-card">
          <div className="login-card-icon">
            <ShieldCheck size={28} />
          </div>

          <div className="login-heading">
            <p>Secure organization access</p>
            <h1>Sign in</h1>
            <span>
          To review your organization&apos;s
              reconciliation exceptions.
            </span>
          </div>

          <form
            className="login-form"
            onSubmit={handleSubmit}
          >
            <label htmlFor="username">
              Username

              <div className="login-input-wrapper">
                <User size={18} />

                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  required
                />
              </div>
            </label>

            <label htmlFor="password">
              Password

              <div className="login-input-wrapper">
                <LockKeyhole size={18} />

                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  required
                />
              </div>
            </label>

            {error ? (
              <div className="login-error" role="alert">
                {error}
              </div>
            ) : null}

            <button
              className="login-submit-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
              {!isSubmitting ? <ArrowRight size={18} /> : null}
            </button>
          </form>

          <div className="login-security-note">
            <ShieldCheck size={15} />
            Access is restricted to your assigned organization.
          </div>
        </section>
      </main>
    </div>
  );
}