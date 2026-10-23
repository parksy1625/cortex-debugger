import { useEffect, useState } from 'react';
import { Activity, BrainCircuit, CircleCheck, CircleAlert, FlaskConical, GitBranch } from 'lucide-react';

type Health = {status: string; stage: string; version: string};

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/v1/health', {signal: controller.signal})
      .then((res) => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
      .then(setHealth)
      .catch((err) => { if (err.name !== 'AbortError') setError('Local API is not running'); });
    return () => controller.abort();
  }, []);

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><BrainCircuit size={22}/><span>Cortex <b>Debugger</b></span></div>
      <div className="section">WORKSPACE</div>
      <div className="nav active"><Activity size={17}/> Overview</div>
      <div className="nav disabled"><FlaskConical size={17}/> Experiments <span>soon</span></div>
      <div className="nav disabled"><GitBranch size={17}/> Regression tests <span>soon</span></div>
      <div className="footer">Local-first · Open source<br/>M0 technical validation</div>
    </aside>
    <main>
      <header><span>WORKSPACE / OVERVIEW</span><span className="pill">M0 · Prototype</span></header>
      <div className="content">
        <div className="eyebrow">CAUSAL MODEL DEBUGGING</div>
        <h1>Understand what changed.<br/><em>Test what caused it.</em></h1>
        <p className="lead">Cortex Debugger turns model intervention experiments into reproducible regression tests. The current milestone verifies the model hook engine before experiment UI is enabled.</p>
        <div className="panel">
          <div className="panel-head"><span>Local engine status</span>{health ? <CircleCheck color="#34b98a" size={20}/> : <CircleAlert color="#f19d52" size={20}/>}</div>
          <div className="status-grid">
            <div><small>API CONNECTION</small><strong>{health ? 'Connected' : 'Disconnected'}</strong></div>
            <div><small>ENGINE MILESTONE</small><strong>{health?.stage ?? 'M0'}</strong></div>
            <div><small>MODEL</small><strong>GPT-2 Small</strong></div>
          </div>
          {error && <div className="warning">{error}. Start: <code>uvicorn apps.api.main:app --host 127.0.0.1</code></div>}
        </div>
        <h2>First executable experiment</h2>
        <div className="step"><div className="number">01</div><div><b>Identity control</b><p>Load GPT-2, capture a residual activation, replace it with itself, and compare final logits.</p><code>cortex smoke --device cpu --layer 0 --token-index 0</code></div></div>
        <div className="step"><div className="number">02</div><div><b>Verify baseline</b><p>Check the measured maximum absolute logit difference against a declared tolerance.</p></div></div>
        <div className="step"><div className="number">03</div><div><b>Build paired-prompt debugger</b><p>Next milestone: clean/corrupted prompts, layer/token visualization, and patching comparison.</p></div></div>
      </div>
    </main>
  </div>;
}
