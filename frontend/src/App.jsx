import { useEffect, useState } from "react";
import { api } from "./api";

const statuses = {
  applied: "Applied",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};

const emptyForm = {
  company: "",
  position: "",
  vacancy_url: "",
  notes: "",
  status: "applied",
};

const pageSize = 10;

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function Brand({ centered = false }) {
  return (
    <div className={`brand ${centered ? "centered" : ""}`}>
      {centered && <div className="brand-mark" aria-hidden="true">↗</div>}
      <p className="eyebrow">YOUR NEXT CHAPTER</p>
      <h1>Job Application Tracker</h1>
      <p className="subtitle">
        Stay organized. Track your progress. Find your next opportunity.
      </p>
    </div>
  );
}

function Notice({ notice }) {
  if (!notice.text) return null;

  return (
    <p
      className={`notice ${notice.error ? "error" : ""}`}
      role={notice.error ? "alert" : "status"}
    >
      {notice.text}
    </p>
  );
}

function AuthForm({ onAuthenticated, notify }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const registering = mode === "register";

  async function submit(event) {
    event.preventDefault();
    if (busy) return;

    setBusy(true);
    notify("");

    try {
      const credentials = { email: email.trim(), password };

      if (registering) {
        await api("/auth/register", {
          method: "POST",
          body: credentials,
        });
      }

      const result = await api("/auth/login", {
        method: "POST",
        body: credentials,
      });

      setPassword("");
      onAuthenticated(result.access_token);
    } catch (error) {
      notify(error.message, true);
    } finally {
      setBusy(false);
    }
  }

  function switchMode() {
    setMode(registering ? "login" : "register");
    setPassword("");
    notify("");
  }

  return (
    <section className="panel auth-panel">
      <h2>{registering ? "Create your account" : "Welcome back"}</h2>
      <p className="muted">
        {registering
          ? "Bring your next opportunity a little closer."
          : "Sign in to continue your job search."}
      </p>

      <form onSubmit={submit}>
        <label htmlFor="email">Email address</label>
        <input
          id="email"
          type="email"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="you@example.com"
          maxLength={255}
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete={registering ? "new-password" : "current-password"}
          placeholder={registering ? "At least 8 characters" : "Your password"}
          minLength={registering ? 8 : 1}
          maxLength={128}
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <button className="full-width" disabled={busy}>
          {busy
            ? "Please wait…"
            : registering
              ? "Create account"
              : "Sign in"}
        </button>

        <button
          type="button"
          className="secondary full-width"
          disabled={busy}
          onClick={switchMode}
        >
          {registering
            ? "Already have an account? Sign in"
            : "New here? Create an account"}
        </button>
      </form>

      <p className="auth-footer">
        A little structure for your next big step.
      </p>
    </section>
  );
}

