import {
  ArrowLeft,
  ArrowRight,
  BusFront,
  CalendarDays,
  Check,
  Clock3,
  MapPin,
  MessageSquareText,
  Route as RouteIcon,
  Send,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useApi, getApiError } from "../hooks/useApi.js";
import { announcementsApi } from "../services/announcements.js";
import { feedbackApi } from "../services/feedback.js";
import { routesApi } from "../services/routes.js";
import { shuttleStatusApi } from "../services/shuttleStatus.js";
import { shuttlesApi } from "../services/shuttles.js";
import { stopsApi } from "../services/stops.js";
import {
  Button,
  EmptyState,
  ErrorState,
  FormField,
  Loading,
  PageHeader,
  Panel,
  Pagination,
  SearchField,
  StatusBadge,
  formatDate,
} from "../components/ui.jsx";

function usePagedList(load, searchKey = "q") {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const params = useMemo(() => ({
    skip: (page - 1) * 50,
    limit: 50,
    ...(query.trim() ? { [searchKey]: query.trim() } : {}),
  }), [page, query, searchKey]);
  const result = useApi(() => load(params), [load, params]);
  return { ...result, query, setQuery, page, setPage, params };
}

function ResourceState({ loading, error, refresh, children, empty, hasItems }) {
  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!hasItems) return empty;
  return children;
}

function RouteCard({ route }) {
  const firstStop = route.route_stops?.[0]?.stop?.name;
  const lastStop = route.route_stops?.at(-1)?.stop?.name;
  return (
    <Link className="route-card" to={`/student/routes/${route.id}`}>
      <div className="route-card__top"><span className="route-code">{route.code}</span><ArrowRight size={17} /></div>
      <h3>{route.name}</h3>
      <p className="route-card__endpoints">{firstStop || "Stops not listed"} <span>→</span> {lastStop || "—"}</p>
      <div className="route-card__meta">
        <span><MapPin size={14} /> {route.route_stops?.length || 0} stops</span>
        <span><Clock3 size={14} /> {route.estimated_duration_minutes ? `${route.estimated_duration_minutes} min estimate` : "Duration not configured"}</span>
      </div>
    </Link>
  );
}

function StopCard({ stop }) {
  const related = stop.route_count;
  return (
    <Link className="stop-card" to={`/student/stops/${stop.id}`}>
      <span className="stop-card__icon"><MapPin size={19} /></span>
      <div className="stop-card__content">
        <h3>{stop.name}</h3>
        <p>{stop.description || "Campus shuttle stop"}</p>
        <span className="stop-card__meta">{related === undefined ? "View stop details and routes" : `${related} ${related === 1 ? "route" : "routes"}`}</span>
      </div>
      <ArrowRight size={17} className="stop-card__arrow" />
    </Link>
  );
}

