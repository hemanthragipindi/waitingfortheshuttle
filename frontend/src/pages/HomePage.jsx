import {
  ArrowRight,
  ArrowUpRight,
  BusFront,
  CircleHelp,
  Clock3,
  MapPin,
  MessageSquareText,
  Route,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <main className="landing">
      <section className="landing-hero">
        <div className="landing-hero__content">
          <span className="landing-kicker"><span /> LOVELY PROFESSIONAL UNIVERSITY</span>
          <h1>Know before you <em>go.</em></h1>
          <p className="landing-hero__intro">
            A clearer campus commute starts with dependable information. Find your stop, browse routes, and check the latest shuttle service updates.
          </p>
          <div className="landing-hero__actions">
            <Link className="button button--primary button--large" to="/login">
              Student sign in <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <Link className="landing-text-link" to="/register">Create an account <ArrowUpRight size={16} /></Link>
          </div>
          <p className="landing-disclaimer"><CircleHelp size={15} /> Updates are manually reported. This service does not provide live GPS or predicted arrival times.</p>
        </div>
        <div className="landing-visual" aria-label="Illustration of the campus shuttle information experience">
          <div className="landing-visual__grid" aria-hidden="true" />
          <div className="transit-card">
            <div className="transit-card__top">
              <span className="transit-card__icon"><BusFront size={20} /></span>
              <span><small>SHUTTLE INFORMATION</small><strong>Campus service</strong></span>
              <span className="transit-card__menu">•••</span>
            </div>
            <div className="transit-card__route">
              <span className="transit-card__line"><i /><i /><i /></span>
              <div><small>ROUTE</small><strong>Plan your campus journey</strong></div>
            </div>
            <div className="transit-card__details">
              <span><MapPin size={16} /><span><small>STOPS</small><strong>Browse campus stops</strong></span></span>
              <span><Clock3 size={16} /><span><small>SERVICE STATUS</small><strong>See latest updates</strong></span></span>
            </div>
            <div className="transit-card__foot"><ShieldCheck size={15} /> Information from your transport team</div>
          </div>
          <div className="landing-visual__caption">A better-informed wait starts here.</div>
        </div>
      </section>

      <section className="landing-features">
        <div className="landing-features__heading">
          <p className="eyebrow">MADE FOR CAMPUS LIFE</p>
          <h2>Make your next trip feel simpler.</h2>
        </div>
        <div className="feature-grid">
          <article className="feature-item"><span><MapPin size={19} /></span><h3>Find your stop</h3><p>Browse campus stops and see which routes serve each location.</p></article>
          <article className="feature-item"><span><Route size={19} /></span><h3>Explore routes</h3><p>Review route stops in order and plan around available information.</p></article>
          <article className="feature-item"><span><MessageSquareText size={19} /></span><h3>Share an update</h3><p>Report an issue or suggestion directly to the transport team.</p></article>
        </div>
      </section>
    </main>
  );
}
