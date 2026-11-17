import {
  ArrowRight,
  ArrowDown,
  ArrowUp,
  Bell,
  BusFront,
  Check,
  ClipboardList,
  Clock3,
  MapPin,
  MessageSquareText,
  Minus,
  Plus,
  Route as RouteIcon,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import {
  Button,
  EmptyState,
  ErrorState,
  FormField,
  Loading,
  Modal,
  PageHeader,
  Panel,
  Pagination,
  SearchField,
  StatusBadge,
  StatCard,
  formatDate,
} from "../components/ui.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getApiError, useApi } from "../hooks/useApi.js";
import { announcementsApi } from "../services/announcements.js";
import { feedbackApi } from "../services/feedback.js";
import { routesApi } from "../services/routes.js";
import { shuttleStatusApi } from "../services/shuttleStatus.js";
import { shuttlesApi } from "../services/shuttles.js";
import { stopsApi } from "../services/stops.js";

const feedbackCategories = [
  ["DELAY", "Delay"],
  ["OVERCROWDING", "Overcrowding"],
  ["INCORRECT_STOP", "Incorrect stop"],
  ["SUGGESTION", "Suggestion"],
  ["OTHER", "Other"],
];
const feedbackStatuses = [
  ["PENDING", "Pending"],
  ["IN_REVIEW", "In review"],
  ["RESOLVED", "Resolved"],
  ["DISMISSED", "Dismissed"],
];

function AdminDashboard() {
  const loadSummary = useMemo(() => async () => {
    const [stops, routes, shuttles, pending, status, announcements, recentFeedback] = await Promise.all([
      stopsApi.list({ limit: 1 }),
      routesApi.list({ limit: 1 }),
      shuttlesApi.list({ limit: 1 }),
      feedbackApi.list({ status: "PENDING", limit: 1 }),
      shuttleStatusApi.list({ limit: 5 }),
      announcementsApi.list({ limit: 3 }),
      feedbackApi.list({ limit: 4 }),
    ]);
    return {
      data: {
        stops: stops.data.total,
        routes: routes.data.total,
        shuttles: shuttles.data.total,
        pending: pending.data.total,
        status: status.data.items,
        announcements: announcements.data.items,
        feedback: recentFeedback.data.items,
      },
    };
  }, []);
  const summary = useApi(loadSummary, [loadSummary]);

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="TRANSPORT ADMINISTRATION"
        title="Operations overview"
        description="A clear view of the records and service updates maintained by your transport team."
        action={<Link className="button button--primary" to="/admin/status"><Plus size={16} /> Update service status</Link>}
      />
      {summary.loading ? <Loading /> : summary.error ? <ErrorState message={summary.error} onRetry={summary.refresh} /> : (
        <>
          <div className="stat-grid">
            <StatCard label="Total stops" value={summary.data.stops} detail="Campus locations" icon={MapPin} />
            <StatCard label="Total routes" value={summary.data.routes} detail="Route records" icon={RouteIcon} tone="blue" />
            <StatCard label="Total shuttles" value={summary.data.shuttles} detail="Registered vehicles" icon={BusFront} tone="amber" />
            <StatCard label="Pending feedback" value={summary.data.pending} detail="Awaiting review" icon={MessageSquareText} tone="red" />
          </div>
          <div className="admin-dashboard-grid">
            <Panel title="Current service status" subtitle="Latest recorded update for each vehicle" action={<Link className="panel-link" to="/admin/status">Manage status <ArrowRight size={14} /></Link>}>
              {summary.data.status.length ? <div className="status-list">{summary.data.status.map((item) => <div key={item.shuttle.id} className="status-row"><span className="status-row__icon"><BusFront size={17} /></span><span className="status-row__name"><strong>{item.shuttle.vehicle_code}</strong><small>{item.shuttle.route_id ? "Assigned to a route" : "No route assigned"}</small></span><span className="status-row__updated"><StatusBadge status={item.status} /><small>{item.last_updated_at ? formatDate(item.last_updated_at) : "No updates recorded"}</small></span></div>)}</div> : <EmptyState title="No service updates" description="Manually recorded shuttle updates will appear here." /> }
            </Panel>
            <Panel title="Management shortcuts" subtitle="Keep campus transport information current">
              <div className="shortcut-list">
                <Link to="/admin/stops"><span><MapPin size={17} /></span><strong>Manage stops</strong><ArrowRight size={15} /></Link>
                <Link to="/admin/routes"><span><RouteIcon size={17} /></span><strong>Manage routes</strong><ArrowRight size={15} /></Link>
                <Link to="/admin/shuttles"><span><BusFront size={17} /></span><strong>Manage shuttles</strong><ArrowRight size={15} /></Link>
                <Link to="/admin/announcements"><span><Bell size={17} /></span><strong>Publish an announcement</strong><ArrowRight size={15} /></Link>
                <Link to="/admin/feedback"><span><ClipboardList size={17} /></span><strong>Review student feedback</strong><ArrowRight size={15} /></Link>
              </div>
            </Panel>
            <Panel title="Recent announcements" subtitle="Latest transport communications" action={<Link className="panel-link" to="/admin/announcements">Manage announcements <ArrowRight size={14} /></Link>}>
              {summary.data.announcements.length ? <div className="announcement-mini-list">{summary.data.announcements.map((item) => <article key={item.id} className="announcement-mini"><span className="announcement-mini__date">{formatDate(item.starts_at || item.created_at, { timeStyle: undefined })} · {item.is_published ? "Published" : "Draft"}</span><h3>{item.title}</h3><p>{item.body}</p></article>)}</div> : <EmptyState title="No announcements yet" description="Announcements created by the transport team will appear here." />}
            </Panel>
            <Panel title="Recent feedback" subtitle={`${summary.data.pending} pending review`} action={<Link className="panel-link" to="/admin/feedback">Review feedback <ArrowRight size={14} /></Link>}>
              {summary.data.feedback.length ? <div className="status-list">{summary.data.feedback.map((item) => <Link key={item.id} to="/admin/feedback" className="status-row"><span className="status-row__icon"><MessageSquareText size={17} /></span><span className="status-row__name"><strong>{feedbackCategories.find(([category]) => category === item.category)?.[1] || item.category} · {formatDate(item.created_at)}</strong><small>{item.message}</small></span><span className="status-row__updated"><StatusBadge status={item.status} /></span></Link>)}</div> : <EmptyState title="No feedback submitted" description="Student feedback will appear here when received." />}
            </Panel>
          </div>
          <div className="admin-data-note"><ShieldCheck size={16} /> Dashboard totals are loaded from the current API records. No sample operational data is shown.</div>
        </>
      )}
    </div>
  );
}

function dateToInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function makeInitialValues(fields, item) {
  return Object.fromEntries(fields.map((field) => {
    let value = item?.[field.name];
    if (field.name === "stop_ids" && item) {
      value = item.route_stops?.map((row) => row.stop_id) || [];
    }
    if (field.type === "datetime-local") value = dateToInput(value);
    if (field.type === "checkbox") value = item ? Boolean(value) : Boolean(field.default);
    if (field.type === "multi-select" || field.type === "ordered-select") value = value || [];
    if (field.type === "ordered-select") value = item ? value : [];
    if (!item && value == null && field.default !== undefined) value = field.default;
    if (field.type === "select" && field.nullable && value == null) value = "";
    if (value == null && field.type !== "checkbox" && field.type !== "multi-select") value = "";
    return [field.name, value];
  }));
}

function serializeValues(fields, values) {
  return Object.fromEntries(fields.map((field) => {
    let value = values[field.name];
    if (field.type === "number") value = value === "" ? (field.nullable ? null : undefined) : Number(value);
    if (field.type === "select" && field.nullable && value === "") value = null;
    if (field.type === "datetime-local") value = value ? new Date(value).toISOString() : null;
    if (field.type === "text" && typeof value === "string") value = value.trim();
    return [field.name, value];
  }).filter(([, value]) => value !== undefined));
}

