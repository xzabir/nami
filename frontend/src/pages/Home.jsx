import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <>
      <nav className="nav">
        <div className="brand"><span className="dot"></span> Nami</div>
        <div className="nav-links">
          <Link to="/login" className="btn btn-ghost"><span className="long">Log</span> In</Link>
          <Link to="/signup" className="btn btn-primary">Sign Up</Link>
        </div>
      </nav>

      <header className="wrap hero">
        <div>
          <div className="eyebrow">Track 2 · Video Captioning Agent</div>
          <h1>Four takes.<br />One clip. <em>Zero rewrites.</em></h1>
          <p className="lead">
            Drop in a video URL and Nami watches it frame by frame with
            Gemma 3's vision model, then writes a formal caption, a sarcastic one,
            and two flavors of funny — all grounded in what's actually on screen.
          </p>
          <div className="hero-actions">
            <Link to="/signup" className="btn btn-primary">Start captioning</Link>
            <Link to="/login" className="btn btn-ghost">I have an account</Link>
          </div>
        </div>

        <div className="slate">
          <div className="slate-header">
            <span>CLIP_014.MP4</span>
            <span>00:00:07 — 00:01:52</span>
          </div>
          <div className="take-row">
            <div className="take-tag">Formal</div>
            <div className="take-text">A cyclist crosses an intersection lined with autumn trees as traffic moves along the boulevard.</div>
          </div>
          <div className="take-row">
            <div className="take-tag">Sarcastic</div>
            <div className="take-text">Wow, a street with cars on it. Truly the content the algorithm was starving for.</div>
          </div>
          <div className="take-row">
            <div className="take-tag">Humorous · Tech</div>
            <div className="take-text">This tree is running autumn.exe and hasn't thrown an exception yet.</div>
          </div>
          <div className="take-row">
            <div className="take-tag">Humorous · Non-tech</div>
            <div className="take-text">The trees really said "let's all change color at once" and nobody objected.</div>
          </div>
        </div>
      </header>

      <section className="section wrap">
        <div className="section-head">
          <h2>Built for the accuracy + style scoring rubric</h2>
          <p>Every design choice maps directly to how Track 2 submissions are judged: caption accuracy and style match, across a hidden set the agent has never seen.</p>
        </div>
        <div className="grid-3">
          <div className="card">
            <div className="idx">01 — Grounding</div>
            <h3>Frame sampling, not guesswork</h3>
            <p>Eight frames evenly sampled across the clip (skipping intro/outro fades) give Gemma 3 real visual context instead of a single thumbnail.</p>
          </div>
          <div className="card">
            <div className="idx">02 — Consistency</div>
            <h3>One grounded call, four styles</h3>
            <p>All four captions come from a single multimodal request, so they describe the same scene instead of drifting across separate calls.</p>
          </div>
          <div className="card">
            <div className="idx">03 — Reliability</div>
            <h3>Schema-safe under pressure</h3>
            <p>Strict JSON validation, an automatic repair retry, and a wall-clock budget guard mean one slow clip never zeroes out the whole run.</p>
          </div>
        </div>
      </section>

      <footer>
        <span>Nami — AMD Developer Hackathon, Track 2</span>
        <span>Gemma 3 · FastAPI · PostgreSQL</span>
      </footer>
    </>
  );
}
