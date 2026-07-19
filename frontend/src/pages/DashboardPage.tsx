import AppHeader from "../components/AppHeader";
import DashboardCharts from "../components/DashboardCharts";
import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Bot,

  ChevronRight,
  CircleAlert,
  FileWarning,
  Filter,

  MapPin,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  User,
  X,
} from "lucide-react";

import {
  askExceptionQuestion,
  getExceptions,
  logout,
} from "../lib/api";

import type {
  AuthUser,
  ExceptionFilters,
  ExceptionQuestionResponse,
  ReconciliationException,
} from "../types/api";

const REASON_CODES = [
  "VALUE_MISMATCH",
  "DATE_MISMATCH",
  "LOCATION_MISMATCH",
  "MISSING_IN_SYSTEM_A",
  "MISSING_IN_SYSTEM_B",
  "DUPLICATE_SYSTEM_B_ENTRY",
  "AMBIGUOUS_SYSTEM_B_ENTRIES",
  "TENANT_MISMATCH",
];

function getStoredUser(): AuthUser | null {
  const storedUser = localStorage.getItem("auth_user");

  if (!storedUser) {
    return null;
  }

  try {
    return JSON.parse(storedUser) as AuthUser;
  } catch {
    return null;
  }
}

function formatReasonCode(reasonCode: string): string {
  return reasonCode
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function getReasonClass(reasonCode: string): string {
  if (
    reasonCode === "VALUE_MISMATCH" ||
    reasonCode === "LOCATION_MISMATCH" ||
    reasonCode === "DATE_MISMATCH"
  ) {
    return "reason-badge reason-badge-warning";
  }

  if (
    reasonCode === "MISSING_IN_SYSTEM_A" ||
    reasonCode === "MISSING_IN_SYSTEM_B"
  ) {
    return "reason-badge reason-badge-danger";
  }

  if (reasonCode === "DUPLICATE_SYSTEM_B_ENTRY") {
    return "reason-badge reason-badge-purple";
  }

  return "reason-badge reason-badge-neutral";
}

export default function DashboardPage() {
  const navigate = useNavigate();

  const [user] = useState<AuthUser | null>(getStoredUser);

  const [exceptions, setExceptions] = useState<
    ReconciliationException[]
  >([]);
  const [count, setCount] = useState(0);

  const [reasonCode, setReasonCode] = useState("");
  const [recordId, setRecordId] = useState("");
  const [locationId, setLocationId] = useState("");

  const [activeFilters, setActiveFilters] =
    useState<ExceptionFilters>({});

  const [isLoading, setIsLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [error, setError] = useState("");

  const [question, setQuestion] = useState("");
  const [questionResult, setQuestionResult] =
    useState<ExceptionQuestionResponse | null>(null);
  const [questionError, setQuestionError] = useState("");
  const [isAskingQuestion, setIsAskingQuestion] =
    useState(false);

  const clearAuthentication = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    navigate("/login", { replace: true });
  }, [navigate]);

  const loadExceptions = useCallback(
    async (filters: ExceptionFilters = {}) => {
      const token = localStorage.getItem("auth_token");

      if (!token) {
        clearAuthentication();
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const response = await getExceptions(token, filters);
        setExceptions(response.results);
        setCount(response.count);
        
      } catch (requestError) {
        if (
          requestError instanceof Error &&
          requestError.message === "SESSION_EXPIRED"
        ) {
          clearAuthentication();
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load exceptions.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [clearAuthentication],
  );

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadExceptions();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadExceptions]);

  function handleFilterSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const filters: ExceptionFilters = {
      reasonCode,
      recordId,
      locationId,
    };

    setActiveFilters(filters);
    void loadExceptions(filters);
  }

  function handleClearFilters() {
    setReasonCode("");
    setRecordId("");
    setLocationId("");
    setActiveFilters({});
    void loadExceptions();
  }

  async function handleQuestionSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanedQuestion = question.trim();

    if (!cleanedQuestion) {
      setQuestionError("Enter a question.");
      return;
    }

    const token = localStorage.getItem("auth_token");

    if (!token) {
      clearAuthentication();
      return;
    }

    setIsAskingQuestion(true);
    setQuestionError("");
    setQuestionResult(null);

    try {
      const response = await askExceptionQuestion(
        token,
        cleanedQuestion,
      );

      setQuestionResult(response);
    } catch (requestError) {
      if (
        requestError instanceof Error &&
        requestError.message === "SESSION_EXPIRED"
      ) {
        clearAuthentication();
        return;
      }

      setQuestionError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to answer the question.",
      );
    } finally {
      setIsAskingQuestion(false);
    }
  }

  async function handleLogout() {
    const token = localStorage.getItem("auth_token");
    setIsLoggingOut(true);

    try {
      if (token) {
        await logout(token);
      }
    } catch {
      // Clear browser authentication even if logout API fails.
    } finally {
      clearAuthentication();
      setIsLoggingOut(false);
    }
  }

  const hasActiveFilters = Object.values(activeFilters).some(Boolean);

  const mismatchCount = exceptions.filter((exception) =>
    exception.reason_code.includes("MISMATCH"),
  ).length;

  const missingCount = exceptions.filter((exception) =>
    exception.reason_code.includes("MISSING"),
  ).length;

  return (
    <div className="app-shell">
      <div className="dashboard-layout">
        <AppHeader
          user={user}
          onLogout={handleLogout}
          isLoggingOut={isLoggingOut}
      />

    <main className="dashboard-main">
      <section className="dashboard-title">
        <div>
          <p>Reconciliation workspace</p>
          <h1>Exception Dashboard</h1>
          <span>
            Review discrepancies and investigate tenant-safe
            reconciliation results.
          </span>
        </div>
      </section>

          <div className="user-pill">
            <div className="user-avatar">
              <User size={17} />
            </div>

            <div>
              <strong>{user?.username ?? "User"}</strong>
              <span>
                {user?.organization_id ?? "Organization"}
              </span>
            </div>
          </div>
     

        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-icon stat-icon-blue">
              <FileWarning size={21} />
            </div>

            <div>
              <span>Total visible</span>
              <strong>{count}</strong>
              <small>Tenant-scoped exceptions</small>
            </div>
          </article>

          <article className="stat-card">
            <div className="stat-icon stat-icon-amber">
              <AlertTriangle size={21} />
            </div>

            <div>
              <span>Mismatches</span>
              <strong>{mismatchCount}</strong>
              <small>Value, date, or location</small>
            </div>
          </article>

          <article className="stat-card">
            <div className="stat-icon stat-icon-red">
              <CircleAlert size={21} />
            </div>

            <div>
              <span>Missing records</span>
              <strong>{missingCount}</strong>
              <small>Absent from either system</small>
            </div>
          </article>

          <article className="stat-card">
            <div className="stat-icon stat-icon-green">
              <ShieldCheck size={21} />
            </div>

            <div>
              <span>Isolation</span>
              <strong>Active</strong>
              <small>PostgreSQL RLS enforced</small>
            </div>
          </article>
        </section>

        <section className="dashboard-card filter-card">
          <div className="card-header">
            <div>
              <span className="section-icon">
                <Filter size={18} />
              </span>

              <div>
                <h2>Filter exceptions</h2>
                <p>Narrow the current organization’s results.</p>
              </div>
            </div>

            {hasActiveFilters ? (
              <button
                type="button"
                className="text-button"
                onClick={handleClearFilters}
              >
                <X size={16} />
                Clear filters
              </button>
            ) : null}
          </div>

          <form
            className="filter-grid"
            onSubmit={handleFilterSubmit}
          >
            <label>
              Reason
              <select
                value={reasonCode}
                onChange={(event) =>
                  setReasonCode(event.target.value)
                }
              >
                <option value="">All reason codes</option>

                {REASON_CODES.map((code) => (
                  <option key={code} value={code}>
                    {formatReasonCode(code)}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Record ID
              <div className="input-with-icon">
                <Search size={16} />
                <input
                  type="text"
                  value={recordId}
                  placeholder="REC-1234"
                  onChange={(event) =>
                    setRecordId(event.target.value)
                  }
                />
              </div>
            </label>

            <label>
              Location ID
              <div className="input-with-icon">
                <MapPin size={16} />
                <input
                  type="text"
                  value={locationId}
                  placeholder="LOC-123"
                  onChange={(event) =>
                    setLocationId(event.target.value)
                  }
                />
              </div>
            </label>

            <button className="primary-button" type="submit">
              <Filter size={17} />
              Apply filters
            </button>
          </form>
        </section>
        <DashboardCharts exceptions={exceptions} />
        <section className="dashboard-card qa-card">
          <div className="qa-accent">
            <Sparkles size={20} />
          </div>

          <div className="card-header">
            <div>
              <span className="section-icon section-icon-purple">
                <Bot size={18} />
              </span>

              <div>
                <h2>Ask ReconGuard</h2>
                <p>
                  Answers use only visible reconciliation exception
                  rows.
                </p>
              </div>
            </div>
          </div>

          <form
            className="qa-form"
            onSubmit={handleQuestionSubmit}
          >
            <input
              type="text"
              value={question}
              maxLength={500}
              placeholder="Which records have value mismatches?"
              onChange={(event) =>
                setQuestion(event.target.value)
              }
            />

            <button
              className="primary-button"
              type="submit"
              disabled={isAskingQuestion}
            >
              {isAskingQuestion ? (
                <RefreshCw className="spin" size={17} />
              ) : (
                <Sparkles size={17} />
              )}

              {isAskingQuestion ? "Checking..." : "Ask"}
            </button>
          </form>

          {questionError ? (
            <div className="inline-error" role="alert">
              <CircleAlert size={17} />
              {questionError}
            </div>
          ) : null}

          {questionResult ? (
            <div
              className={
                questionResult.supported
                  ? "answer-panel"
                  : "answer-panel answer-panel-refused"
              }
            >
              <div className="answer-status">
                <span>
                  {questionResult.supported
                    ? "Grounded answer"
                    : "Unsupported question"}
                </span>

                <strong>
                  {questionResult.supported
                    ? "Supported"
                    : "Refused"}
                </strong>
              </div>

              <p>{questionResult.answer}</p>

              {questionResult.citations.length > 0 ? (
                <div className="citation-row">
                  <span>Citations</span>

                  {questionResult.citations.map((citation) => (
                    <button
                      key={citation}
                      type="button"
                      onClick={() =>
                        document
                          .getElementById(
                            `exception-row-${citation}`,
                          )
                          ?.scrollIntoView({
                            behavior: "smooth",
                            block: "center",
                          })
                      }
                    >
                      #{citation}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="dashboard-card table-card">
          <div className="card-header">
            <div>
              <span className="section-icon">
                <FileWarning size={18} />
              </span>

              <div>
                <h2>Reconciliation exceptions</h2>
                <p>
                  {hasActiveFilters
                    ? `${count} filtered result${
                        count === 1 ? "" : "s"
                      }`
                    : `${count} visible result${
                        count === 1 ? "" : "s"
                      }`}
                </p>
              </div>
            </div>

            <button
              type="button"
              className="icon-button"
              onClick={() =>
                void loadExceptions(activeFilters)
              }
              aria-label="Refresh exceptions"
            >
              <RefreshCw size={17} />
            </button>
          </div>

          {isLoading ? (
            <div className="loading-state">
              <RefreshCw className="spin" size={24} />
              <p>Loading exceptions...</p>
            </div>
          ) : null}

          {error ? (
            <div className="error-state">
              <CircleAlert size={26} />
              <div>
                <strong>Unable to load exceptions</strong>
                <p>{error}</p>
              </div>

              <button
                type="button"
                onClick={() =>
                  void loadExceptions(activeFilters)
                }
              >
                Retry
              </button>
            </div>
          ) : null}

          {!isLoading && !error && exceptions.length === 0 ? (
            <div className="empty-state">
              <ShieldCheck size={34} />
              <h3>No exceptions found</h3>
              <p>
                No rows match the current filter selection.
              </p>
            </div>
          ) : null}

          {!isLoading && !error && exceptions.length > 0 ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Record</th>
                    <th>Location</th>
                    <th>Reason</th>
                    <th>Explanation</th>
                    <th>System B entries</th>
                    <th>Created</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {exceptions.map((exception) => (
                    <tr
                      key={exception.id}
                      id={`exception-row-${exception.id}`}
                    >
                      <td>
                        <span className="row-number">
                          #{exception.id}
                        </span>
                      </td>

                      <td>
                        <strong className="record-id">
                          {exception.record_id}
                        </strong>
                      </td>

                      <td>
                        <span className="location-cell">
                          <MapPin size={14} />
                          {exception.location_id ?? "Unknown"}
                        </span>
                      </td>

                      <td>
                        <span
                          className={getReasonClass(
                            exception.reason_code,
                          )}
                        >
                          {formatReasonCode(
                            exception.reason_code,
                          )}
                        </span>
                      </td>

                      <td className="explanation-cell">
                        {exception.reason}
                      </td>

                      <td>
                        {exception.system_b_entry_ids.length >
                        0
                          ? exception.system_b_entry_ids.join(
                              ", ",
                            )
                          : "—"}
                      </td>

                      <td className="created-cell">
                        {formatDate(exception.created_at)}
                      </td>

                      <td>
                        <ChevronRight
                          className="row-chevron"
                          size={17}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </main>
    </div>
    </div>
  );
}