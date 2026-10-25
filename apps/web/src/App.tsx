import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Activity, AlertCircle, BrainCircuit, CheckCircle2, ChevronRight, Cpu, Download, FlaskConical, History, Info, Layers, Play, RefreshCw, Square, Trash2 } from 'lucide-react';
import { createRegressionManifest, validateManifestBounds, type RegressionManifest, type Submission, type Evidence } from './regressionManifest';
import './styles.css';

type Status = 'queued'|'running'|'completed'|'failed'|'cancelled';
type Config = {device:string;layer:number;token_index:number;revision:string|null};
type Result = Evidence & {
 activation_rms_delta:number[][];
 scores:{clean:number;corrupted:number;patched:number;recovery:number|null};
 control:{max_abs_logit_delta:number;tolerance:number};
 patch:{layer:number;token_index:number;site:string};runtime_seconds?:number
};
type Experiment = {id:string;status:Status;created_at:string;configuration:Config;error:string|null;result:Result|null};
type HistoryItem = Pick<Experiment,'id'|'status'|'created_at'|'configuration'>;
type FormValues = Submission;
type RuntimeDiagnostics = {python:string;python_supported:boolean;os:string;architecture:string;torch_installed:boolean;transformerlens_installed:boolean;free_disk_gb:number;model_download_required_first_use:boolean};
const starter:FormValues = {clean:'The dog runs',corrupted:'The cat runs',correct_token:' dog',incorrect_token:' cat',layer:5,token_index:2,device:'cpu',revision:''};
const done = (s:Status) => ['completed','failed','cancelled'].includes(s);
const number = (n:number|null|undefined,places=4) => typeof n==='number'&&Number.isFinite(n) ? n.toFixed(places) : '—';
function authorizedFetch(path:string,init?:RequestInit):Promise<Response> {
 const headers=new Headers(init?.headers);
 const token=window.sessionStorage.getItem('cortex-pair-token');
 if(token)headers.set('Authorization','Bearer '+token);
 return fetch(path,{...init,headers});
}
async function api<T>(path:string,init?:RequestInit):Promise<T> {
 const res=await authorizedFetch(path,init); const data=await res.json().catch(()=>({}));
 if(!res.ok){const d=data.detail; throw new Error(typeof d==='string'?d:Array.isArray(d)?d.map((e:{msg:string})=>e.msg).join('; '):'HTTP '+res.status)}
 return data as T;
}
function Heatmap({data,selection,onSelect}:{data:number[][];selection:[number,number];onSelect:(row:number,col:number)=>void}){
 const max=Math.max(1e-10,...data.flat().filter(Number.isFinite));
 return <div className="heat-scroll"><div className="heat-grid" style={{gridTemplateColumns:`35px repeat(${data[0]?.length??1},minmax(19px,1fr))`}}>
 {data.map((row,i)=><div key={i} style={{display:'contents'}}><span className="layer">{i}</span>{row.map((v,j)=><button type="button" key={j}
 className={'heat-cell '+(selection[0]===i&&selection[1]===j?'chosen':'')}
 style={{backgroundColor:`rgba(72,171,248,${.09+.86*Math.sqrt(Math.max(0,v)/max)})`}}
 title={`Layer ${i} / token ${j} / RMS ${number(v,6)}`}
 aria-label={`Layer ${i}, token ${j}, RMS ${number(v,6)}`}
 onClick={()=>onSelect(i,j)}/>)}</div>)}</div><div className="heat-legend">Layer ↓ · Token position → · Brighter = larger RMS difference</div></div>
}
export default function App(){
 const [tab,setTab]=useState<'studio'|'history'>('studio');
 const [form,setForm]=useState<FormValues>(starter);
 const [connected,setConnected]=useState(false);
 const [pairingRequired,setPairingRequired]=useState(false);
 const [authenticated,setAuthenticated]=useState(true);
 const [pairCode,setPairCode]=useState('');
 const [pairBusy,setPairBusy]=useState(false);
 const [pairError,setPairError]=useState('');
 const [runtime,setRuntime]=useState<RuntimeDiagnostics|null>(null);
 const [current,setCurrent]=useState<Experiment|null>(null);
 const [history,setHistory]=useState<HistoryItem[]>([]);
 const [error,setError]=useState('');
 const [pending,setPending]=useState(false);
 const [cell,setCell]=useState<[number,number]>([5,2]);
 // Raw prompts are kept only in this in-memory session, never in SQLite.
 const [submitted,setSubmitted]=useState<{id:string;form:FormValues}|null>(null);
 const [manifest,setManifest]=useState<RegressionManifest|null>(null);
 const edit=<K extends keyof FormValues,>(name:K,value:FormValues[K])=>setForm(prev=>({...prev,[name]:value}));
 const loadHistory=useCallback(async()=>{try{setHistory((await api<{items:HistoryItem[]}>('/api/v1/experiments?limit=30')).items)}catch{/* health/errors shown elsewhere */}},[]);
 const loadJob=useCallback(async(id:string)=>{const result=await api<Experiment>('/api/v1/experiments/'+encodeURIComponent(id));setCurrent(result);if(done(result.status))void loadHistory()},[loadHistory]);
 const refreshRuntime=useCallback(async()=>{try{setRuntime(await api<RuntimeDiagnostics>('/api/v1/setup'))}catch{setRuntime(null)}},[]);
 useEffect(()=>{
  void api('/api/v1/health').then(()=>{setConnected(true);void refreshRuntime()}).catch(()=>setConnected(false));
  void api<{enabled:boolean;authenticated:boolean}>('/api/v1/auth/status')
   .then(status=>{
    setPairingRequired(status.enabled);
    setAuthenticated(status.authenticated);
    if(status.authenticated)void loadHistory();
    else if(window.sessionStorage.getItem('cortex-pair-token'))
      window.sessionStorage.removeItem('cortex-pair-token');
   })
   .catch(()=>{setPairingRequired(false);setAuthenticated(true);void loadHistory()});
 },[loadHistory,refreshRuntime]);
 const pairBrowser=async(e:FormEvent<HTMLFormElement>)=>{
  e.preventDefault();setPairError('');setPairBusy(true);
  try {
   const result=await api<{token:string}>('/api/v1/auth/pair',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({code:pairCode.trim()})
   });
   window.sessionStorage.setItem('cortex-pair-token',result.token);
   setPairCode('');setAuthenticated(true);void loadHistory();
  } catch(e){setPairError(e instanceof Error?e.message:String(e))}
  finally{setPairBusy(false)}
 };
 useEffect(()=>{if(!current||done(current.status))return;const timer=window.setInterval(()=>{void loadJob(current.id).catch(e=>setError(String(e)))},1100);return()=>window.clearInterval(timer)},[current?.id,current?.status,loadJob]);
 const run=async(e:FormEvent<HTMLFormElement>)=>{
  e.preventDefault();setError('');setPending(true);
  try{
   const req={...form,revision:form.revision.trim()||null};
   const job=await api<{id:string;status:Status;created_at:string}>('/api/v1/experiments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(req)});
   setSubmitted({id:job.id,form:{...form}});
   setManifest(null);
   setCurrent({...job,configuration:req,error:null,result:null});setCell([form.layer,form.token_index]);setTab('studio');setConnected(true);void loadHistory()
  }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setPending(false)}
 };
 const cancel=async()=>{if(!current)return;try{await api('/api/v1/experiments/'+current.id+'/cancel',{method:'POST'});await loadJob(current.id)}catch(e){setError(String(e))}};
 const download=()=>{if(!current?.result)return;const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='cortex-'+current.id.slice(0,8)+'.json';a.click();URL.revokeObjectURL(url)};
 const downloadShareable=async()=>{
  if(!current)return;
  setError('');
  try {
   const report=await api<Record<string,unknown>>('/api/v1/experiments/'+current.id+'/shareable');
   const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
   const a=document.createElement('a');a.href=url;a.download='cortex-shareable-'+current.id.slice(0,8)+'.json';a.click();URL.revokeObjectURL(url);
  } catch(e){setError(e instanceof Error?e.message:String(e))}
 };
 const deleteRecord=async(id:string)=>{
  if(!window.confirm('Delete this local experiment record? SQLite backups may retain earlier copies.'))return;
  setError('');
  try {
   const response=await authorizedFetch('/api/v1/experiments/'+id,{method:'DELETE'});
   if(!response.ok)throw new Error(response.status===409?'Cancel the running job before deletion.':'Unable to delete experiment.');
   if(current?.id===id){setCurrent(null);setSubmitted(null);setManifest(null)}
   await loadHistory();
  } catch(e){setError(e instanceof Error?e.message:String(e))}
 };
 const generateManifest=async()=>{
  setError('');
  if(!current?.result||current.status!=='completed'||submitted?.id!==current.id){
   setError('Manifest generation requires a completed experiment from this browser session. History does not preserve raw prompts.');return;
  }
  try { setManifest(await createRegressionManifest(submitted.form,current.result)); }
  catch(e){setError(e instanceof Error?e.message:String(e))}
 };
 const editLimit=(name:keyof RegressionManifest['assertions'],value:number)=>{
  setManifest(prev=>prev?{...prev,assertions:{...prev.assertions,[name]:value}}:prev);
 };
 const downloadManifest=()=>{
  if(!manifest)return;
  const problem=validateManifestBounds(manifest);
  if(problem){setError(problem);return;}
  const blob=new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob); const a=document.createElement('a');
  a.href=url; a.download='cortex-regression-'+(current?.id.slice(0,8)??'experiment')+'.json';
  a.click();URL.revokeObjectURL(url);
 };
 const busy=pending||Boolean(current&&!done(current.status));
 const result=current?.result; const rms=result?.activation_rms_delta?.[cell[0]]?.[cell[1]];

 if(pairingRequired&&!authenticated)return <div className="pair-screen">
  <form className="pair-card" onSubmit={pairBrowser}>
   <span className="pair-icon"><BrainCircuit size={30}/></span>
   <h1>Connect to your local Cortex</h1>
   <p>Enter the nine-digit code displayed in the app launcher or terminal. The code works once per server launch and is never saved to experiment history.</p>
   <label htmlFor="cortex-pair-code">PAIRING CODE</label>
   <input id="cortex-pair-code" aria-label="Pairing code" autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{9}" maxLength={9} required value={pairCode} onChange={e=>setPairCode(e.target.value.replace(/\D/g,''))} placeholder="9-digit code"/>
   {pairError&&<p role="alert" className="pair-error">{pairError}</p>}
   <button type="submit" className="primary" disabled={pairBusy||pairCode.length!==9}>{pairBusy?'Connecting…':'Unlock local studio'}</button>
   <small>This protects the app from unauthenticated local HTTP clients without the code. It cannot protect against malicious software with access to your operating-system account.</small>
  </form>
 </div>;
 return <div className="shell"><aside className="sidebar">
 <div className="brand"><span className="logo"><BrainCircuit size={22}/></span>Cortex <strong>Debugger</strong></div>
 <div className="aside-label">WORKSPACE</div>
 <button className={'side-link '+(tab==='studio'?'selected':'')} onClick={()=>setTab('studio')}><FlaskConical size={17}/> Experiment <ChevronRight size={15}/></button>
 <button className={'side-link '+(tab==='history'?'selected':'')} onClick={()=>{setTab('history');void loadHistory()}}><History size={17}/> History <small>{history.length}</small></button>
 <hr/><div className="aside-label">MODEL</div><div className="model"><Cpu size={18}/><div>GPT-2 Small<small>12 layers · local weights</small></div></div>
 <div className="aside-foot"><span className={'indicator '+(connected?'ok':'')}/>{connected?'Local API connected':'API offline'}<small>M11 · authentication preview</small></div>
 </aside><main><header><span>CORTEX / {tab==='studio'?'EXPERIMENT STUDIO':'HISTORY'}</span><div><span className="local-pill">LOCAL ONLY</span><span>v0.10.0-rc1</span></div></header>
 <div className="content"><div className="heading"><div><div className="eyebrow">MECHANISTIC INTERPRETABILITY / M11</div><h1>{tab==='studio'?'Experiment studio':'Experiment history'}</h1><p>Compare model runs, intervene on residual activations, and inspect measured effects.</p></div><span className="model-pill"><Activity size={13}/> GPT-2 ENGINE</span></div>
 {error&&<div className="error" role="alert"><AlertCircle size={16}/>{error}<button onClick={()=>setError('')} aria-label="Dismiss">×</button></div>}
 {!connected&&<div className="notice"><Info size={15}/>API offline. Run <code>uvicorn apps.api.main:app --host 127.0.0.1 --port 8000</code> then refresh.</div>}
 {tab==='studio'&&connected&&<section className="runtime-readiness" aria-label="Local runtime readiness">
 <div className="runtime-main"><span className="runtime-title"><Cpu size={16}/> Local runtime check</span>
 <small>{runtime?runtime.os+' · '+runtime.architecture+' · Python '+runtime.python:'Checking Python and model dependencies…'}</small></div>
 {runtime&&<div className="runtime-checks">
  <span className={runtime.python_supported?'ready':'missing'}>Python {runtime.python_supported?'ready':'unsupported'}</span>
  <span className={runtime.torch_installed?'ready':'missing'}>PyTorch {runtime.torch_installed?'installed':'missing'}</span>
  <span className={runtime.transformerlens_installed?'ready':'missing'}>TransformerLens {runtime.transformerlens_installed?'installed':'missing'}</span>
  <span>Free disk {runtime.free_disk_gb.toFixed(1)} GB</span>
 </div>}
 <button type="button" className="secondary" onClick={()=>void refreshRuntime()}><RefreshCw size={14}/> Check again</button>
 <p className="runtime-note">GPT-2 weights download on first use. Model loading happens only when you run an experiment.</p>
 </section>}
 {tab==='studio'?<><div className="studio">
 <form className="panel" onSubmit={run}>
 <div className="panel-heading"><span className="panel-icon"><Layers size={17}/></span><div><h2>Input configuration</h2><p>Clean / corrupted / patch</p></div></div>
 <div className="fields"><label>CLEAN PROMPT <small>Source A</small><textarea value={form.clean} onChange={e=>edit('clean',e.target.value)} rows={3} required maxLength={600}/></label>
 <label>CORRUPTED PROMPT <small>Target B</small><textarea value={form.corrupted} onChange={e=>edit('corrupted',e.target.value)} rows={3} required maxLength={600}/></label>
 <div className="columns"><label>CORRECT TOKEN<input value={form.correct_token} onChange={e=>edit('correct_token',e.target.value)} required maxLength={60}/></label><label>INCORRECT TOKEN<input value={form.incorrect_token} onChange={e=>edit('incorrect_token',e.target.value)} required maxLength={60}/></label></div>
 <div className="columns"><label>PATCH LAYER<input type="number" min="0" max="11" value={form.layer} onChange={e=>edit('layer',Number(e.target.value))} required/></label><label>TOKEN INDEX<input type="number" min="0" max="127" value={form.token_index} onChange={e=>edit('token_index',Number(e.target.value))} required/></label></div>
 <div className="columns"><label>COMPUTE<select value={form.device} onChange={e=>edit('device',e.target.value as 'cpu'|'mps')}><option value="cpu">CPU (portable)</option><option value="mps">Apple MPS</option></select></label><label>MODEL SHA OVERRIDE<input value={form.revision} onChange={e=>edit('revision',e.target.value)} placeholder="Defaults to pinned GPT-2 SHA"/></label></div>
 <div className="hint"><Info size={15}/> Both inputs must tokenize to equal lengths; candidate strings must each be a single GPT-2 token.</div></div>
 <div className="form-foot"><button className="primary" disabled={busy||!connected}><Play size={15} fill="currentColor"/>{busy?'Experiment in progress':'Run experiment'}</button><small>1 running + up to 2 waiting</small></div></form>
 <div className="outputs"><section className="panel"><div className="result-head"><h2>Experiment results</h2><span className={'status '+(current?.status??'idle')}>{current?.status??'Awaiting run'}</span></div>
 {result?<><div className="scores"><div><small>CLEAN MARGIN</small><strong>{number(result.scores.clean)}</strong></div><div><small>CORRUPTED</small><strong>{number(result.scores.corrupted)}</strong></div><div><small>PATCHED</small><strong>{number(result.scores.patched)}</strong></div></div>
 <div className="recovery"><div><small>NORMALIZED RECOVERY</small><strong>{result.scores.recovery==null?'Undefined':number(result.scores.recovery*100,1)+'%'}</strong></div><span>May be negative or above 100%</span></div>
 <div className="control"><CheckCircle2 size={16} color={result.status==='pass'?'#44d3a0':'#f4a377'}/> Self-patch control {number(result.control.max_abs_logit_delta,6)} / tolerance {number(result.control.tolerance,6)}</div></>:
 <div className="empty"><span className="empty-icon"><Activity size={25}/></span><strong>{current?'Experiment '+current.status:'No results yet'}</strong><p>{current?.error??(current?'Model execution is pending or running.':'Run an experiment to see scores and activation changes.')}</p>{(current?.status==='queued'||current?.status==='running')&&<button className="secondary" onClick={cancel} type="button"><Square size={14}/> Cancel experiment</button>}</div>}</section>
 <section className="panel"><div className="result-head"><div><h2>Activation difference</h2><p>Residual stream · layer × token · RMS</p></div><span className="descriptive">DESCRIPTIVE</span></div>
 {result?<><Heatmap data={result.activation_rms_delta} selection={cell} onSelect={(l,t)=>{setCell([l,t]);edit('layer',l);edit('token_index',t)}}/><div className="pick"><b>Layer {cell[0]} · Token {cell[1]}</b><span>RMS {number(rms,6)} — Rerun to patch this location</span></div></>:<div className="heat-empty"><Layers size={22}/>Run an experiment to populate the heatmap</div>}</section>
 {result&&<div className="export-actions">
 <button className="secondary export" onClick={download}><Download size={15}/> Export full evidence (token IDs)</button>
 {current?.status==='completed'&&<button className="secondary export" onClick={()=>void downloadShareable()}><Download size={15}/> Export redacted summary</button>}
 </div>}
 <section className="panel regression-panel">
  <div className="result-head"><div><h2>Regression test</h2><p>M3 JSON manifest · reviewed numerical bounds</p></div><span className="descriptive">LOCAL EXPORT</span></div>
  <div className="regression-content">
   <p>Create a pinned-model replay test from a verified experiment. The file stays in this browser until you choose to save it.</p>
   <div className="privacy-warning"><AlertCircle size={16}/><span><strong>Contains raw prompts.</strong> Do not publish this manifest if prompts are private. Only successful runs from this browser session can be exported.</span></div>
   {result&&current?.status==='completed'&&submitted?.id===current.id?
     <button className="secondary regression-build" onClick={()=>void generateManifest()}>Prepare regression test</button>:
     <p className="manifest-unavailable">Run a passing experiment here to enable manifest export. Saved history alone cannot reconstruct prompts.</p>}
   {manifest&&<div className="manifest-editor" aria-label="Regression thresholds">
     <p>Review these starting tolerances before saving. They are engineering defaults, not statistical confidence intervals.</p>
     <div className="manifest-bounds">
       {([
         ['control_delta_max','MAX CONTROL DELTA'],
         ['recovery_min','MIN RECOVERY'],
         ['recovery_max','MAX RECOVERY'],
         ['patched_margin_min','MIN PATCHED MARGIN'],
         ['patched_margin_max','MAX PATCHED MARGIN'],
       ] as const).map(([key,label])=><label key={key}>{label}
         <input type="number" step="any" value={manifest.assertions[key]}
           onChange={e=>editLimit(key,e.target.valueAsNumber)} />
       </label>)}
     </div>
     <div className="manifest-actions">
       <button className="primary" type="button" onClick={downloadManifest} disabled={Boolean(validateManifestBounds(manifest))}>
         <Download size={15}/> Download regression JSON
       </button>
       <small>Replay with: <code>cortex verify your-file.json</code></small>
     </div>
     {validateManifestBounds(manifest)&&<div className="error">{validateManifestBounds(manifest)}</div>}
   </div>}
  </div>
 </section></div></div>
 <div className="disclaimer"><Info size={16}/> A heatmap is descriptive, not causal proof. Patching results apply only to the exact model and inputs. Pin revision for future regression tests.</div></>:
 <section className="panel history-panel"><div className="result-head"><h2>Recent experiments</h2><button className="secondary" onClick={()=>void loadHistory()}><RefreshCw size={14}/> Refresh</button></div>{history.length?history.map(item=><div key={item.id} className="history-item">
 <button className="history-open" onClick={()=>{setSubmitted(null);setManifest(null);void loadJob(item.id).then(()=>{setTab('studio');setCell([item.configuration.layer,item.configuration.token_index])}).catch(e=>setError(String(e)))}}><History size={15}/><div><b>{item.id.slice(0,8)}</b><small>{new Date(item.created_at).toLocaleString()} · L{item.configuration.layer}/T{item.configuration.token_index}</small></div><span className={'status '+item.status}>{item.status}</span><ChevronRight size={15}/></button>
 <button className="delete-record" title="Delete local record" aria-label={'Delete experiment '+item.id.slice(0,8)} onClick={()=>void deleteRecord(item.id)}><Trash2 size={15}/></button>
 </div>):<div className="empty"><p>No local experiments yet.</p></div>}</section>}
 </div></main></div>;
}