export function Overview() {
  const { user } = useAuth();
  const routes = useApi(() => routesApi.list({ limit: 4 }), []);
  const stops = useApi(() => stopsApi.list({ limit: 4 }), []);
  const statuses = useApi(() => shuttleStatusApi.list({ limit: 4 }), []);
  const announcements = useApi(() => announcementsApi.list({ limit: 3 }), []);
  const anyError = routes.error || stops.error || statuses.error || announcements.error;

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="STUDENT DASHBOARD"
        title={`Good day, ${user?.full_name?.split(" ")[0] || "there"}`}
        description="Here’s the latest campus shuttle information to help you plan your next trip."
        action={<Link className="button button--primary" to="/student/feedback"><MessageSquareText size={16} /> Send feedback</Link>}
      />
      {anyError && <ErrorState message={anyError} onRetry={() => [routes.refresh(), stops.refresh(), statuses.refresh(), announcements.refresh()]} />}
      <div className="student-dashboard-grid">
        <section className="dashboard-main-column">
          <Panel title="Current service status" subtitle="Latest manually reported shuttle updates" action={<Link className="panel-link" to="/student/shuttles">View all <ArrowRight size={14} /></Link>}>
            {statuses.loading ? <Loading /> : statuses.data?.items?.length ? (
              <div className="status-list">
                {statuses.data.items.map((item) => (
                  <Link key={item.shuttle.id} to={`/student/shuttles/${item.shuttle.id}`} className="status-row">
                    <span className="status-row__icon"><BusFront size={17} /></span>
                    <span className="status-row__name"><strong>{item.shuttle.vehicle_code}</strong><small>{item.shuttle.is_active ? "Service vehicle" : "Inactive vehicle"}</small></span>
                    <span className="status-row__updated"><StatusBadge status={item.status} /><small>{item.last_updated_at ? `Updated ${formatDate(item.last_updated_at)}` : "No updates recorded"}</small></span>
                  </Link>
                ))}
              </div>
            ) : <EmptyState title="No shuttle updates yet" description="Service status will appear here when the transport team records an update." />}
          </Panel>
          <Panel title="Available routes" subtitle="Explore stops and route information" action={<Link className="panel-link" to="/student/routes">All routes <ArrowRight size={14} /></Link>}>
            {routes.loading ? <Loading /> : routes.data?.items?.length ? (
              <div className="route-card-grid">{routes.data.items.map((route) => <RouteCard key={route.id} route={route} />)}</div>
            ) : <EmptyState title="Routes will appear here" description="There are no active routes available yet." />}
          </Panel>
        </section>
        <aside className="dashboard-side-column">
          <Panel title="Campus stops" subtitle="Find your nearest shuttle stop" action={<Link className="panel-link" to="/student/stops">Browse <ArrowRight size={14} /></Link>}>
            {stops.loading ? <Loading /> : stops.data?.items?.length ? (
              <div className="compact-list">
                {stops.data.items.map((stop) => (
                  <Link key={stop.id} className="compact-item" to={`/student/stops/${stop.id}`}>
                    <span className="compact-item__icon"><MapPin size={15} /></span>
                    <span><strong>{stop.name}</strong><small>{stop.description || "Campus stop"}</small></span>
                    <ArrowRight size={15} />
                  </Link>
                ))}
              </div>
            ) : <EmptyState title="No stops listed" description="Configured campus stops will appear here." />}
          </Panel>
          <Panel title="Latest announcements" subtitle="Updates from the transport team" action={<Link className="panel-link" to="/student/announcements">All updates <ArrowRight size={14} /></Link>}>
            {announcements.loading ? <Loading /> : announcements.data?.items?.length ? (
              <div className="announcement-mini-list">
                {announcements.data.items.map((item) => (
                  <article key={item.id} className="announcement-mini">
                    <span className="announcement-mini__date">{formatDate(item.starts_at || item.created_at, { timeStyle: undefined })}</span>
                    <h3>{item.title}</h3>
                    <p>{item.body}</p>
                  </article>
                ))}
              </div>
            ) : <EmptyState title="No announcements" description="Published service updates will appear here." />}
          </Panel>
          <div className="info-callout">
            <span><ShieldCheck size={17} /></span>
            <p><strong>Information you can trust</strong>Service updates are manually reported by administrators, not live tracking.</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

export function Stops() {
  const loadStops = useMemo(() => (params) => stopsApi.list(params), []);
  const { data, loading, error, refresh, query, setQuery, page, setPage } = usePagedList(loadStops);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  return (
    <div className="page-content">
      <PageHeader eyebrow="EXPLORE CAMPUS" title="Campus stops" description="Find shuttle stops across campus and see where each one can take you." />
      <div className="toolbar"><SearchField value={query} onChange={setQuery} placeholder="Search stops" /></div>
      <ResourceState loading={loading} error={error} refresh={refresh} hasItems={data?.items?.length} empty={<EmptyState title="No stops found" description={query ? "Try a different search term." : "Active campus stops will appear here when they're added."} />}>
        <div className="stop-card-grid">{items.map((stop) => <StopCard key={stop.id} stop={stop} />)}</div>
        <Pagination page={page} limit={50} total={total} onPageChange={setPage} />
        <div className="list-footnote">Page {page} · {total} active {total === 1 ? "stop" : "stops"}</div>
      </ResourceState>
    </div>
  );
}

export function StopDetails() {
  const { stopId } = useParams();
  const stop = useApi(() => stopsApi.get(stopId), [stopId]);
  const routes = useApi(() => routesApi.list({ limit: 100 }), []);
  const matchingRoutes = routes.data?.items?.filter((route) => route.route_stops?.some((item) => item.stop_id === stopId)) || [];
  const serviceStatus = useApi(() => shuttleStatusApi.list({ limit: 100 }), []);
  const servingRouteIds = new Set(matchingRoutes.map((route) => route.id));
  const matchingStatuses = serviceStatus.data?.items?.filter((item) => servingRouteIds.has(item.shuttle.route_id)) || [];
  return (
    <div className="page-content">
      <Link to="/student/stops" className="back-link"><ArrowLeft size={16} /> All campus stops</Link>
      {stop.loading ? <Loading /> : stop.error ? <ErrorState message={stop.error} onRetry={stop.refresh} /> : (
        <>
          <PageHeader eyebrow="CAMPUS STOP" title={stop.data.name} description={stop.data.description || "Shuttle stop information and available routes."} />
          <div className="detail-grid">
            <Panel title="Stop information">
              <div className="detail-facts"><span><MapPin size={17} /> Stop name</span><strong>{stop.data.name}</strong><span>Directory status</span><strong>Active</strong></div>
              <p className="subtle-copy">This stop is listed in the active campus directory. Shuttle service status is shown separately.</p>
            </Panel>
            <Panel title="Routes serving this stop" subtitle="Active routes that include this stop">
              {routes.loading ? <Loading /> : routes.error ? <ErrorState message={routes.error} onRetry={routes.refresh} /> : matchingRoutes.length ? <div className="compact-list">{matchingRoutes.map((route) => <Link key={route.id} className="compact-item" to={`/student/routes/${route.id}`}><span className="route-code">{route.code}</span><span><strong>{route.name}</strong><small>{route.route_stops.length} listed stops</small></span><ArrowRight size={15} /></Link>)}</div> : <EmptyState title="No routes listed" description="No active route currently includes this stop." />}
            </Panel>
            <Panel title="Shuttle service status" subtitle="Latest manual reports for routes serving this stop">
              {serviceStatus.loading ? <Loading /> : serviceStatus.error ? <ErrorState message={serviceStatus.error} onRetry={serviceStatus.refresh} /> : matchingStatuses.length ? <div className="status-list">{matchingStatuses.map((item) => <Link key={item.shuttle.id} to={`/student/shuttles/${item.shuttle.id}`} className="status-row"><span className="status-row__icon"><BusFront size={17} /></span><span className="status-row__name"><strong>{item.shuttle.vehicle_code}</strong><small>{item.message || "No administrator message"}</small></span><span className="status-row__updated"><StatusBadge status={item.status} /><small>{item.last_updated_at ? `Updated ${formatDate(item.last_updated_at)}` : "No updates recorded"}</small></span></Link>)}</div> : <EmptyState title="No shuttle status for this stop" description="Status appears when a shuttle is assigned to a route serving this stop." />}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}

export function Routes() {
  const loadRoutes = useMemo(() => (params) => routesApi.list(params), []);
  const { data, loading, error, refresh, query, setQuery, page, setPage } = usePagedList(loadRoutes);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  return (
    <div className="page-content">
      <PageHeader eyebrow="PLAN YOUR JOURNEY" title="Shuttle routes" description="Review active routes, their ordered stops, and estimated journey durations when configured." />
      <div className="toolbar"><SearchField value={query} onChange={setQuery} placeholder="Search by route name or code" /></div>
      <ResourceState loading={loading} error={error} refresh={refresh} hasItems={data?.items?.length} empty={<EmptyState title="No routes found" description={query ? "Try another route name or code." : "Active shuttle routes will appear here when configured."} />}>
        <div className="route-card-grid route-card-grid--wide">{items.map((route) => <RouteCard key={route.id} route={route} />)}</div>
        <Pagination page={page} limit={50} total={total} onPageChange={setPage} />
        <div className="list-footnote">Page {page} · {total} active {total === 1 ? "route" : "routes"}</div>
      </ResourceState>
    </div>
  );
}

export function RouteDetails() {
  const { routeId } = useParams();
  const route = useApi(() => routesApi.get(routeId), [routeId]);
  const status = useApi(() => shuttleStatusApi.byRoute(routeId, { limit: 50 }), [routeId]);
  return (
    <div className="page-content">
      <Link to="/student/routes" className="back-link"><ArrowLeft size={16} /> All routes</Link>
      {route.loading ? <Loading /> : route.error ? <ErrorState message={route.error} onRetry={route.refresh} /> : (
        <>
          <PageHeader eyebrow={`ROUTE ${route.data.code}`} title={route.data.name} description="Stops are shown in the order currently configured by the transport team." />
          <div className="detail-grid detail-grid--wide">
            <Panel title="Route stops" subtitle={`${route.data.route_stops.length} stops on this route`}>
              {route.data.route_stops.length ? <ol className="stop-timeline">{route.data.route_stops.map((item, index) => <li key={item.stop_id}><span className="stop-timeline__number">{String(index + 1).padStart(2, "0")}</span><span><Link to={`/student/stops/${item.stop_id}`}>{item.stop.name}</Link>{index === 0 && <small>Starting stop</small>}{index === route.data.route_stops.length - 1 && route.data.route_stops.length > 1 && <small>Last listed stop</small>}</span><MapPin size={15} /></li>)}</ol> : <EmptyState title="No stops added" description="Route stops have not been configured yet." />}
            </Panel>
            <div className="stacked-panels">
              <Panel title="Journey information">
                <div className="detail-facts"><span>Route code</span><strong>{route.data.code}</strong><span>Availability</span><strong>{route.data.is_active ? "Available" : "Unavailable"}</strong><span>Estimated duration</span><strong>{route.data.estimated_duration_minutes ? `${route.data.estimated_duration_minutes} minutes` : "Not configured"}</strong></div>
              </Panel>
              <Panel title="Shuttle service status" subtitle="Latest manual reports for this route">
                {status.loading ? <Loading /> : status.error ? <ErrorState message={status.error} onRetry={status.refresh} /> : status.data?.items?.length ? <div className="status-list">{status.data.items.map((item) => <Link key={item.shuttle.id} to={`/student/shuttles/${item.shuttle.id}`} className="status-row"><span className="status-row__icon"><BusFront size={16} /></span><span className="status-row__name"><strong>{item.shuttle.vehicle_code}</strong><small>{item.last_updated_at ? `Updated ${formatDate(item.last_updated_at)}` : "No updates recorded"}</small></span><StatusBadge status={item.status} /></Link>)}</div> : <EmptyState title="No assigned shuttles" description="Service status appears when a shuttle is assigned to this route." />}
              </Panel>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function Shuttles() {
  const [search, setSearch] = useState("");
  const items = useApi(() => shuttleStatusApi.list({ limit: 100 }), []);
  const filtered = items.data?.items?.filter((item) =>
    item.shuttle.vehicle_code.toLowerCase().includes(search.toLowerCase())
  ) || [];
  return (
    <div className="page-content">
      <PageHeader eyebrow="CAMPUS TRANSPORT" title="Shuttle information" description="View active shuttle vehicles and the latest service information recorded by the transport team." />
      <div className="toolbar"><SearchField value={search} onChange={setSearch} placeholder="Search vehicle code" /></div>
      {items.loading ? <Loading /> : items.error ? <ErrorState message={items.error} onRetry={items.refresh} /> : filtered.length ? (
        <div className="shuttle-grid">{filtered.map(({ shuttle, status: serviceStatus, message, last_updated_at: updated }) => (
          <Link className="shuttle-card" to={`/student/shuttles/${shuttle.id}`} key={shuttle.id}>
            <div className="shuttle-card__header"><span className="shuttle-card__icon"><BusFront size={20} /></span><StatusBadge status={serviceStatus} /></div>
            <p className="eyebrow">{shuttle.is_active ? "ACTIVE VEHICLE" : "INACTIVE VEHICLE"}</p>
            <h3>{shuttle.vehicle_code}</h3>
            <p>{shuttle.route_id ? "Assigned to a campus route" : "No route assigned"}</p>
            <div className="shuttle-card__foot"><span>{message || (updated ? "No administrator message" : "No updates recorded")}</span><small>{updated ? formatDate(updated) : "Not updated"}</small></div>
          </Link>
        ))}</div>
      ) : <EmptyState title="No shuttles found" description={search ? "Try a different vehicle code." : "Shuttle records will appear here when configured."} />}
      <p className="disclosure-note"><ShieldCheck size={15} /> Status information is manually entered. No live location or arrival prediction is available.</p>
    </div>
  );
}

export function ShuttleDetails() {
  const { shuttleId } = useParams();
  const current = useApi(() => shuttleStatusApi.current(shuttleId), [shuttleId]);
  const history = useApi(() => shuttleStatusApi.history(shuttleId, { limit: 50 }), [shuttleId]);
  return (
    <div className="page-content">
      <Link to="/student/shuttles" className="back-link"><ArrowLeft size={16} /> All shuttles</Link>
      {current.loading ? <Loading /> : current.error ? <ErrorState message={current.error} onRetry={current.refresh} /> : (
        <>
          <PageHeader eyebrow="SHUTTLE DETAILS" title={current.data.shuttle.vehicle_code} description="Service information recorded for this shuttle." action={<StatusBadge status={current.data.status} />} />
          <div className="detail-grid">
            <Panel title="Current service information">
              <div className="detail-facts"><span>Vehicle status</span><strong>{current.data.shuttle.is_active ? "Active" : "Inactive"}</strong><span>Service update</span><StatusBadge status={current.data.status} /><span>Last updated</span><strong>{formatDate(current.data.last_updated_at)}</strong><span>Administrator message</span><strong>{current.data.message || "No message recorded"}</strong></div>
              {current.data.shuttle.route_id && <Link className="button button--secondary detail-action" to={`/student/routes/${current.data.shuttle.route_id}`}>View assigned route <ArrowRight size={15} /></Link>}
            </Panel>
            <Panel title="Status update history" subtitle="Most recent updates appear first">
              {history.loading ? <Loading /> : history.error ? <ErrorState message={history.error} onRetry={history.refresh} /> : history.data?.items?.length ? <div className="history-list">{history.data.items.map((item) => <article key={item.id} className="history-item"><span className="history-item__marker" /><div><StatusBadge status={item.status} /><p>{item.message || "No message provided."}</p><small>{formatDate(item.created_at)}</small></div></article>)}</div> : <EmptyState title="No status history" description="No manual service updates have been recorded for this shuttle." />}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}

export function Announcements() {
  const notices = useApi(() => announcementsApi.list({ limit: 100 }), []);
  return (
    <div className="page-content">
      <PageHeader eyebrow="SERVICE INFORMATION" title="Announcements" description="Published messages and service notices from the transport team." />
      {notices.loading ? <Loading /> : notices.error ? <ErrorState message={notices.error} onRetry={notices.refresh} /> : notices.data?.items?.length ? (
        <div className="announcement-list">{notices.data.items.map((item) => <article key={item.id} className="announcement-card"><div className="announcement-card__date"><CalendarDays size={16} /><span>{formatDate(item.starts_at || item.created_at)}</span></div><h2>{item.title}</h2><p>{item.body}</p>{item.ends_at && <span className="announcement-card__until">Until {formatDate(item.ends_at)}</span>}</article>)}</div>
      ) : <EmptyState title="No announcements yet" description="Published campus shuttle notices will appear here." />}
    </div>
  );
}

const feedbackCategories = [
  ["DELAY", "Delay"],
  ["OVERCROWDING", "Overcrowding"],
  ["INCORRECT_STOP", "Incorrect stop information"],
  ["SUGGESTION", "Suggestion"],
  ["OTHER", "Other"],
];

export function Feedback() {
  const navigate = useNavigate();
  const stops = useApi(() => stopsApi.list({ limit: 100 }), []);
  const routes = useApi(() => routesApi.list({ limit: 100 }), []);
  const shuttles = useApi(() => shuttlesApi.list({ limit: 100 }), []);
  const [form, setForm] = useState({ category: "DELAY", message: "", rating: "", route_id: "", stop_id: "", shuttle_id: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!form.message.trim()) {
      setError("Enter a description before submitting.");
      return;
    }
    setSubmitting(true);
    try {
      await feedbackApi.create({
        category: form.category,
        message: form.message.trim(),
        ...(form.rating ? { rating: Number(form.rating) } : {}),
        ...(form.route_id ? { route_id: form.route_id } : {}),
        ...(form.stop_id ? { stop_id: form.stop_id } : {}),
        ...(form.shuttle_id ? { shuttle_id: form.shuttle_id } : {}),
      });
      setSuccess("Thanks — your feedback has been sent to the transport team.");
      setForm({ category: "DELAY", message: "", rating: "", route_id: "", stop_id: "", shuttle_id: "" });
    } catch (requestError) {
      setError(getApiError(requestError, "Your feedback could not be sent."));
    } finally {
      setSubmitting(false);
    }
  }

  const referenceError = stops.error || routes.error || shuttles.error;
  return (
    <div className="page-content">
      <PageHeader eyebrow="HELP IMPROVE CAMPUS TRANSIT" title="Send feedback" description="Report a service issue or share an idea with the transport team." />
      <div className="form-page-grid">
        <Panel title="Your feedback" subtitle="Fields marked with * are required">
          <form className="portal-form" onSubmit={submit}>
            <label className="form-field"><span>Feedback category <i>*</i></span><select name="category" value={form.category} onChange={update} required>{feedbackCategories.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <FormField as="textarea" name="message" label="What happened?" hint="Please avoid including sensitive personal information." required maxLength={5000} rows={5} value={form.message} onChange={update} />
            <label className="form-field"><span>Overall rating <small>(optional)</small></span><select name="rating" value={form.rating} onChange={update}><option value="">No rating</option>{[5, 4, 3, 2, 1].map((rating) => <option key={rating} value={rating}>{rating} — {rating === 5 ? "Excellent" : rating === 1 ? "Needs improvement" : "Good"}</option>)}</select></label>
            {referenceError && <p className="field-hint">Reference lists could not be loaded. You can still submit feedback without linking a route, stop, or shuttle.</p>}
            <div className="form-row">
              <label className="form-field"><span>Related route <small>(optional)</small></span><select name="route_id" value={form.route_id} onChange={update}><option value="">No route selected</option>{routes.data?.items?.map((route) => <option value={route.id} key={route.id}>{route.code} · {route.name}</option>)}</select></label>
              <label className="form-field"><span>Related stop <small>(optional)</small></span><select name="stop_id" value={form.stop_id} onChange={update}><option value="">No stop selected</option>{stops.data?.items?.map((stop) => <option value={stop.id} key={stop.id}>{stop.name}</option>)}</select></label>
            </div>
            <label className="form-field"><span>Related shuttle <small>(optional)</small></span><select name="shuttle_id" value={form.shuttle_id} onChange={update}><option value="">No shuttle selected</option>{shuttles.data?.items?.map((shuttle) => <option value={shuttle.id} key={shuttle.id}>{shuttle.vehicle_code}</option>)}</select></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            {success && <p className="form-success" role="status"><Check size={16} />{success} <Link to="/student/my-feedback">View my feedback</Link></p>}
            <Button type="submit" disabled={submitting} icon={Send}>{submitting ? "Sending…" : "Submit feedback"}</Button>
          </form>
        </Panel>
        <div className="feedback-aside">
          <div className="feedback-info"><span><ShieldCheck size={18} /></span><h2>What happens next?</h2><p>Your feedback is visible to the transport administrators, who can review it and update its status.</p></div>
          <div className="feedback-info feedback-info--subtle"><span><Clock3 size={18} /></span><h2>Service updates</h2><p>Reported feedback is not a live incident feed. For current status, check the shuttle information page.</p><Link to="/student/shuttles">View shuttle status <ArrowRight size={14} /></Link></div>
        </div>
      </div>
    </div>
  );
}

export function MyFeedback() {
  const feedback = useApi(() => feedbackApi.mine({ limit: 100 }), []);
  return (
    <div className="page-content">
      <PageHeader eyebrow="YOUR SUBMISSIONS" title="My feedback" description="Review feedback you have submitted and its current review status." action={<Link className="button button--primary" to="/student/feedback"><MessageSquareText size={16} /> Send feedback</Link>} />
      {feedback.loading ? <Loading /> : feedback.error ? <ErrorState message={feedback.error} onRetry={feedback.refresh} /> : feedback.data?.items?.length ? (
        <div className="feedback-list">{feedback.data.items.map((item) => <article className="feedback-card" key={item.id}><div className="feedback-card__top"><span className="feedback-category">{feedbackCategories.find(([value]) => value === item.category)?.[1] || item.category}</span><StatusBadge status={item.status} /></div><p>{item.message}</p><div className="feedback-card__meta"><span>Submitted {formatDate(item.created_at)}</span>{item.rating && <span>{item.rating}/5 rating</span>}</div>{item.admin_response && <div className="admin-response"><strong>Transport team response</strong><p>{item.admin_response}</p></div>}</article>)}</div>
      ) : <EmptyState title="No feedback submitted" description="Feedback you send to the transport team will appear here." action={<Link className="button button--secondary" to="/student/feedback">Send feedback</Link>} />}
    </div>
  );
}

export function Profile() {
  const { user } = useAuth();
  return (
    <div className="page-content">
      <PageHeader eyebrow="ACCOUNT SETTINGS" title="My profile" description="Your student account information." />
      <Panel title="Profile details" subtitle="Managed through your university account">
        <div className="profile-details"><span className="profile-details__avatar"><UserRound size={23} /></span><div><span className="profile-details__label">Full name</span><strong>{user?.full_name}</strong></div><div><span className="profile-details__label">University email</span><strong>{user?.email}</strong></div><div><span className="profile-details__label">Account type</span><strong>Student</strong></div></div>
        <p className="subtle-copy">Profile details are read-only in this portal. Contact your university account administrator to change your account information.</p>
      </Panel>
    </div>
  );
}

const StudentPages = {
  Stops,
  StopDetails,
  Routes,
  RouteDetails,
  Shuttles,
  ShuttleDetails,
  Announcements,
  Feedback,
  MyFeedback,
  Profile,
};

export default StudentPages;
