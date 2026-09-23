export async function api(
  path,
  { token, method = "GET", body, signal } = {},
) {
  const headers = {};

  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let response;

  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Unable to connect. Check that both servers are running.");
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    let detail = data?.detail;

    if (Array.isArray(detail)) {
      detail = detail
        .map((item) => `${item.loc.at(-1)}: ${item.msg}`)
        .join("; ");
    }

    const error = new Error(
      response.status >= 500
        ? "The server could not complete the request. Please try again."
        : typeof detail === "string"
          ? detail
          : `Request failed (${response.status}).`,
    );

    error.status = response.status;
    throw error;
  }

  return data;
}