function EntityDialog({ title, fields, item, onClose, onSubmit, submitting }) {
  const [values, setValues] = useState(() => makeInitialValues(fields, item));
  const originalStopIds = useRef(item?.route_stops?.map((row) => row.stop_id) || []);
  const [error, setError] = useState("");

  function change(event, field) {
    const value = field.type === "multi-select"
      ? Array.from(event.target.selectedOptions, (option) => option.value)
      : field.type === "checkbox"
        ? event.target.checked
        : event.target.value;
    setValues((current) => ({ ...current, [field.name]: value }));
  }

  function updateOrder(field, index, offset) {
    setValues((current) => {
      const ordered = [...current[field.name]];
      const target = index + offset;
      if (target < 0 || target >= ordered.length) return current;
      [ordered[index], ordered[target]] = [ordered[target], ordered[index]];
      return { ...current, [field.name]: ordered };
    });
  }

  function addOrderedOption(field) {
    const pendingKey = `${field.name}_pending`;
    const pending = values[pendingKey];
    if (!pending || values[field.name].includes(pending)) return;
    setValues((current) => ({
      ...current,
      [field.name]: [...current[field.name], pending],
      [pendingKey]: "",
    }));
  }

  function removeOrderedOption(field, value) {
    setValues((current) => ({
      ...current,
      [field.name]: current[field.name].filter((item) => item !== value),
    }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const payload = serializeValues(fields, values);
      if (item && payload.stop_ids) {
        const sameOrder = payload.stop_ids.length === originalStopIds.current.length
          && payload.stop_ids.every((stopId, index) => stopId === originalStopIds.current[index]);
        if (sameOrder) delete payload.stop_ids;
      }
      await onSubmit(payload);
    } catch (requestError) {
      setError(getApiError(requestError, "The changes could not be saved."));
    }
  }

  return (
    <Modal title={title} onClose={onClose} wide>
      <form className="portal-form modal__form" onSubmit={submit}>
        <div className="modal__fields">
          {fields.map((field) => {
            if (field.type === "checkbox") {
              return <label className="checkbox-field" key={field.name}><input type="checkbox" checked={Boolean(values[field.name])} onChange={(event) => change(event, field)} /><span><strong>{field.label}</strong>{field.hint && <small>{field.hint}</small>}</span></label>;
            }
            if (field.type === "select" || field.type === "multi-select") {
              return <label className="form-field" key={field.name}><span>{field.label}{field.required && <i> *</i>}</span><select name={field.name} value={field.type === "multi-select" ? (values[field.name] || []) : values[field.name]} onChange={(event) => change(event, field)} multiple={field.type === "multi-select"} required={field.required}>{field.nullable && <option value="">Not assigned</option>}{field.type !== "multi-select" && field.placeholder && <option value="" disabled>{field.placeholder}</option>}{field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select>{field.type === "multi-select" && field.hint && <small className="field-hint">{field.hint}</small>}</label>;
            }
            if (field.type === "ordered-select") {
              const pendingKey = `${field.name}_pending`;
              const optionMap = new Map(field.options.map((option) => [option.value, option.label]));
              return <div className="form-field ordered-stops" key={field.name}>
                <span>{field.label}</span>
                <div className="ordered-stops__add">
                  <select value={values[pendingKey] || ""} onChange={(event) => setValues((current) => ({ ...current, [pendingKey]: event.target.value }))}>
                    <option value="">Choose a stop to add</option>
                    {field.options.filter((option) => !values[field.name].includes(option.value)).map((option) => <option key={option.value} value={option.value} disabled={option.disabled}>{option.label}</option>)}
                  </select>
                  <Button type="button" variant="secondary" onClick={() => addOrderedOption(field)}>Add stop</Button>
                </div>
                {values[field.name].length ? <ol className="ordered-stops__list">{values[field.name].map((value, index) => <li key={value}><span className="ordered-stops__position">{index + 1}</span><strong>{optionMap.get(value) || "Inactive or unavailable stop"}</strong><span className="ordered-stops__actions"><button type="button" aria-label={`Move ${optionMap.get(value)} up`} disabled={index === 0} onClick={() => updateOrder(field, index, -1)}><ArrowUp size={14} /></button><button type="button" aria-label={`Move ${optionMap.get(value)} down`} disabled={index === values[field.name].length - 1} onClick={() => updateOrder(field, index, 1)}><ArrowDown size={14} /></button><button type="button" aria-label={`Remove ${optionMap.get(value)}`} onClick={() => removeOrderedOption(field, value)}><Minus size={14} /></button></span></li>)}</ol> : <small className="field-hint">No stops are in this route yet.</small>}
                {field.hint && <small className="field-hint">{field.hint}</small>}
              </div>;
            }
            return <FormField key={field.name} as={field.type === "textarea" ? "textarea" : undefined} name={field.name} label={field.label} hint={field.hint} type={field.type} required={field.required} maxLength={field.maxLength} min={field.min} max={field.max} step={field.step} rows={field.rows} value={values[field.name]} onChange={(event) => change(event, field)} />;
          })}
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="modal__actions"><Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>Cancel</Button><Button type="submit" disabled={submitting}>{submitting ? "Saving…" : item ? "Save changes" : "Create record"}</Button></div>
      </form>
    </Modal>
  );
}

function ManagementPage({
  title,
  eyebrow,
  description,
  noun,
  service,
  fields,
  columns,
  onRemove,
  activeField,
  pageSize = 25,
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [dialogItem, setDialogItem] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const queryValue = query.trim();
  const listing = useApi(
    () => service.list({ skip: (page - 1) * pageSize, limit: pageSize, ...(queryValue ? { q: queryValue } : {}) }),
    [service, page, pageSize, queryValue],
  );

  function openCreate() {
    setDialogItem(null);
    setDialogOpen(true);
    setActionError("");
  }

  function openEdit(item) {
    setDialogItem(item);
    setDialogOpen(true);
    setActionError("");
  }

  async function save(values) {
    setBusy(true);
    try {
      if (dialogItem) await service.update(dialogItem.id, values);
      else await service.create(values);
      setDialogOpen(false);
      setNotice(`${noun} ${dialogItem ? "updated" : "created"} successfully.`);
      await listing.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function deactivate(item) {
    setBusy(true);
    setActionError("");
    try {
      if (onRemove) await onRemove(item);
      else await service.update(item.id, { [activeField]: !item[activeField] });
      setDeleteItem(null);
      setNotice(onRemove ? `${noun} deleted successfully.` : `${noun} ${item[activeField] === false ? "activated" : "deactivated"} successfully.`);
      await listing.refresh();
    } catch (requestError) {
      setActionError(getApiError(requestError, `The ${noun.toLowerCase()} could not be updated.`));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page-content">
      <PageHeader eyebrow={eyebrow} title={title} description={description} action={<Button icon={Plus} onClick={openCreate}>Add {noun.toLowerCase()}</Button>} />
      <Panel className="table-panel">
        <div className="table-toolbar">
          <SearchField value={query} onChange={(value) => { setQuery(value); setPage(1); }} placeholder={`Search ${noun.toLowerCase()}s`} />
          <span>{listing.data?.total ?? "—"} records</span>
        </div>
        {notice && <div className="form-success table-notice" role="status"><Check size={16} />{notice}<button type="button" onClick={() => setNotice("")}>Dismiss</button></div>}
        {actionError && <ErrorState message={actionError} />}
        {listing.loading ? <Loading /> : listing.error ? <ErrorState message={listing.error} onRetry={listing.refresh} /> : listing.data.items.length ? (
          <>
            <div className="table-scroll"><table className="data-table"><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}<th className="table-actions-heading">Actions</th></tr></thead><tbody>
              {listing.data.items.map((item) => <tr key={item.id}>
                {columns.map((column) => <td key={column.key}>{column.render ? column.render(item) : item[column.key] ?? "—"}</td>)}
                <td><div className="row-actions"><button type="button" onClick={() => openEdit(item)}>Edit</button>{activeField && <button type="button" className={item[activeField] ? "row-action--danger" : ""} onClick={() => setDeleteItem(item)}>{item[activeField] ? "Deactivate" : "Activate"}</button>}{onRemove && <button type="button" className="row-action--danger" onClick={() => setDeleteItem(item)}>Delete</button>}</div></td>
              </tr>)}
            </tbody></table></div>
            <Pagination page={page} limit={pageSize} total={listing.data.total} onPageChange={setPage} />
          </>
        ) : <EmptyState title={`No ${noun.toLowerCase()}s found`} description={query ? "Try another search." : `Create a ${noun.toLowerCase()} to get started.`} action={<Button icon={Plus} onClick={openCreate}>Add {noun.toLowerCase()}</Button>} />}
      </Panel>
      {dialogOpen && <EntityDialog title={`${dialogItem ? "Edit" : "Add"} ${noun.toLowerCase()}`} fields={dialogItem ? fields : fields.filter((field) => field.name !== "is_active")} item={dialogItem} onClose={() => setDialogOpen(false)} onSubmit={save} submitting={busy} />}
      {deleteItem && <ConfirmDialog title={`${deleteItem[activeField] === false ? "Activate" : activeField ? "Deactivate" : "Delete"} ${noun.toLowerCase()}?`} description={activeField ? `This changes the ${noun.toLowerCase()} availability. Existing history is preserved.` : `This permanently deletes this ${noun.toLowerCase()} record.`} confirmLabel={deleteItem[activeField] === false ? "Activate" : activeField ? "Deactivate" : "Delete"} onCancel={() => setDeleteItem(null)} onConfirm={() => deactivate(deleteItem)} busy={busy} destructive={Boolean(activeField && deleteItem[activeField]) || Boolean(onRemove)} />}
    </div>
  );
}

const stopFields = [
  { name: "name", label: "Stop name", type: "text", required: true, maxLength: 120 },
  { name: "description", label: "Description", type: "textarea", rows: 3, hint: "Optional details to help students find the stop." },
  { name: "is_active", label: "Active stop", type: "checkbox", default: true, hint: "Inactive stops are hidden from students." },
];
const routeFields = (stops) => [
  { name: "code", label: "Route code", type: "text", required: true, maxLength: 32, hint: "Letters, numbers, underscores, and hyphens." },
  { name: "name", label: "Route name", type: "text", required: true, maxLength: 120 },
  { name: "estimated_duration_minutes", label: "Estimated duration (minutes)", type: "number", min: 1, nullable: true, hint: "Optional; do not enter an unverified estimate." },
  { name: "stop_ids", label: "Ordered route stops", type: "ordered-select", options: stops.map((stop) => ({ value: stop.id, label: stop.name })), hint: "Use the arrow controls to set the published stop order." },
  { name: "is_active", label: "Active route", type: "checkbox", default: true, hint: "Inactive routes are hidden from students." },
];
const shuttleFields = (routes) => [
  { name: "vehicle_code", label: "Vehicle code", type: "text", required: true, maxLength: 32 },
  { name: "capacity", label: "Passenger capacity", type: "number", min: 1, required: true },
  { name: "route_id", label: "Assigned route", type: "select", nullable: true, options: routes.map((route) => ({ value: route.id, label: `${route.code} · ${route.name}` })) },
  { name: "is_active", label: "Active shuttle", type: "checkbox", default: true, hint: "Inactive shuttles are hidden from student lists." },
];
const announcementFields = [
  { name: "title", label: "Announcement title", type: "text", required: true, maxLength: 160 },
  { name: "body", label: "Description", type: "textarea", rows: 5, required: true, hint: "Include clear, relevant service information." },
  { name: "starts_at", label: "Publication date", type: "datetime-local", hint: "Optional. Set a date/time to schedule the announcement." },
  { name: "ends_at", label: "End date", type: "datetime-local", hint: "Optional. Must be later than the publication date." },
  { name: "is_published", label: "Published", type: "checkbox", hint: "Unpublished announcements are visible to admins only." },
];

export function Stops() {
  return <ManagementPage title="Stop management" eyebrow="CAMPUS DIRECTORY" description="Create and maintain the stops students can browse." noun="Stop" service={stopsApi} fields={stopFields} columns={[
    { key: "name", label: "Stop name" },
    { key: "description", label: "Description", render: (item) => item.description || "—" },
    { key: "is_active", label: "Status", render: (item) => <span className={`table-state ${item.is_active ? "table-state--active" : ""}`}>{item.is_active ? "Active" : "Inactive"}</span> },
  ]} activeField="is_active" />;
}

export function Routes() {
  const stopOptions = useApi(() => stopsApi.list({ limit: 100, is_active: true }), []);
  const stops = stopOptions.data?.items || [];
  return <ManagementPage title="Route management" eyebrow="CAMPUS NETWORK" description="Create routes, maintain stop ordering, and configure journey duration only when verified." noun="Route" service={routesApi} fields={routeFields(stops)} columns={[
    { key: "code", label: "Route code", render: (item) => <span className="route-code">{item.code}</span> },
    { key: "name", label: "Route name" },
    { key: "route_stops", label: "Stops", render: (item) => item.route_stops?.length ?? 0 },
    { key: "estimated_duration_minutes", label: "Est. duration", render: (item) => item.estimated_duration_minutes ? `${item.estimated_duration_minutes} min` : "Not configured" },
    { key: "is_active", label: "Status", render: (item) => <span className={`table-state ${item.is_active ? "table-state--active" : ""}`}>{item.is_active ? "Active" : "Inactive"}</span> },
  ]} activeField="is_active" />;
}

export function Shuttles() {
  const routeOptions = useApi(() => routesApi.list({ limit: 100, is_active: true }), []);
  const routes = routeOptions.data?.items || [];
  const routeNames = Object.fromEntries(routes.map((route) => [route.id, `${route.code} · ${route.name}`]));
  return <ManagementPage title="Shuttle management" eyebrow="VEHICLE REGISTER" description="Manage vehicle records and their active route assignments." noun="Shuttle" service={shuttlesApi} fields={shuttleFields(routes)} columns={[
    { key: "vehicle_code", label: "Vehicle code" },
    { key: "capacity", label: "Capacity" },
    { key: "route_id", label: "Assigned route", render: (item) => routeNames[item.route_id] || (item.route_id ? "Route not available" : "Unassigned") },
    { key: "is_active", label: "Status", render: (item) => <span className={`table-state ${item.is_active ? "table-state--active" : ""}`}>{item.is_active ? "Active" : "Inactive"}</span> },
  ]} activeField="is_active" />;
}

function StatusManagement() {
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState({ shuttle_id: "", status: "ON_TIME", message: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const shuttles = useApi(() => shuttlesApi.list({ limit: 100, is_active: true }), []);
  const statuses = useApi(() => shuttleStatusApi.list({ limit: 100 }), []);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      await shuttleStatusApi.create({
        shuttle_id: form.shuttle_id,
        status: form.status,
        ...(form.message.trim() ? { message: form.message.trim() } : {}),
      });
      setSuccess("Manual service update recorded.");
      setFormOpen(false);
      setForm({ shuttle_id: "", status: "ON_TIME", message: "" });
      await statuses.refresh();
    } catch (requestError) {
      setError(getApiError(requestError, "The status update could not be saved."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-content">
      <PageHeader eyebrow="MANUAL SERVICE REPORTING" title="Shuttle status" description="Record an administrator-reported service update. This is not a live GPS feed or arrival prediction." action={<Button icon={Plus} onClick={() => { setError(""); setFormOpen(true); }}>Record update</Button>} />
      {success && <div className="form-success page-notice" role="status"><Check size={16} />{success}</div>}
      <Panel title="Current shuttle service" subtitle="Latest update for each vehicle" className="table-panel">
        {statuses.loading ? <Loading /> : statuses.error ? <ErrorState message={statuses.error} onRetry={statuses.refresh} /> : statuses.data?.items?.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Vehicle</th><th>Status</th><th>Administrator message</th><th>Last updated</th></tr></thead><tbody>{statuses.data.items.map((item) => <tr key={item.shuttle.id}><td><strong>{item.shuttle.vehicle_code}</strong><small className="table-subtext">{item.shuttle.is_active ? "Active vehicle" : "Inactive vehicle"}</small></td><td><StatusBadge status={item.status} /></td><td>{item.message || "—"}</td><td>{formatDate(item.last_updated_at)}</td></tr>)}</tbody></table></div> : <EmptyState title="No shuttle records" description="Create an active shuttle before recording a service status." />}
      </Panel>
      <div className="admin-data-note"><Clock3 size={16} /> Each submission is stored as a timestamped history record; the newest recorded update is displayed.</div>
      {formOpen && <Modal title="Record shuttle status" onClose={() => setFormOpen(false)}><form className="portal-form modal__form" onSubmit={submit}>
        {shuttles.loading ? <Loading /> : shuttles.error ? <ErrorState message={shuttles.error} onRetry={shuttles.refresh} /> : <label className="form-field"><span>Shuttle <i>*</i></span><select required value={form.shuttle_id} onChange={(event) => setForm((current) => ({ ...current, shuttle_id: event.target.value }))}><option value="">Choose an active shuttle</option>{shuttles.data.items.map((shuttle) => <option key={shuttle.id} value={shuttle.id}>{shuttle.vehicle_code}</option>)}</select>{!shuttles.data.items.length && <small className="field-hint">No active shuttles are available.</small>}</label>}
        <label className="form-field"><span>Service status <i>*</i></span><select value={form.status} onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}>{[["ON_TIME", "On time"], ["DELAYED", "Delayed"], ["UNAVAILABLE", "Out of service"], ["NOT_UPDATED", "Not updated"]].map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <FormField as="textarea" name="message" label="Administrator message" hint="Optional. Do not enter an estimated arrival unless it is from a verified source." rows={3} maxLength={2000} value={form.message} onChange={(event) => setForm((current) => ({ ...current, message: event.target.value }))} />
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="modal__actions"><Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button><Button type="submit" disabled={submitting || shuttles.loading || !shuttles.data?.items?.length}>{submitting ? "Recording…" : "Record update"}</Button></div>
      </form></Modal>}
    </div>
  );
}

export function Announcements() {
  return <ManagementPage title="Announcements" eyebrow="SERVICE COMMUNICATIONS" description="Publish, schedule, and maintain campus shuttle information." noun="Announcement" service={announcementsApi} fields={announcementFields} columns={[
    { key: "title", label: "Title" },
    { key: "starts_at", label: "Publication date", render: (item) => formatDate(item.starts_at || item.created_at) },
    { key: "is_published", label: "Visibility", render: (item) => <span className={`table-state ${item.is_published ? "table-state--active" : ""}`}>{item.is_published ? "Published" : "Draft"}</span> },
  ]} onRemove={(item) => announcementsApi.remove(item.id)} />;
}

function FeedbackManagement() {
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [reviewItem, setReviewItem] = useState(null);
  const [reviewStatus, setReviewStatus] = useState("IN_REVIEW");
  const [response, setResponse] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const params = useMemo(() => ({
    skip: (page - 1) * 50,
    limit: 50,
    ...(status ? { status } : {}),
    ...(category ? { category } : {}),
  }), [status, category, page]);
  const feedback = useApi(() => feedbackApi.list(params), [params]);

  function openReview(item) {
    setReviewItem(item);
    setReviewStatus(item.status === "PENDING" ? "IN_REVIEW" : item.status);
    setResponse(item.admin_response || "");
    setError("");
  }

  async function submitReview(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await feedbackApi.updateStatus(reviewItem.id, {
        status: reviewStatus,
        ...(response !== "" ? { admin_response: response } : {}),
      });
      setReviewItem(null);
      await feedback.refresh();
    } catch (requestError) {
      setError(getApiError(requestError, "Feedback could not be updated."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-content">
      <PageHeader eyebrow="STUDENT REPORTS" title="Feedback review" description="Review submissions from students and share a status or response." />
      <Panel className="table-panel">
        <div className="table-toolbar table-toolbar--filters">
          <select aria-label="Filter by status" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">All statuses</option>{feedbackStatuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
          <select aria-label="Filter by category" value={category} onChange={(event) => { setCategory(event.target.value); setPage(1); }}><option value="">All categories</option>{feedbackCategories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
          <span>{feedback.data?.total ?? "—"} submissions</span>
        </div>
        {feedback.loading ? <Loading /> : feedback.error ? <ErrorState message={feedback.error} onRetry={feedback.refresh} /> : feedback.data?.items?.length ? <><div className="table-scroll"><table className="data-table"><thead><tr><th>Category</th><th>Report</th><th>Rating</th><th>Status</th><th>Submitted</th><th>Action</th></tr></thead><tbody>{feedback.data.items.map((item) => <tr key={item.id}><td>{feedbackCategories.find(([value]) => value === item.category)?.[1] || item.category}</td><td className="feedback-message-cell">{item.message}</td><td>{item.rating ? `${item.rating}/5` : "—"}</td><td><StatusBadge status={item.status} /></td><td>{formatDate(item.created_at)}</td><td><button className="row-actions__single" onClick={() => openReview(item)}>Review</button></td></tr>)}</tbody></table></div><Pagination page={page} limit={50} total={feedback.data.total} onPageChange={setPage} /></> : <EmptyState title="No matching feedback" description="New student submissions will appear here." />}
      </Panel>
      {reviewItem && <Modal title="Review student feedback" onClose={() => setReviewItem(null)}><form className="portal-form modal__form" onSubmit={submitReview}>
        <div className="review-summary"><span>{feedbackCategories.find(([value]) => value === reviewItem.category)?.[1] || reviewItem.category}</span><StatusBadge status={reviewItem.status} /><p>{reviewItem.message}</p><small>Submitted {formatDate(reviewItem.created_at)}{reviewItem.rating ? ` · Rating ${reviewItem.rating}/5` : ""}</small></div>
        <label className="form-field"><span>Review status <i>*</i></span><select value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)}>{feedbackStatuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <FormField as="textarea" name="admin_response" label="Response to student" hint="Optional. Leave unchanged to preserve the existing response." rows={4} maxLength={5000} value={response} onChange={(event) => setResponse(event.target.value)} />
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="modal__actions"><Button type="button" variant="secondary" onClick={() => setReviewItem(null)}>Cancel</Button><Button type="submit" disabled={submitting}>{submitting ? "Saving…" : "Save review"}</Button></div>
      </form></Modal>}
    </div>
  );
}

export function Profile() {
  const { user } = useAuth();
  return (
    <div className="page-content">
      <PageHeader eyebrow="ADMINISTRATOR ACCOUNT" title="Profile" description="Your transport administration account details." />
      <Panel title="Account information" subtitle="Administrator accounts are provisioned by a trusted backend operator">
        <div className="profile-details"><span className="profile-details__avatar"><ShieldCheck size={23} /></span><div><span className="profile-details__label">Full name</span><strong>{user?.full_name}</strong></div><div><span className="profile-details__label">Email</span><strong>{user?.email}</strong></div><div><span className="profile-details__label">Role</span><strong>Administrator</strong></div></div>
        <p className="subtle-copy">Administrator permissions are verified by the backend on each management request. Contact the account operator for profile or access changes.</p>
      </Panel>
    </div>
  );
}

export const Dashboard = AdminDashboard;
export const Status = StatusManagement;
export const Feedback = FeedbackManagement;
