import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

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
    .map(
      (word) =>
        word.charAt(0).toUpperCase() + word.slice(1),
    )
    .join(" ");
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
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
  
    return () => {
      window.clearTimeout(timeoutId);
    };
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
      // Clear local authentication even if the backend is unavailable.
    } finally {
      clearAuthentication();
      setIsLoggingOut(false);
    }
  }

  return (
    <main className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">
            {user?.organization_name ?? "Organization"}
          </p>

          <h1>Reconciliation Exceptions</h1>

          <p>
            Review exceptions visible to{" "}
            {user?.username ?? "the current user"}.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={handleLogout}
          disabled={isLoggingOut}
        >
          {isLoggingOut ? "Logging out..." : "Logout"}
        </button>
      </header>

      <section className="summary-card">
        <span>Visible exceptions</span>
        <strong>{count}</strong>
      </section>

      <section className="panel">
        <h2>Filters</h2>

        <form
          className="filter-form"
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
              <option value="">All reasons</option>

              {REASON_CODES.map((code) => (
                <option key={code} value={code}>
                  {formatReasonCode(code)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Record ID
            <input
              type="text"
              value={recordId}
              placeholder="REC-1001"
              onChange={(event) =>
                setRecordId(event.target.value)
              }
            />
          </label>

          <label>
            Location ID
            <input
              type="text"
              value={locationId}
              placeholder="LOC-101"
              onChange={(event) =>
                setLocationId(event.target.value)
              }
            />
          </label>

          <div className="filter-actions">
            <button type="submit">Apply filters</button>

            <button
              type="button"
              className="secondary-button"
              onClick={handleClearFilters}
            >
              Clear
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Ask about exceptions</h2>
            <p>
              Answers are limited to your organization&apos;s
              visible reconciliation rows.
            </p>
          </div>
        </div>

        <form
          className="question-form"
          onSubmit={handleQuestionSubmit}
        >
          <label htmlFor="exception-question">
            Question
          </label>

          <div className="question-input-row">
            <input
              id="exception-question"
              type="text"
              value={question}
              placeholder="Which records have value mismatches?"
              maxLength={500}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
            />

            <button
              type="submit"
              disabled={isAskingQuestion}
            >
              {isAskingQuestion ? "Checking..." : "Ask"}
            </button>
          </div>
        </form>

        {questionError ? (
          <div className="error-message" role="alert">
            {questionError}
          </div>
        ) : null}

        {questionResult ? (
          <div
            className={
              questionResult.supported
                ? "answer-card"
                : "answer-card refusal-card"
            }
          >
            <div className="answer-heading">
              <strong>
                {questionResult.supported
                  ? "Grounded answer"
                  : "Unable to answer"}
              </strong>

              <span>
                {questionResult.supported
                  ? "Supported"
                  : "Unsupported"}
              </span>
            </div>

            <p>{questionResult.answer}</p>

            {questionResult.citations.length > 0 ? (
              <div className="citation-list">
                <span>Cited exception rows:</span>

                {questionResult.citations.map((citation) => (
                  <button
                    key={citation}
                    type="button"
                    className="citation-button"
                    onClick={() => {
                      document
                        .getElementById(
                          `exception-row-${citation}`,
                        )
                        ?.scrollIntoView({
                          behavior: "smooth",
                          block: "center",
                        });
                    }}
                  >
                    #{citation}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Exceptions</h2>

            <p>
              {Object.values(activeFilters).some(Boolean)
                ? "Filtered results"
                : "All visible organization results"}
            </p>
          </div>
        </div>

        {isLoading ? (
          <p className="state-message">
            Loading exceptions...
          </p>
        ) : null}

        {error ? (
          <div className="error-message" role="alert">
            <p>{error}</p>

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

        {!isLoading &&
        !error &&
        exceptions.length === 0 ? (
          <p className="state-message">
            No exceptions match the selected filters.
          </p>
        ) : null}

        {!isLoading &&
        !error &&
        exceptions.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Row ID</th>
                  <th>Record</th>
                  <th>Location</th>
                  <th>Reason</th>
                  <th>Explanation</th>
                  <th>System B entries</th>
                  <th>Created</th>
                </tr>
              </thead>

              <tbody>
                {exceptions.map((exception) => (
                  <tr
                    key={exception.id}
                    id={`exception-row-${exception.id}`}
                  >
                    <td>#{exception.id}</td>
                    <td>{exception.record_id}</td>
                    <td>
                      {exception.location_id ?? "Unknown"}
                    </td>
                    <td>
                      <span className="reason-badge">
                        {formatReasonCode(
                          exception.reason_code,
                        )}
                      </span>
                    </td>
                    <td>{exception.reason}</td>
                    <td>
                      {exception.system_b_entry_ids.length >
                      0
                        ? exception.system_b_entry_ids.join(
                            ", ",
                          )
                        : "—"}
                    </td>
                    <td>
                      {formatDate(exception.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </main>
  );
}