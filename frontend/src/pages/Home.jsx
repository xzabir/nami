import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <>
      <nav className="nav container">
        <div className="flex items-center justify-between">
          <div className="brand">
            <span className="dot"></span> Nami
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="btn btn-ghost text-sm">Log In</Link>
            <Link to="/signup" className="btn btn-primary text-sm">Sign Up</Link>
          </div>
        </div>
      </nav>

      <main className="container">
        <section className="hero">
          <div className="badge badge-neutral mb-6">Track 2 · Video Captioning Agent</div>
          <h1>Four takes.<br />One clip. <span style={{ color: 'var(--accent)' }}>Zero rewrites.</span></h1>
          <p className="text-muted mt-6" style={{ maxWidth: '600px', margin: '1.5rem auto 0', fontSize: '1.1rem' }}>
            Drop in a video URL and Nami watches it frame by frame with
            Gemma 3's vision model, then writes a formal caption, a sarcastic one,
            and two flavors of funny — all grounded in what's actually on screen.
          </p>
          <div className="flex items-center justify-center gap-4 mt-12">
            <Link to="/signup" className="btn btn-primary">Start captioning</Link>
            <Link to="/login" className="btn btn-outline">I have an account</Link>
          </div>
        </section>

        <section className="mt-12 mb-12">
          <div className="text-center mb-12">
            <h2>Built for the accuracy + style scoring rubric</h2>
            <p className="text-muted" style={{ maxWidth: '600px', margin: '0 auto' }}>
              Every design choice maps directly to how Track 2 submissions are judged: caption accuracy and style match, across a hidden set the agent has never seen.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <div className="card">
              <div className="font-mono text-xs uppercase" style={{ color: 'var(--accent)' }}>01 — Grounding</div>
              <h3 className="mt-4">Frame sampling, not guesswork</h3>
              <p className="text-muted text-sm mt-2">
                Eight frames evenly sampled across the clip give Gemma 3 real visual context instead of a single thumbnail.
              </p>
            </div>
            
            <div className="card">
              <div className="font-mono text-xs uppercase" style={{ color: 'var(--accent)' }}>02 — Consistency</div>
              <h3 className="mt-4">One grounded call, four styles</h3>
              <p className="text-muted text-sm mt-2">
                All four captions come from a single multimodal request, so they describe the same scene without drifting.
              </p>
            </div>

            <div className="card">
              <div className="font-mono text-xs uppercase" style={{ color: 'var(--accent)' }}>03 — Reliability</div>
              <h3 className="mt-4">Schema-safe under pressure</h3>
              <p className="text-muted text-sm mt-2">
                Strict JSON validation and an automatic repair retry mean one slow clip never zeroes out the whole run.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="container py-8 mt-12" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex items-center justify-between text-xs font-mono text-muted">
          <span>Nami — AMD Developer Hackathon, Track 2</span>
          <span>Gemma 3 · FastAPI · PostgreSQL</span>
        </div>
      </footer>
    </>
  );
}
