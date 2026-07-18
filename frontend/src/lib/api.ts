import type {
  ExceptionFilters,
  ExceptionListResponse,
  ExceptionQuestionResponse,
  LoginResponse,
} from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();

    return (
      data.non_field_errors?.[0] ??
      data.detail ??
      "The request could not be completed."
    );
  } catch {
    return "The request could not be completed.";
  }
}

export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      password,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as LoginResponse;
}

export async function getExceptions(
  token: string,
  filters: ExceptionFilters = {},
): Promise<ExceptionListResponse> {
  const queryParams = new URLSearchParams();

  if (filters.reasonCode) {
    queryParams.set("reason_code", filters.reasonCode);
  }

  if (filters.recordId?.trim()) {
    queryParams.set("record_id", filters.recordId.trim());
  }

  if (filters.locationId?.trim()) {
    queryParams.set("location_id", filters.locationId.trim());
  }

  const queryString = queryParams.toString();
  const url = `${API_BASE_URL}/api/exceptions/${
    queryString ? `?${queryString}` : ""
  }`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (response.status === 401) {
    throw new Error("SESSION_EXPIRED");
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as ExceptionListResponse;
}

export async function logout(token: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/logout/`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok && response.status !== 401) {
    throw new Error(await parseError(response));
  }
}

export async function askExceptionQuestion(
  token: string,
  question: string,
): Promise<ExceptionQuestionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/exceptions/ask/`,
    {
      method: "POST",
      headers: {
        Authorization: `Token ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
      }),
    },
  );

  if (response.status === 401) {
    throw new Error("SESSION_EXPIRED");
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as ExceptionQuestionResponse;
}
