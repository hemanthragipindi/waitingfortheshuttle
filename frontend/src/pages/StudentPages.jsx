import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bell,
  BusFront,
  CalendarDays,
  Check,
  CheckCircle2,
  Clock3,
  Compass,
  ExternalLink,
  Info,
  MapPin,
  MessageSquareText,
  Route as RouteIcon,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
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
  labelFor,
  serviceAreas,
  serviceStatuses,
  serviceTypes,
} from "../constants/transport.js";
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
  StatCard,
  formatDate,
  formatRelativeTime,
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
        <span>{labelFor(serviceAreas, route.service_area)}</span>
        <span>{route.service_types?.map((type) => labelFor(serviceTypes, type)).join(", ") || "Service type pending"}</span>
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
        <p>{labelFor(serviceAreas, stop.service_area)} · {stop.description || "Transport stop"}</p>
        <span className="stop-card__meta">{related === undefined ? "View stop details and routes" : `${related} ${related === 1 ? "route" : "routes"}`}</span>
      </div>
      <ArrowRight size={17} className="stop-card__arrow" />
    </Link>
  );
}

export function Overview() {
  const { user } = useAuth();
  const routesReq = useApi(() => routesApi.list({ limit: 100 }), []);
  const stopsReq = useApi(() => stopsApi.list({ limit: 100 }), []);
  const statusesReq = useApi(() => shuttleStatusApi.list({ limit: 100 }), []);
  const announcementsReq = useApi(() => announcementsApi.list({ limit: 10 }), []);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedRouteId, setSelectedRouteId] = useState(null);

  const anyError = routesReq.error || stopsReq.error || statusesReq.error || announcementsReq.error;
  const anyLoading = routesReq.loading || stopsReq.loading || statusesReq.loading || announcementsReq.loading;

  const routes = useMemo(() => routesReq.data?.items || [], [routesReq.data]);
  const stops = useMemo(() => stopsReq.data?.items || [], [stopsReq.data]);
  const statusItems = useMemo(() => statusesReq.data?.items || [], [statusesReq.data]);
  const announcements = useMemo(() => announcementsReq.data?.items || [], [announcementsReq.data]);

  // Lookup maps
  const routeMap = useMemo(() => new Map(routes.map((r) => [r.id, r])), [routes]);
  const stopMap = useMemo(() => new Map(stops.map((s) => [s.id, s])), [stops]);

  // Active route for Route Explorer
  const activeRouteId = selectedRouteId || routes[0]?.id;
  const selectedRoute = useMemo(
    () => routes.find((r) => r.id === activeRouteId) || routes[0] || null,
    [routes, activeRouteId]
  );

  // Process shuttle status with real API data and stale check (>2 hours)
  const processedStatuses = useMemo(() => {
    return statusItems.map((item) => {
      const route = routeMap.get(item.shuttle.route_id);
      let effectiveStatus = item.status;
      let isStale = false;

      if (!item.last_updated_at || item.status === "NOT_UPDATED") {
        effectiveStatus = "STATUS_UNAVAILABLE";
      } else {
        const ageMs = Date.now() - new Date(item.last_updated_at).getTime();
        const ageMinutes = Math.floor(ageMs / 60000);
        if (ageMinutes > 120) {
          isStale = true;
          effectiveStatus = "STALE";
        }
      }

      const firstStop = route?.route_stops?.[0]?.stop?.name;
      const lastStop = route?.route_stops?.at(-1)?.stop?.name;
      const reportedStop = firstStop ? `${firstStop}` : "Campus Corridor";

      return {
        ...item,
        effectiveStatus,
        isStale,
        route,
        reportedStop,
        routeName: route ? `${route.code} · ${route.name}` : "Unassigned / Standby",
        firstStop,
        lastStop,
      };
    });
  }, [statusItems, routeMap]);

  // Filter counts
  const counts = useMemo(() => {
    return {
      ALL: processedStatuses.length,
      AVAILABLE: processedStatuses.filter((s) => s.effectiveStatus === "ON_TIME" || s.effectiveStatus === "AVAILABLE").length,
      DELAYED: processedStatuses.filter((s) => s.effectiveStatus === "DELAYED").length,
      UNAVAILABLE: processedStatuses.filter((s) => s.effectiveStatus === "UNAVAILABLE" || s.effectiveStatus === "NOT_OPERATING" || s.effectiveStatus === "CANCELLED").length,
      STALE: processedStatuses.filter((s) => s.effectiveStatus === "STALE" || s.effectiveStatus === "STATUS_UNAVAILABLE").length,
    };
  }, [processedStatuses]);

  // Filtered statuses
  const filteredStatuses = useMemo(() => {
    if (statusFilter === "ALL") return processedStatuses;
    if (statusFilter === "AVAILABLE") return processedStatuses.filter((s) => s.effectiveStatus === "ON_TIME" || s.effectiveStatus === "AVAILABLE");
    if (statusFilter === "DELAYED") return processedStatuses.filter((s) => s.effectiveStatus === "DELAYED");
    if (statusFilter === "UNAVAILABLE") return processedStatuses.filter((s) => s.effectiveStatus === "UNAVAILABLE" || s.effectiveStatus === "NOT_OPERATING" || s.effectiveStatus === "CANCELLED");
    if (statusFilter === "STALE") return processedStatuses.filter((s) => s.effectiveStatus === "STALE" || s.effectiveStatus === "STATUS_UNAVAILABLE");
    return processedStatuses;
  }, [processedStatuses, statusFilter]);

  // Active verified shuttles count
  const activeShuttlesCount = useMemo(() => {
    return statusItems.filter((item) => item.shuttle?.is_active).length;
  }, [statusItems]);

  // Urgent notice if any
  const urgentNotice = useMemo(() => {
    return announcements.find((a) => {
      const text = `${a.title} ${a.body}`.toLowerCase();
      return text.includes("delay") || text.includes("service") || text.includes("interruption") || text.includes("divert") || text.includes("urgent");
    }) || null;
  }, [announcements]);

  // Shuttles assigned to the currently selected route
  const selectedRouteShuttles = useMemo(() => {
    if (!selectedRoute) return [];
    return processedStatuses.filter((s) => s.shuttle.route_id === selectedRoute.id);
  }, [selectedRoute, processedStatuses]);

  // Announcements relevant to selected route
  const selectedRouteAnnouncements = useMemo(() => {
    if (!selectedRoute) return [];
    const code = selectedRoute.code.toLowerCase();
    const name = selectedRoute.name.toLowerCase();
    return announcements.filter((a) => {
      const text = `${a.title} ${a.body}`.toLowerCase();
      return text.includes(code) || text.includes(name);
    });
  }, [selectedRoute, announcements]);

  const refreshAll = () => {
    routesReq.refresh();
    stopsReq.refresh();
    statusesReq.refresh();
    announcementsReq.refresh();
  };

  return (
    <div className="page-content">
      {/* Top Hero Heading */}
      <div className="dashboard-hero-header">
        <div>
          <span className="dashboard-kicker-badge">
            <Compass size={13} /> LOVELY PROFESSIONAL UNIVERSITY · CAMPUS & REGIONAL TRANSPORT
          </span>
          <h1>Good day, {user?.full_name?.split(" ")[0] || "Student"}</h1>
          <p className="page-heading__description">
            Verified university shuttle coordination across LPU Campus, Phagwara, and Jalandhar corridors.
          </p>
        </div>
        <div className="page-heading__action">
          <Button variant="secondary" onClick={refreshAll} icon={Clock3} disabled={anyLoading}>
            {anyLoading ? "Refreshing…" : "Refresh status"}
          </Button>
        </div>
      </div>

      {anyError && (
        <ErrorState message={anyError} onRetry={refreshAll} />
      )}

      {/* Urgent Service Alert Banner (if any) */}
      {urgentNotice && (
        <div className="dashboard-alert-banner" role="alert">
          <div className="dashboard-alert-banner__content">
            <span className="dashboard-alert-banner__icon">
              <AlertTriangle size={18} />
            </span>
            <div>
              <h4>Service Notice: {urgentNotice.title}</h4>
              <p>{urgentNotice.body}</p>
            </div>
          </div>
          <Link to="/student/announcements" className="button button--secondary" style={{ flexShrink: 0 }}>
            Read bulletins
          </Link>
        </div>
      )}

      {/* Section A: Transport Overview */}
      <div className="dashboard-section">
        <div className="stat-grid">
          <StatCard
            label="Available Routes"
            value={routesReq.loading ? "…" : (routesReq.data?.total ?? routes.length)}
            detail="Verified transit corridors"
            icon={RouteIcon}
            tone="blue"
          />
          <StatCard
            label="Registered Stops"
            value={stopsReq.loading ? "…" : (stopsReq.data?.total ?? stops.length)}
            detail="Boarding & arrival points"
            icon={MapPin}
            tone="green"
          />
          <StatCard
            label="Active Shuttles"
            value={statusesReq.loading ? "…" : activeShuttlesCount}
            detail="Vehicles in operation"
            icon={BusFront}
            tone="amber"
          />
          <StatCard
            label="Service Notices"
            value={announcementsReq.loading ? "…" : (announcementsReq.data?.total ?? announcements.length)}
            detail="Official announcements"
            icon={Bell}
            tone="red"
          />
        </div>
      </div>

      {/* Section B: Shuttle Status Cards */}
      <section className="dashboard-section">
        <div className="section-head-bar">
          <div>
            <h2>Live Shuttle Coordination Status</h2>
            <p>Verified status records maintained by university transport administration.</p>
          </div>
          <div className="filter-pill-group">
            <button
              type="button"
              className={`filter-pill ${statusFilter === "ALL" ? "is-active" : ""}`}
              onClick={() => setStatusFilter("ALL")}
            >
              All Shuttles <span className="filter-pill__count">{counts.ALL}</span>
            </button>
            <button
              type="button"
              className={`filter-pill ${statusFilter === "AVAILABLE" ? "is-active" : ""}`}
              onClick={() => setStatusFilter("AVAILABLE")}
            >
              On Time / Available <span className="filter-pill__count">{counts.AVAILABLE}</span>
            </button>
            <button
              type="button"
              className={`filter-pill ${statusFilter === "DELAYED" ? "is-active" : ""}`}
              onClick={() => setStatusFilter("DELAYED")}
            >
              Delayed <span className="filter-pill__count">{counts.DELAYED}</span>
            </button>
            <button
              type="button"
              className={`filter-pill ${statusFilter === "UNAVAILABLE" ? "is-active" : ""}`}
              onClick={() => setStatusFilter("UNAVAILABLE")}
            >
              Out of Service <span className="filter-pill__count">{counts.UNAVAILABLE}</span>
            </button>
            <button
              type="button"
              className={`filter-pill ${statusFilter === "STALE" ? "is-active" : ""}`}
              onClick={() => setStatusFilter("STALE")}
            >
              Stale / Unavailable <span className="filter-pill__count">{counts.STALE}</span>
            </button>
          </div>
        </div>

        {statusesReq.loading ? (
          <Loading label="Loading shuttle service status" />
        ) : filteredStatuses.length ? (
          <div className="student-status-grid">
            {filteredStatuses.map((item) => (
              <Link
                key={item.shuttle.id}
                to={`/student/shuttles/${item.shuttle.id}`}
                className="student-status-card"
              >
                <div className="student-status-card__header">
                  <div className="student-status-card__vehicle">
                    <span className="student-status-card__icon">
                      <BusFront size={18} />
                    </span>
                    <div>
                      <span className="student-status-card__vehicle-code">
                        {item.shuttle.vehicle_code}
                      </span>
                      <span className="student-status-card__operator">
                        {item.shuttle.is_university_operated
                          ? "University Operated"
                          : "External Public Transit"}
                        {item.shuttle.capacity ? ` · ${item.shuttle.capacity} seats` : ""}
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={item.effectiveStatus} />
                </div>

                <div className="student-status-card__body">
                  <div className="status-card-row">
                    <RouteIcon size={14} />
                    <span>
                      Route: <strong>{item.routeName}</strong>
                    </span>
                  </div>

                  <div className="status-card-row">
                    <MapPin size={14} />
                    <span>
                      Reported Stop: <strong>{item.reportedStop}</strong>
                    </span>
                  </div>

                  {item.message && (
                    <div className="status-card-message">
                      “{item.message}”
                    </div>
                  )}
                </div>

                <div className="student-status-card__footer">
                  <span className="admin-reported-pill">
                    <ShieldCheck size={12} /> Admin Reported
                  </span>
                  <span
                    className="status-timestamp"
                    title={item.last_updated_at ? formatDate(item.last_updated_at) : "No timestamp recorded"}
                  >
                    <Clock3 size={11} /> {formatRelativeTime(item.last_updated_at)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No shuttles match this filter"
            description="Select another status filter or check back once the transport administration posts an update."
          />
        )}
      </section>

      {/* Section C: Route Explorer */}
      <section className="dashboard-section">
        <div className="section-head-bar">
          <div>
            <h2>Campus & Regional Route Explorer</h2>
            <p>Select an active route to inspect ordered stop sequences, terminal points, and assigned shuttles.</p>
          </div>
          <Link to="/student/routes" className="panel-link">
            All routes directory <ArrowRight size={14} />
          </Link>
        </div>

        {routesReq.loading ? (
          <Loading label="Loading transport routes" />
        ) : routes.length ? (
          <div className="route-explorer-box">
            {/* Horizontal Route Tabs */}
            <div className="route-explorer-tabs">
              {routes.map((route) => (
                <button
                  type="button"
                  key={route.id}
                  className={`route-explorer-tab ${route.id === activeRouteId ? "is-active" : ""}`}
                  onClick={() => setSelectedRouteId(route.id)}
                >
                  <span className="route-code">{route.code}</span>
                  <span>{route.name}</span>
                </button>
              ))}
            </div>

            {selectedRoute && (
              <div className="route-explorer-detail">
                {/* Main Stop Timeline */}
                <div className="route-explorer-detail__main">
                  <div className="route-header-block">
                    <div>
                      <span className="eyebrow">ROUTE {selectedRoute.code} · {labelFor(serviceAreas, selectedRoute.service_area)}</span>
                      <h3>{selectedRoute.name}</h3>
                      <p>
                        {selectedRoute.service_types?.map((t) => labelFor(serviceTypes, t)).join(", ")}
                        {selectedRoute.estimated_duration_minutes ? ` · ~${selectedRoute.estimated_duration_minutes} min journey` : ""}
                      </p>
                    </div>
                    <Link
                      to={`/student/routes/${selectedRoute.id}`}
                      className="button button--secondary"
                      style={{ fontSize: "10px", padding: "0 10px", minHeight: "32px" }}
                    >
                      Route details <ArrowRight size={13} />
                    </Link>
                  </div>

                  {/* Terminal Origin -> Terminus Banner */}
                  <div className="route-terminal-banner">
                    <span>Origin: <strong>{selectedRoute.route_stops?.[0]?.stop?.name || "Starting Point"}</strong></span>
                    <span className="route-terminal-arrow">➔</span>
                    <span>Terminus: <strong>{selectedRoute.route_stops?.at(-1)?.stop?.name || "End Terminal"}</strong></span>
                  </div>

                  {/* Visual Stop Sequence Timeline */}
                  {selectedRoute.route_stops?.length ? (
                    <div className="route-timeline-horizontal">
                      {selectedRoute.route_stops.map((stopRow, index) => {
                        const isStart = index === 0;
                        const isEnd = index === selectedRoute.route_stops.length - 1;
                        return (
                          <div
                            key={stopRow.stop_id}
                            className={`route-timeline-stop ${isStart ? "is-start" : ""} ${isEnd ? "is-end" : ""}`}
                          >
                            <span className="route-timeline-stop__num">
                              {index + 1}
                            </span>
                            <div className="route-timeline-stop__content">
                              <div>
                                <Link to={`/student/stops/${stopRow.stop_id}`}>
                                  <strong>{stopRow.stop.name}</strong>
                                </Link>
                                {isStart && <span className="stop-badge-pill stop-badge-pill--start">Starting Terminal</span>}
                                {isEnd && selectedRoute.route_stops.length > 1 && <span className="stop-badge-pill stop-badge-pill--end">Final Stop</span>}
                              </div>
                              <small>{labelFor(serviceAreas, stopRow.stop.service_area)} · Boarding point</small>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <EmptyState
                      title="No stops configured"
                      description="Stops for this route will appear here once registered by the transport desk."
                    />
                  )}
                </div>

                {/* Right Side: Assigned Shuttles & Route Notices */}
                <div className="route-explorer-detail__side">
                  <div>
                    <h4 className="side-subpanel-title">
                      Assigned Shuttles ({selectedRouteShuttles.length})
                    </h4>
                    {selectedRouteShuttles.length ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                        {selectedRouteShuttles.map((s) => (
                          <Link
                            key={s.shuttle.id}
                            to={`/student/shuttles/${s.shuttle.id}`}
                            className="assigned-shuttle-chip"
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              <BusFront size={15} style={{ color: "var(--green-800)" }} />
                              <div>
                                <strong>{s.shuttle.vehicle_code}</strong>
                                <small style={{ display: "block", color: "#8a968e", fontSize: "8px" }}>
                                  {s.reportedStop}
                                </small>
                              </div>
                            </div>
                            <StatusBadge status={s.effectiveStatus} />
                          </Link>
                        ))}
                      </div>
                    ) : (
                      <p style={{ margin: 0, fontSize: "10px", color: "#8a968e" }}>
                        No shuttles currently assigned to this route.
                      </p>
                    )}
                  </div>

                  <div>
                    <h4 className="side-subpanel-title">Route Notices</h4>
                    {selectedRouteAnnouncements.length ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {selectedRouteAnnouncements.map((a) => (
                          <div key={a.id} style={{ fontSize: "10px", padding: "8px", background: "#fff", border: "1px solid #e7ebe8", borderRadius: "6px" }}>
                            <strong style={{ color: "#324337" }}>{a.title}</strong>
                            <p style={{ margin: "3px 0 0", color: "#77857c", fontSize: "9px" }}>{a.body}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p style={{ margin: 0, fontSize: "10px", color: "#8a968e" }}>
                        No specific delays or route notices recorded for this route.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState
            title="No active routes found"
            description="Active campus transit routes will appear here."
          />
        )}
      </section>

      {/* Section D: Latest Announcements */}
      <section className="dashboard-section">
        <div className="section-head-bar">
          <div>
            <h2>Service Announcements & Bulletins</h2>
            <p>Official transport notices regarding route deviations, schedules, and operations.</p>
          </div>
          <Link to="/student/announcements" className="panel-link">
            All announcements <ArrowRight size={14} />
          </Link>
        </div>

        {announcementsReq.loading ? (
          <Loading label="Loading transport bulletins" />
        ) : announcements.length ? (
          <div className="announcement-list">
            {announcements.slice(0, 4).map((item) => (
              <article key={item.id} className="announcement-card">
                <div className="announcement-card__date">
                  <CalendarDays size={14} />
                  <span>{formatDate(item.starts_at || item.created_at)}</span>
                  <span style={{ marginLeft: "auto", fontSize: "8px", fontWeight: "700", color: "var(--green-900)" }}>
                    OFFICIAL NOTICE
                  </span>
                </div>
                <h2>{item.title}</h2>
                <p>{item.body}</p>
                {item.ends_at && (
                  <span className="announcement-card__until">
                    Effective until {formatDate(item.ends_at)}
                  </span>
                )}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No announcements published"
            description="Service updates will appear here when posted by the transport team."
          />
        )}
      </section>

      {/* Section E: Secondary Student Feedback Banner */}
      <div className="secondary-feedback-box">
        <div className="secondary-feedback-box__content">
          <span className="secondary-feedback-box__icon">
            <MessageSquareText size={20} />
          </span>
          <div>
            <h4>Notice an unlisted delay or have transit feedback?</h4>
            <p>
              Your reports help transport coordinators correct stop listings and identify service issues.
            </p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
          <Link to="/student/my-feedback" className="button button--secondary">
            My Submissions
          </Link>
          <Link to="/student/feedback" className="button button--primary">
            Send Feedback
          </Link>
        </div>
      </div>

      {/* Information Integrity Disclaimer */}
      <div className="disclosure-note" style={{ marginTop: "22px" }}>
        <ShieldCheck size={16} />
        <span>
          <strong>Information Integrity:</strong> All shuttle updates are manually recorded by university administrators. The platform does not display automated GPS tracking, algorithmically estimated arrival countdowns, or synthetic crowd percentages.
        </span>
      </div>
    </div>
  );
}

export function Stops() {
  const [area, setArea] = useState("");
  const loadStops = useMemo(() => (params) => stopsApi.list({
    ...params,
    ...(area ? { service_area: area } : {}),
  }), [area]);
  const { data, loading, error, refresh, query, setQuery, page, setPage } = usePagedList(loadStops);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  return (
    <div className="page-content">
      <PageHeader eyebrow="EXPLORE CAMPUS" title="Campus stops" description="Find shuttle stops across campus and see where each one can take you." />
      <div className="toolbar"><SearchField value={query} onChange={setQuery} placeholder="Search stops" /><select aria-label="Filter by service area" value={area} onChange={(event) => { setArea(event.target.value); setPage(1); }}><option value="">All service areas</option>{serviceAreas.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></div>
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
  const [area, setArea] = useState("");
  const [destination, setDestination] = useState("");
  const [serviceType, setServiceType] = useState("");
  const [status, setStatus] = useState("");
  const loadRoutes = useMemo(() => (params) => routesApi.list({
    ...params,
    ...(area ? { service_area: area } : {}),
    ...(destination.trim() ? { destination: destination.trim() } : {}),
    ...(serviceType ? { service_type: serviceType } : {}),
    ...(status ? { status } : {}),
  }), [area, destination, serviceType, status]);
  const { data, loading, error, refresh, query, setQuery, page, setPage } = usePagedList(loadRoutes);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  return (
    <div className="page-content">
      <PageHeader eyebrow="PLAN YOUR JOURNEY" title="Shuttle routes" description="Review active routes, their ordered stops, and estimated journey durations when configured." />
      <div className="toolbar"><SearchField value={query} onChange={(value) => { setQuery(value); setPage(1); }} placeholder="Search by route name or code" /><input value={destination} onChange={(event) => { setDestination(event.target.value); setPage(1); }} placeholder="Destination" aria-label="Filter by destination" /><select aria-label="Filter by service area" value={area} onChange={(event) => { setArea(event.target.value); setPage(1); }}><option value="">All areas</option>{serviceAreas.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><select aria-label="Filter by route type" value={serviceType} onChange={(event) => { setServiceType(event.target.value); setPage(1); }}><option value="">All service types</option>{serviceTypes.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><select aria-label="Filter by current status" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">All current statuses</option>{serviceStatuses.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></div>
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
  const [area, setArea] = useState("");
  const [serviceType, setServiceType] = useState("");
  const [status, setStatus] = useState("");
  const items = useApi(() => shuttleStatusApi.list({ limit: 100, ...(area ? { service_area: area } : {}), ...(serviceType ? { service_type: serviceType } : {}), ...(status ? { status } : {}) }), [area, serviceType, status]);
  const filtered = items.data?.items?.filter((item) =>
    item.shuttle.vehicle_code.toLowerCase().includes(search.toLowerCase())
  ) || [];
  return (
    <div className="page-content">
      <PageHeader eyebrow="CAMPUS TRANSPORT" title="Shuttle information" description="View active shuttle vehicles and the latest service information recorded by the transport team." />
      <div className="toolbar"><SearchField value={search} onChange={setSearch} placeholder="Search vehicle or service code" /><select aria-label="Filter by service area" value={area} onChange={(event) => setArea(event.target.value)}><option value="">All areas</option>{serviceAreas.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><select aria-label="Filter by service type" value={serviceType} onChange={(event) => setServiceType(event.target.value)}><option value="">All service types</option>{serviceTypes.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><select aria-label="Filter by current status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All current statuses</option>{serviceStatuses.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></div>
      {items.loading ? <Loading /> : items.error ? <ErrorState message={items.error} onRetry={items.refresh} /> : filtered.length ? (
        <div className="shuttle-grid">{filtered.map(({ shuttle, status: serviceStatus, message, last_updated_at: updated }) => (
          <Link className="shuttle-card" to={`/student/shuttles/${shuttle.id}`} key={shuttle.id}>
            <div className="shuttle-card__header"><span className="shuttle-card__icon"><BusFront size={20} /></span><StatusBadge status={serviceStatus} /></div>
            <p className="eyebrow">{shuttle.is_university_operated ? "UNIVERSITY-OPERATED" : "EXTERNAL PUBLIC TRANSPORT"}</p>
            <h3>{shuttle.vehicle_code}</h3>
            <p>{labelFor(serviceTypes, shuttle.service_type)} · {shuttle.route_id ? "Assigned to a route" : "No route assigned"}</p>
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