function Dashboard({ token, onLogout, notify }) {
  const [user, setUser] = useState(null);
  const [summary, setSummary] = useState(null);
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ ...emptyForm });
  const [editingId, setEditingId] = useState(null);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState({ search: "", status: "", offset: 0 });

  const [version, setVersion] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [hasNext, setHasNext] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setLoadError("");

      const params = new URLSearchParams({
        limit: String(pageSize + 1),
        offset: String(query.offset),
      });

      if (query.search) params.set("search", query.search);
      if (query.status) params.set("status", query.status);

      try {
        const options = { token, signal: controller.signal };

        const [me, stats, applications] = await Promise.all([
          api("/auth/me", options),
          api("/applications/summary", options),
          api(`/applications/?${params}`, options),
        ]);

        if (controller.signal.aborted) return;

        if (!applications.length && query.offset > 0) {
          setQuery((current) => ({
            ...current,
            offset: Math.max(0, current.offset - pageSize),
          }));
          return;
        }

        setUser(me);
        setSummary(stats);
        setItems(applications.slice(0, pageSize));
        setHasNext(applications.length > pageSize);
      } catch (error) {
        if (controller.signal.aborted) return;

        if (error.status === 401) {
          onLogout("Your session has expired. Please sign in again.");
        } else {
          setLoadError(error.message);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [token, query, version, onLogout]);

  function resetForm() {
    setEditingId(null);
    setForm({ ...emptyForm });
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function handleError(error) {
    if (error.status === 401) {
      onLogout("Your session has expired. Please sign in again.");
    } else {
      notify(error.message, true);
    }
  }

  async function save(event) {
    event.preventDefault();
    if (saving) return;

    const body = {
      company: form.company.trim(),
      position: form.position.trim(),
      vacancy_url: form.vacancy_url.trim() || null,
      notes: form.notes.trim() || null,
    };

    if (!body.company || !body.position) {
      notify("Company and position cannot be blank.", true);
      return;
    }

    if (body.vacancy_url && !safeUrl(body.vacancy_url)) {
      notify("Please enter an HTTP or HTTPS job posting URL.", true);
      return;
    }

    const editing = editingId !== null;
    if (editing) body.status = form.status;

    setSaving(true);
    notify("");

    try {
      await api(
        editing ? `/applications/${editingId}` : "/applications/",
        {
          token,
          method: editing ? "PATCH" : "POST",
          body,
        },
      );

      resetForm();
      setVersion((value) => value + 1);
      notify(editing ? "Application updated." : "Application added.");
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  }

  function edit(application) {
    setEditingId(application.id);
    setForm({
      company: application.company,
      position: application.position,
      vacancy_url: application.vacancy_url ?? "",
      notes: application.notes ?? "",
      status: application.status,
    });

    document.getElementById("company")?.focus();
  }

  async function remove(application) {
    if (deletingId !== null) return;
    if (!window.confirm(`Delete your application to ${application.company}?`)) {
      return;
    }

    setDeletingId(application.id);
    notify("");

    try {
      await api(`/applications/${application.id}`, {
        token,
        method: "DELETE",
      });

      if (editingId === application.id) resetForm();
      setVersion((value) => value + 1);
      notify("Application deleted.");
    } catch (error) {
      handleError(error);
    } finally {
      setDeletingId(null);
    }
  }

  function filter(event) {
    event.preventDefault();
    setQuery({ search: search.trim(), status, offset: 0 });
  }

  return (
    <>
      <p className="account">{user?.email ?? "Loading your workspace…"}</p>

      <div className="stats">
        {Object.entries({ total: "Total", ...statuses }).map(([key, label]) => (
          <div className="stat" key={key}>
            <span>{label}</span>
            <strong>{summary?.[key] ?? "—"}</strong>
          </div>
        ))}
      </div>

      <div className="workspace">
        <section className="panel editor">
          <p className="eyebrow">KEEP MOVING FORWARD</p>
          <h2>{editingId === null ? "New application" : "Edit application"}</h2>

          <form onSubmit={save}>
            <fieldset disabled={saving}>
              <label htmlFor="company">Company</label>
              <input
                id="company"
                name="company"
                placeholder="Company name"
                maxLength={100}
                required
                value={form.company}
                onChange={updateField}
              />

              <label htmlFor="position">Position</label>
              <input
                id="position"
                name="position"
                placeholder="e.g. Python Developer"
                maxLength={100}
                required
                value={form.position}
                onChange={updateField}
              />

              <label htmlFor="vacancy-url">Job posting URL · Optional</label>
              <input
                id="vacancy-url"
                name="vacancy_url"
                type="url"
                placeholder="https://example.com/careers"
                value={form.vacancy_url}
                onChange={updateField}
              />

              {editingId !== null && (
                <>
                  <label htmlFor="application-status">Status</label>
                  <select
                    id="application-status"
                    name="status"
                    value={form.status}
                    onChange={updateField}
                  >
                    {Object.entries(statuses).map(([value, label]) => (
                      <option value={value} key={value}>{label}</option>
                    ))}
                  </select>
                </>
              )}

              <label htmlFor="notes">Notes · Optional</label>
              <textarea
                id="notes"
                name="notes"
                rows={4}
                placeholder="Contacts, interview details, or next steps…"
                value={form.notes}
                onChange={updateField}
              />

              <div className="actions">
                <button type="submit">
                  {saving
                    ? "Saving…"
                    : editingId === null
                      ? "Add application"
                      : "Save changes"}
                </button>

                {editingId !== null && (
                  <button
                    type="button"
                    className="secondary"
                    onClick={resetForm}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </fieldset>
          </form>
        </section>

        <section className="panel">
          <p className="eyebrow">YOUR OPPORTUNITIES</p>
          <h2>My applications</h2>

          <form className="filters" onSubmit={filter} role="search">
            <input
              aria-label="Search company or position"
              type="search"
              placeholder="Search company or position"
              maxLength={100}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <select
              aria-label="Filter by status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option value="">All statuses</option>
              {Object.entries(statuses).map(([value, label]) => (
                <option value={value} key={value}>{label}</option>
              ))}
            </select>
            <button disabled={loading}>Search</button>
          </form>

          <div aria-busy={loading}>
            {loading ? (
              <p className="empty" role="status">Loading applications…</p>
            ) : loadError ? (
              <div className="empty">
                <p role="alert">{loadError}</p>
                <button
                  className="secondary"
                  onClick={() => setVersion((value) => value + 1)}
                >
                  Try again
                </button>
              </div>
            ) : items.length === 0 ? (
              <div className="empty">
                <h3>No applications found</h3>
                <p>Add your first application or adjust your filters.</p>
              </div>
            ) : (
              items.map((application) => {
                const url = safeUrl(application.vacancy_url);

                return (
                  <article className="application" key={application.id}>
                    <div className="card-heading">
                      <div>
                        <h3>{application.position}</h3>
                        <p className="company">{application.company}</p>
                      </div>
                      <span className={`badge ${application.status}`}>
                        {statuses[application.status]}
                      </span>
                    </div>

                    {application.notes && (
                      <p className="notes">{application.notes}</p>
                    )}

                    {url && (
                      <a href={url} target="_blank" rel="noopener noreferrer">
                        Open job posting ↗
                      </a>
                    )}

                    <div className="actions">
                      <button
                        className="secondary"
                        disabled={saving || deletingId !== null}
                        onClick={() => edit(application)}
                      >
                        Edit
                      </button>
                      <button
                        className="danger"
                        disabled={saving || deletingId !== null}
                        onClick={() => remove(application)}
                      >
                        {deletingId === application.id ? "Deleting…" : "Delete"}
                      </button>
                    </div>
                  </article>
                );
              })
            )}
          </div>

          <nav className="pagination" aria-label="Application pages">
            <button
              className="secondary"
              disabled={loading || !!loadError || query.offset === 0}
              onClick={() => setQuery((current) => ({
                ...current,
                offset: Math.max(0, current.offset - pageSize),
              }))}
            >
              ← Previous
            </button>
            <span>Page {query.offset / pageSize + 1}</span>
            <button
              className="secondary"
              disabled={loading || !!loadError || !hasNext}
              onClick={() => setQuery((current) => ({
                ...current,
                offset: current.offset + pageSize,
              }))}
            >
              Next →
            </button>
          </nav>
        </section>
      </div>
    </>
  );
}

export default function App() {
  const [token, setToken] = useState(
    () => sessionStorage.getItem("access_token"),
  );
  const [notice, setNotice] = useState({ text: "", error: false });

  function notify(text, error = false) {
    setNotice({ text, error });
  }

  // Stable function identity prevents unnecessary dashboard reloads.
  const [logout] = useState(() => (text = "You have signed out.") => {
    sessionStorage.removeItem("access_token");
    setToken(null);
    setNotice({ text, error: false });
  });

  function authenticated(value) {
    sessionStorage.setItem("access_token", value);
    setToken(value);
    notify("");
  }

  return (
    <main className={`app-shell ${token ? "" : "auth-layout"}`}>
      <header className="site-header">
        <Brand centered={!token} />
        {token && (
          <button className="secondary" onClick={() => logout()}>
            Sign out
          </button>
        )}
      </header>

      <Notice notice={notice} />

      {token ? (
        <Dashboard
          key={token}
          token={token}
          onLogout={logout}
          notify={notify}
        />
      ) : (
        <AuthForm onAuthenticated={authenticated} notify={notify} />
      )}
    </main>
  );
}