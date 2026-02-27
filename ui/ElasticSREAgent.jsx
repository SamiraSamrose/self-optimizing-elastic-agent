import { useState, useEffect, useRef, useCallback } from "react";

const STYLE = `
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Barlow+Condensed:wght@300;400;500;600;700;800&family=Barlow:wght@300;400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
:root{
  --bg:#05080d;--bg2:#080d15;--panel:#0a1220;--panel2:#0d1828;
  --border:#162030;--border2:#1e2e42;
  --accent:#00c8ff;--accent2:#0077aa;
  --green:#00e5a0;--green2:#007755;
  --yellow:#f5c518;--red:#ff3d5a;--orange:#ff7c2a;--purple:#c084fc;
  --text:#b8cfe0;--text2:#6a8fa8;--text3:#3a5870;
  --mono:'IBM Plex Mono',monospace;
  --cond:'Barlow Condensed',sans-serif;
  --body:'Barlow',sans-serif;
}
html,body,#root{height:100%;background:var(--bg);color:var(--text);font-family:var(--body);}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}
@keyframes spin{to{transform:rotate(360deg);}}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
@keyframes scan{0%{top:-2px;}100%{top:100vh;}}
.scanline{position:fixed;left:0;right:0;height:1px;background:rgba(0,200,255,.03);animation:scan 9s linear infinite;pointer-events:none;z-index:9999;}
.app{display:grid;grid-template-columns:230px 1fr;grid-template-rows:52px 1fr;height:100vh;overflow:hidden;}
.hdr{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;padding:0 20px;background:var(--bg2);border-bottom:1px solid var(--border);z-index:10;}
.hdr-logo{display:flex;align-items:center;gap:10px;}
.hdr-hex{width:28px;height:28px;background:linear-gradient(135deg,var(--accent),var(--green));clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);}
.hdr-title{font-family:var(--cond);font-size:17px;font-weight:800;letter-spacing:.1em;color:var(--accent);}
.hdr-sub{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.04em;}
.hdr-meta{display:flex;gap:18px;align-items:center;}
.hdr-pill{display:flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10px;color:var(--text2);}
.dot{width:6px;height:6px;border-radius:50%;}
.dot-green{background:var(--green);animation:pulse 2s ease-in-out infinite;}
.dot-yellow{background:var(--yellow);animation:pulse 2s ease-in-out infinite;}
.hdr-time{font-family:var(--mono);font-size:10px;color:var(--text3);}
.sidebar{background:var(--bg2);border-right:1px solid var(--border);overflow-y:auto;padding:8px 0;}
.sb-sec{font-family:var(--mono);font-size:9px;font-weight:600;letter-spacing:.12em;color:var(--text3);padding:14px 14px 5px;text-transform:uppercase;}
.nav{display:flex;align-items:center;gap:8px;padding:7px 14px;cursor:pointer;font-family:var(--cond);font-size:13px;font-weight:500;color:var(--text2);letter-spacing:.03em;border-left:2px solid transparent;transition:all .15s;}
.nav:hover{color:var(--text);background:rgba(0,200,255,.04);}
.nav.on{color:var(--accent);border-left-color:var(--accent);background:rgba(0,200,255,.07);}
.nav-ico{width:6px;height:6px;border-radius:50%;flex-shrink:0;opacity:.8;}
.nbadge{margin-left:auto;background:var(--red);color:#fff;font-family:var(--mono);font-size:9px;padding:1px 5px;border-radius:8px;}
.main{overflow-y:auto;background:var(--bg);padding:18px;}
.pnl{background:var(--panel);border:1px solid var(--border);border-radius:6px;margin-bottom:14px;animation:fadeIn .25s ease;}
.pnl-hdr{display:flex;align-items:center;justify-content:space-between;padding:11px 15px;border-bottom:1px solid var(--border);}
.pnl-title{display:flex;align-items:center;gap:7px;font-family:var(--cond);font-size:14px;font-weight:700;letter-spacing:.05em;color:var(--text);}
.pnl-tag{font-family:var(--mono);font-size:9px;color:var(--text3);background:var(--bg);border:1px solid var(--border);padding:2px 7px;border-radius:3px;}
.pnl-body{padding:14px;}
.btn{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:11px;font-weight:500;padding:6px 13px;border-radius:4px;cursor:pointer;border:1px solid;transition:all .15s;letter-spacing:.02em;}
.btn-primary{background:rgba(0,200,255,.1);border-color:var(--accent2);color:var(--accent);}
.btn-primary:hover:not(:disabled){background:rgba(0,200,255,.2);border-color:var(--accent);}
.btn-green{background:rgba(0,229,160,.08);border-color:var(--green2);color:var(--green);}
.btn-green:hover:not(:disabled){background:rgba(0,229,160,.18);}
.btn-red{background:rgba(255,61,90,.08);border-color:#7a1a2a;color:var(--red);}
.btn-red:hover:not(:disabled){background:rgba(255,61,90,.18);}
.btn-ghost{background:transparent;border-color:var(--border2);color:var(--text2);}
.btn-ghost:hover:not(:disabled){border-color:var(--text3);color:var(--text);}
.btn-orange{background:rgba(255,124,42,.08);border-color:#7a4a1a;color:var(--orange);}
.btn-orange:hover:not(:disabled){background:rgba(255,124,42,.18);}
.btn-purple{background:rgba(192,132,252,.08);border-color:#6a3a9a;color:var(--purple);}
.btn-purple:hover:not(:disabled){background:rgba(192,132,252,.18);}
.btn:disabled{opacity:.35;cursor:not-allowed;}
.btn-sm{padding:4px 10px;font-size:10px;}
.spin{width:11px;height:11px;border:2px solid var(--border2);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}
.g4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;}
.mc{background:var(--panel2);border:1px solid var(--border);border-radius:5px;padding:12px;}
.mc-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px;}
.bar{height:3px;background:var(--border);border-radius:2px;margin-top:7px;overflow:hidden;}
.bar-fill{height:100%;border-radius:2px;transition:width .5s;}
.tbl{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;}
.tbl th{text-align:left;padding:6px 11px;font-size:9px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--text3);border-bottom:1px solid var(--border);}
.tbl td{padding:7px 11px;border-bottom:1px solid var(--border);vertical-align:top;color:var(--text);}
.tbl tr:last-child td{border-bottom:none;}
.tbl tr:hover td{background:rgba(0,200,255,.025);}
.bdg{display:inline-flex;align-items:center;font-family:var(--mono);font-size:9px;font-weight:600;letter-spacing:.07em;padding:2px 7px;border-radius:3px;text-transform:uppercase;}
.bdg-critical{background:rgba(255,61,90,.16);color:var(--red);border:1px solid rgba(255,61,90,.3);}
.bdg-high{background:rgba(255,124,42,.14);color:var(--orange);border:1px solid rgba(255,124,42,.28);}
.bdg-medium{background:rgba(245,197,24,.1);color:var(--yellow);border:1px solid rgba(245,197,24,.22);}
.bdg-low{background:rgba(0,229,160,.08);color:var(--green);border:1px solid rgba(0,229,160,.2);}
.bdg-info{background:rgba(0,200,255,.08);color:var(--accent);border:1px solid rgba(0,200,255,.2);}
.bdg-purple{background:rgba(192,132,252,.08);color:var(--purple);border:1px solid rgba(192,132,252,.2);}
.code{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:11px;font-family:var(--mono);font-size:11px;color:#8ecfef;line-height:1.7;white-space:pre-wrap;word-break:break-all;max-height:260px;overflow-y:auto;}
.rbox{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:11px;margin-top:10px;}
.rbox-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px;}
.rbox-val{font-family:var(--mono);font-size:11px;color:var(--text);line-height:1.7;white-space:pre-wrap;}
.inp{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:7px 11px;font-family:var(--mono);font-size:11px;color:var(--text);width:100%;outline:none;transition:border-color .15s;}
.inp:focus{border-color:var(--accent2);}
.inp::placeholder{color:var(--text3);}
.ta{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:9px 11px;font-family:var(--mono);font-size:11px;color:var(--text);width:100%;outline:none;resize:vertical;min-height:90px;line-height:1.6;transition:border-color .15s;}
.ta:focus{border-color:var(--accent2);}
select.inp{cursor:pointer;}
.sf{display:flex;flex-direction:column;gap:7px;}
.si{display:flex;gap:11px;align-items:flex-start;padding:9px 13px;border-radius:5px;border:1px solid var(--border);background:var(--panel2);transition:all .2s;}
.si.active{border-color:var(--accent);background:rgba(0,200,255,.05);}
.si.done{border-color:var(--green2);background:rgba(0,229,160,.04);}
.si-num{font-family:var(--mono);font-size:10px;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid var(--border2);color:var(--text3);}
.si.active .si-num{border-color:var(--accent);color:var(--accent);}
.si.done .si-num{border-color:var(--green);color:var(--green);}
.si-lbl{font-family:var(--cond);font-size:13px;font-weight:600;color:var(--text2);}
.si.active .si-lbl{color:var(--accent);}
.si.done .si-lbl{color:var(--green);}
.si-det{font-family:var(--mono);font-size:10px;color:var(--text3);margin-top:2px;}
.si-out{font-family:var(--mono);font-size:10px;color:var(--text2);margin-top:6px;padding:7px 10px;background:var(--bg);border-radius:3px;line-height:1.6;border-left:2px solid var(--border2);}
.div{border:none;border-top:1px solid var(--border);margin:12px 0;}
.prog{height:5px;background:var(--border);border-radius:3px;overflow:hidden;margin:5px 0;}
.prog-fill{height:100%;border-radius:3px;transition:width .3s;}
.ap{padding:8px 11px;border-radius:4px;margin-bottom:5px;border-left:3px solid;font-family:var(--mono);font-size:10px;line-height:1.6;}
.ap-critical{border-color:var(--red);background:rgba(255,61,90,.05);}
.ap-high{border-color:var(--orange);background:rgba(255,124,42,.05);}
.ap-medium{border-color:var(--yellow);background:rgba(245,197,24,.05);}
.ap-low{border-color:var(--green);background:rgba(0,229,160,.05);}
.acard{border:1px solid var(--border2);border-radius:5px;padding:13px;background:var(--panel2);margin-bottom:10px;}
.acard-action{font-family:var(--cond);font-size:13px;font-weight:700;color:var(--yellow);margin-bottom:3px;}
.acard-target{font-family:var(--mono);font-size:10px;color:var(--text2);margin-bottom:5px;}
.acard-reason{font-family:var(--mono);font-size:10px;color:var(--text3);line-height:1.6;margin-bottom:9px;}
.log-row{display:grid;grid-template-columns:82px 58px 1fr;gap:8px;padding:4px 14px;border-bottom:1px solid var(--border);align-items:start;}
.log-t{font-family:var(--mono);font-size:9px;color:var(--text3);}
.log-l{font-family:var(--mono);font-size:9px;font-weight:600;}
.log-m{font-family:var(--mono);font-size:10px;color:var(--text);line-height:1.5;}
.tc{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:10px;margin-bottom:6px;}
.tc-name{font-family:var(--mono);font-size:10px;font-weight:600;color:var(--green);}
.tc-args{font-family:var(--mono);font-size:10px;color:var(--text2);margin-top:5px;line-height:1.5;}
.tc-result{font-family:var(--mono);font-size:10px;color:var(--accent);margin-top:5px;line-height:1.5;padding-top:5px;border-top:1px solid var(--border);}
.kbr{border:1px solid var(--border);border-radius:4px;padding:11px;margin-bottom:7px;background:var(--panel2);}
.kbr-score{font-family:var(--mono);font-size:9px;color:var(--yellow);}
.kbr-title{font-family:var(--cond);font-size:13px;font-weight:600;color:var(--text);margin:3px 0;}
.kbr-url{font-family:var(--mono);font-size:9px;color:var(--accent2);margin-bottom:5px;}
.kbr-txt{font-family:var(--mono);font-size:10px;color:var(--text2);line-height:1.6;}
.ccard{flex:1;border:1px solid var(--border);border-radius:5px;padding:13px;background:var(--panel2);text-align:center;}
.ccard-amt{font-family:var(--cond);font-size:30px;font-weight:800;line-height:1;}
.ccard-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);margin-top:4px;}
.sim-card{border:1px solid var(--border);border-radius:4px;padding:11px;background:var(--panel2);}
.sim-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);text-transform:uppercase;margin-bottom:7px;}
.sim-row{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;padding:3px 0;}
.schema-item{border:1px solid var(--border);border-radius:4px;padding:11px;margin-bottom:8px;background:var(--panel2);}
.wf-step{border:1px solid var(--border);border-radius:5px;padding:12px;margin-bottom:8px;background:var(--panel2);}
.wf-step.wf-active{border-color:var(--accent);background:rgba(0,200,255,.04);}
.wf-step.wf-done{border-color:var(--green2);background:rgba(0,229,160,.04);}
.wf-step.wf-rejected{border-color:rgba(255,61,90,.4);background:rgba(255,61,90,.04);}
.wf-step-hdr{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.wf-step-lbl{font-family:var(--cond);font-size:13px;font-weight:700;}
/* settings row */
.srow{display:grid;grid-template-columns:260px 1fr 80px;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:10px;}
.srow:last-child{border-bottom:none;}
.srow-key{color:var(--accent);}
.srow-val{color:var(--text2);}
.srow-src{color:var(--text3);font-size:9px;}
/* chunk preview */
.chunk{background:var(--panel2);border:1px solid var(--border);border-radius:4px;padding:9px;margin-bottom:6px;font-family:var(--mono);font-size:10px;color:var(--text2);line-height:1.6;}
.chunk-meta{font-size:9px;color:var(--text3);margin-bottom:4px;}
/* test result */
.test-row{display:grid;grid-template-columns:20px 1fr 60px 60px;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:10px;}
.test-pass{color:var(--green);}
.test-fail{color:var(--red);}
/* docker step */
.docker-step{display:flex;align-items:center;gap:10px;padding:8px 11px;border-radius:4px;border:1px solid var(--border);background:var(--panel2);margin-bottom:6px;font-family:var(--mono);font-size:10px;}
.docker-step.done{border-color:var(--green2);background:rgba(0,229,160,.04);}
.docker-step.active{border-color:var(--accent);background:rgba(0,200,255,.04);}
/* cli cmd */
.cli-cmd{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:11px;margin-bottom:8px;}
.cli-cmd-line{font-family:var(--mono);font-size:11px;color:var(--green);margin-bottom:4px;}
.cli-desc{font-family:var(--mono);font-size:10px;color:var(--text2);margin-bottom:6px;}
.cli-output{font-family:var(--mono);font-size:10px;color:var(--accent);line-height:1.6;border-top:1px solid var(--border);padding-top:7px;margin-top:7px;}
/* webhook */
.webhook-field{display:grid;grid-template-columns:140px 1fr;gap:10px;align-items:center;padding:5px 0;font-family:var(--mono);font-size:10px;border-bottom:1px solid var(--border);}
.webhook-field:last-child{border-bottom:none;}
.webhook-key{color:var(--text3);}
`;

// ── Anthropic API ─────────────────────────────────────────────────────────────
async function callAgent(system, user) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system,
      messages: [{ role: "user", content: user }],
    }),
  });
  const d = await r.json();
  return d.content?.map(b => b.text || "").join("") || "";
}

// ── Shared constants ──────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `You are an expert Elastic SRE Agent. Your goal is to minimize query latency and maximize resource efficiency. When you detect a performance bottleneck via ES|QL, search the documentation for the 'Best Practice' resolution. Propose a configuration change or a re-indexing strategy. Never apply a 'destructive' change without explaining the 'Why' and seeking approval.`;

const TOOL_SCHEMAS = [
  { name:"run_esql_query",          step:"2A", color:"var(--accent)",  params:["query:string","index_pattern:string","time_range_hours:integer"] },
  { name:"search_elastic_docs",     step:"2B", color:"var(--purple)",  params:["query:string","top_k:integer"] },
  { name:"update_index_settings",   step:"2C", color:"var(--orange)",  params:["index_name:string","settings:object","reason:string"] },
  { name:"update_cluster_settings", step:"2C", color:"var(--orange)",  params:["persistent:object","transient:object","reason:string"] },
  { name:"create_index_template",   step:"2C/4A",color:"var(--orange)",params:["template_name:string","index_patterns:array","mappings:object","reason:string"] },
  { name:"trigger_reindex",         step:"2C/4B",color:"var(--yellow)",params:["source_index:string","destination_index:string","query:object","reason:string"] },
  { name:"update_alias",            step:"2C/4C",color:"var(--yellow)",params:["alias_name:string","remove_index:string","add_index:string","reason:string"] },
];

// config/settings.py — all env vars
const ALL_SETTINGS = [
  { key:"ELASTICSEARCH_URL",          val:"https://localhost:9200",          src:".env" },
  { key:"ELASTICSEARCH_API_KEY",      val:"<api_key>",                       src:".env" },
  { key:"ELASTICSEARCH_USERNAME",     val:"elastic",                         src:".env" },
  { key:"ELASTICSEARCH_PASSWORD",     val:"<password>",                      src:".env" },
  { key:"MONITORING_CLUSTER_URL",     val:"https://monitoring.cluster:9200", src:".env" },
  { key:"MONITORING_API_KEY",         val:"<monitoring_key>",                src:".env" },
  { key:"SLOWLOG_INDEX_PATTERN",      val:".ds-elasticsearch.slowlog-*",     src:"settings.py" },
  { key:"NODE_METRICS_INDEX_PATTERN", val:"metrics-elasticsearch.node-*",    src:"settings.py" },
  { key:"INDEX_METADATA_INDEX",       val:"index-metadata",                  src:"settings.py" },
  { key:"REASONING_PROVIDER",         val:"anthropic",                       src:".env" },
  { key:"ANTHROPIC_MODEL",            val:"claude-3-5-sonnet-20241022",      src:"settings.py" },
  { key:"OPENAI_MODEL",               val:"gpt-4o",                          src:"settings.py" },
  { key:"DOCS_VECTOR_INDEX",          val:"./faiss_docs.index",              src:".env" },
  { key:"EMBEDDING_MODEL",            val:"all-MiniLM-L6-v2",                src:"settings.py" },
  { key:"LOOP_INTERVAL_SECONDS",      val:"3600",                            src:".env" },
  { key:"TOP_SLOW_QUERIES_LIMIT",     val:"5",                               src:"settings.py" },
  { key:"APPROVAL_WEBHOOK_URL",       val:"https://hooks.example.com/sre",   src:".env" },
  { key:"APPROVAL_TIMEOUT_SECONDS",   val:"300",                             src:"settings.py" },
  { key:"CLOUD_COST_PER_NODE_MONTHLY",val:"200",                             src:".env" },
  { key:"BILLING_API_KEY",            val:"<billing_key>",                   src:".env" },
  { key:"SIMULATION_ENABLED",         val:"true",                            src:".env" },
  { key:"EPHEMERAL_CLUSTER_URL",      val:"",                                src:".env" },
  { key:"BENCHMARK_ITERATIONS",       val:"10",                              src:"settings.py" },
];

// Telemetry
const genNodes = () => [
  { name:"node-1 (master)", cpu:34, mem:61, heap:55, disk_r:4200, disk_w:1800 },
  { name:"node-2 (data)",   cpu:72, mem:78, heap:82, disk_r:9100, disk_w:5300 },
  { name:"node-3 (data)",   cpu:68, mem:74, heap:77, disk_r:8400, disk_w:4900 },
  { name:"node-4 (ingest)", cpu:41, mem:49, heap:43, disk_r:2100, disk_w:3200 },
];
const genSlowQ = () => [
  { statement:'{"query":{"wildcard":{"user_id":{"value":"kim*"}}},"size":10000}',                         avg_ns:14200000000, count:342 },
  { statement:'{"query":{"regexp":{"log_message":{"value":".*ERROR.*"}}},"aggs":{"by_host":{"terms":{"field":"hostname"}}}}', avg_ns:8700000000, count:189 },
  { statement:'{"query":{"script":{"script":{"source":"doc[\'price\'].value*doc[\'qty\'].value>5000"}}},"size":50000}',        avg_ns:6100000000, count:127 },
  { statement:'{"query":{"wildcard":{"email":{"value":"*@gmail.com"}}},"aggs":{"domains":{"terms":{"field":"email.keyword"}}}}', avg_ns:4800000000, count:445 },
  { statement:'{"query":{"nested":{"path":"events","query":{"nested":{"path":"events.details","query":{"match":{"events.details.status":"failed"}}}}}}}', avg_ns:3200000000, count:201 },
];
const genBreakers = () => [
  { node:"node-2 (data)", used_pct:78.4, used_bytes:2890000000, limit_bytes:3686400000, type:"parent" },
  { node:"node-3 (data)", used_pct:71.2, used_bytes:2624000000, limit_bytes:3686400000, type:"parent" },
  { node:"node-2 (data)", used_pct:62.1, used_bytes:1120000000, limit_bytes:1843200000, type:"fielddata" },
];
const genIndexMeta = () => [
  { index:"logs-2024",   field:"user_id",     type:"keyword", docs:45000000,  size:18000000000, shards:5 },
  { index:"logs-2024",   field:"log_message", type:"text",    docs:45000000,  size:18000000000, shards:5 },
  { index:"events-prod", field:"email",       type:"keyword", docs:12000000,  size:4500000000,  shards:3 },
  { index:"metrics-app", field:"hostname",    type:"keyword", docs:88000000,  size:32000000000, shards:8 },
  { index:"events-prod", field:"payload",     type:"object",  docs:12000000,  size:4500000000,  shards:3 },
];

const fmtNs  = ns => { const ms=ns/1e6; return ms>=1000?`${(ms/1000).toFixed(1)}s`:`${ms.toFixed(0)}ms`; };
const fmtB   = b  => b>=1e12?`${(b/1e12).toFixed(1)}TB`:b>=1e9?`${(b/1e9).toFixed(1)}GB`:b>=1e6?`${(b/1e6).toFixed(1)}MB`:`${(b/1e3).toFixed(0)}KB`;
const trunc  = (s,n) => s.length>n?s.slice(0,n)+"…":s;
const sleep  = ms => new Promise(r=>setTimeout(r,ms));

function Spin() { return <div className="spin"/>; }
function Divider() { return <hr className="div"/>; }

function Clock() {
  const [t,setT] = useState("");
  useEffect(()=>{ const f=()=>setT(new Date().toISOString().replace("T"," ").slice(0,19)+" UTC"); f(); const id=setInterval(f,1000); return()=>clearInterval(id); },[]);
  return <span className="hdr-time">{t}</span>;
}

function useLog() {
  const [logs,setLogs] = useState([]);
  const add = useCallback((msg,lvl="INFO")=>{
    const t=new Date().toISOString().slice(11,19);
    setLogs(p=>[...p.slice(-299),{t,lvl,msg}]);
  },[]);
  return [logs,add];
}

// PANEL: Config Settings

function PanelSettings({ addLog }) {
  const [search,setSearch] = useState("");
  const [edited,setEdited] = useState({});
  const [saved,setSaved]   = useState(false);
  const [analysis,setAn]   = useState("");
  const [loading,setL]     = useState(false);

  const filtered = ALL_SETTINGS.filter(s=>s.key.toLowerCase().includes(search.toLowerCase()));

  function edit(key,val) { setEdited(p=>({...p,[key]:val})); setSaved(false); }

  async function validate() {
    setL(true); setAn("");
    addLog("config/settings.py — validating all env settings","INFO");
    const overrides = Object.entries(edited).map(([k,v])=>`${k}=${v}`).join(", ");
    const r = await callAgent(
      SYSTEM_PROMPT,
      `You are config/settings.py. Validate this configuration for a Self-Optimizing Elastic SRE Agent. Settings: ${ALL_SETTINGS.map(s=>s.key+"="+( edited[s.key]||s.val)).join(", ")}. ${overrides?"Overrides: "+overrides:""} Report: any misconfigured values, missing required fields, and whether SIMULATION_ENABLED=true is safe given the EPHEMERAL_CLUSTER_URL setting. 4-5 lines.`
    );
    setAn(r); setSaved(true); setL(false);
    addLog("config/settings.py — validation complete","INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--text2)"}}>⚙</span> Configuration <span className="pnl-tag">config/settings.py — all env vars</span></div>
        <div style={{display:"flex",gap:7}}>
          <input className="inp" style={{width:180}} placeholder="Search setting…" value={search} onChange={e=>setSearch(e.target.value)}/>
          <button className="btn btn-primary btn-sm" onClick={validate} disabled={loading}>{loading&&<Spin/>} Validate Config</button>
        </div>
      </div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:8}}>
          {ALL_SETTINGS.length} settings — loaded from .env + config/settings.py hardcoded defaults
        </div>
        <div style={{marginBottom:12}}>
          {filtered.map(s=>(
            <div key={s.key} className="srow">
              <span className="srow-key">{s.key}</span>
              <input className="inp" style={{padding:"3px 8px",fontSize:10}}
                value={edited[s.key]!==undefined?edited[s.key]:s.val}
                onChange={e=>edit(s.key,e.target.value)}/>
              <span className="srow-src">{s.src}</span>
            </div>
          ))}
        </div>
        {analysis && (
          <div className="rbox" style={{borderLeft:"3px solid var(--accent)"}}>
            <div className="rbox-lbl">config/settings.py validation result</div>
            <div className="rbox-val">{analysis}</div>
          </div>
        )}
      </div>
    </div>
  );
}

// PANEL: Approval Config 

function PanelApprovalConfig({ addLog }) {
  const [mode,setMode]       = useState("webhook");
  const [webhookUrl,setWh]   = useState("https://hooks.example.com/sre-approvals");
  const [timeout,setTo]      = useState(300);
  const [pollInterval,setPi] = useState(5);
  const [testResult,setTr]   = useState("");
  const [loading,setL]       = useState(false);
  // simulate a pending webhook approval
  const [webhookPayload,setWp] = useState(null);

  async function testApprovalFlow() {
    setL(true); setTr(""); setWp(null);
    addLog(`workflows/approval.py :: request_approval() — mode=${mode}`,"INFO");

    const payload = {
      approval_id: `appr_${Date.now()}`,
      action: "trigger_reindex",
      target: "logs-2024 → logs-2024-optimized",
      reason: "Switching user_id from keyword to wildcard field type to optimize partial-match queries.",
      payload: { source_index:"logs-2024", destination_index:"logs-2024-optimized" },
      expires_at: new Date(Date.now()+timeout*1000).toISOString(),
    };

    if (mode==="webhook") {
      // _webhook_approval() — posts to webhook, polls for decision
      addLog(`workflows/approval.py :: _webhook_approval() — POST ${webhookUrl}`,"INFO");
      setWp(payload);
      addLog(`_webhook_approval() — polling ${webhookUrl}/status every ${pollInterval}s for ${timeout}s`,"INFO");
    } else {
      // _cli_approval() — blocks on stdin
      addLog("workflows/approval.py :: _cli_approval() — blocking on stdin prompt","INFO");
    }

    const r = await callAgent(
      SYSTEM_PROMPT,
      `You are workflows/approval.py request_approval() (Step 2C). Mode="${mode}". ${mode==="webhook"?`_webhook_approval() POSTs to ${webhookUrl} with the approval payload, then polls ${webhookUrl}/status every ${pollInterval}s until approved/rejected or ${timeout}s timeout.`:`_cli_approval() prints the action details to stdout and blocks waiting for user to type 'yes' or 'no'.`} Describe what happens step by step, including how submit_approval_decision() records the result. 4-5 sentences.`
    );
    setTr(r); setL(false);
    addLog(`request_approval() flow described — timeout=${timeout}s`,"INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--yellow)"}}>⚠</span> Approval Flow Config <span className="pnl-tag">workflows/approval.py — _webhook_approval / _cli_approval</span></div>
        <button className="btn btn-orange btn-sm" onClick={testApprovalFlow} disabled={loading}>{loading&&<Spin/>} Test Flow</button>
      </div>
      <div className="pnl-body">
        {/* Approval mode toggle — _webhook_approval vs _cli_approval */}
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>APPROVAL MODE — workflows/approval.py :: request_approval()</div>
        <div className="g2" style={{marginBottom:12}}>
          {["webhook","cli"].map(m=>(
            <div key={m} onClick={()=>setMode(m)} style={{padding:"10px 14px",border:"1px solid",borderRadius:4,cursor:"pointer",borderColor:mode===m?"var(--yellow)":"var(--border)",background:mode===m?"rgba(245,197,24,.05)":"var(--panel2)"}}>
              <div style={{fontFamily:"var(--cond)",fontSize:13,fontWeight:700,color:mode===m?"var(--yellow)":"var(--text2)"}}>
                {m==="webhook"?"_webhook_approval()":"_cli_approval()"}
              </div>
              <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginTop:2}}>
                {m==="webhook"?"POST to webhook URL, poll for decision":"Block stdin, await yes/no prompt"}
              </div>
            </div>
          ))}
        </div>

        {/* _webhook_approval() config — APPROVAL_WEBHOOK_URL */}
        {mode==="webhook" && (
          <div style={{marginBottom:12}}>
            <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>_webhook_approval() CONFIG — APPROVAL_WEBHOOK_URL</div>
            {[["APPROVAL_WEBHOOK_URL",webhookUrl,setWh],["APPROVAL_TIMEOUT_SECONDS",timeout,setTo],["Poll Interval (s)",pollInterval,setPi]].map(([l,v,s])=>(
              <div key={l} className="webhook-field">
                <span className="webhook-key">{l}</span>
                <input className="inp" style={{padding:"3px 8px",fontSize:10}} value={v} onChange={e=>s(e.target.type==="number"?Number(e.target.value):e.target.value)} type={typeof v==="number"?"number":"text"}/>
              </div>
            ))}
            {/* Simulated webhook payload */}
            {webhookPayload && (
              <div className="rbox" style={{marginTop:10}}>
                <div className="rbox-lbl">_webhook_approval() POST payload → {webhookUrl}</div>
                <div className="code" style={{fontSize:10}}>{JSON.stringify(webhookPayload,null,2)}</div>
              </div>
            )}
          </div>
        )}

        {/* _cli_approval() preview */}
        {mode==="cli" && (
          <div className="rbox" style={{marginBottom:12}}>
            <div className="rbox-lbl">_cli_approval() — stdin prompt output</div>
            <div className="code">{`[APPROVAL REQUIRED]
Action:  trigger_reindex
Target:  logs-2024 → logs-2024-optimized
Reason:  Switching user_id to wildcard field type.
Payload: {"source_index":"logs-2024","destination_index":"logs-2024-optimized"}
Approve? [yes/no]: _`}</div>
          </div>
        )}

        {/* submit_approval_decision() */}
        <div className="rbox" style={{marginBottom:10,borderLeft:"3px solid var(--text3)"}}>
          <div className="rbox-lbl">submit_approval_decision() — records operator decision</div>
          <div className="rbox-val">{`def submit_approval_decision(approval_id: str, approved: bool, reason: str = "") -> dict:
    pending = _PENDING_APPROVALS.get(approval_id)
    pending["decision"] = "approved" if approved else "rejected"
    pending["decided_at"] = datetime.now(timezone.utc).isoformat()
    return pending`}</div>
        </div>

        {testResult && (
          <div className="rbox" style={{borderLeft:"3px solid var(--yellow)"}}>
            <div className="rbox-lbl">request_approval() flow — workflows/approval.py</div>
            <div className="rbox-val">{testResult}</div>
          </div>
        )}
      </div>
    </div>
  );
}

// PANEL: Search Pipeline 
function PanelSearchPipeline({ addLog }) {
  const [rawHtml,setRaw]   = useState(`<html><head><title>Wildcard field type | Elasticsearch Guide</title></head><body><h1>Wildcard field type</h1><p>The <code>wildcard</code> field type is optimized for wildcard queries on values with many unique terms. It stores a trigram index alongside the original value.</p><p>Unlike the <code>keyword</code> type, the wildcard type is designed for partial matching using <code>*</code> and <code>?</code> wildcards without the performance penalty of a full shard scan.</p></body></html>`);
  const [chunkSz,setChk]   = useState(200);
  const [overlap,setOvl]   = useState(30);
  const [stripped,setStrip]= useState("");
  const [chunks,setChunks] = useState([]);
  const [embedResult,setEmb]= useState("");
  const [loading,setL]     = useState(false);

  // _strip_html() — tools/search_tool.py
  function stripHtml() {
    addLog("tools/search_tool.py :: _strip_html() — removing HTML tags and extracting text","INFO");
    const text = rawHtml
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi,"")
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi,"")
      .replace(/<[^>]+>/g," ")
      .replace(/\s+/g," ")
      .trim();
    setStrip(text);
    addLog(`_strip_html() — extracted ${text.length} chars from HTML`,"INFO");
  }

  // _split_text() — tools/search_tool.py
  function splitText() {
    if (!stripped) return;
    addLog(`tools/search_tool.py :: _split_text(chunk_size=${chunkSz}, chunk_overlap=${overlap})`,"INFO");
    const result = [];
    let start = 0;
    while (start < stripped.length) {
      const end = Math.min(start + chunkSz, stripped.length);
      result.push({ chunk_idx:result.length, text:stripped.slice(start,end), start_char:start, end_char:end });
      start += chunkSz - overlap;
    }
    setChunks(result);
    addLog(`_split_text() — produced ${result.length} chunks (size=${chunkSz}, overlap=${overlap})`,"INFO");
  }

  // build_docs_index() — embed + add to FAISS
  async function buildIndex() {
    if (!chunks.length) return;
    setL(true); setEmb("");
    addLog("tools/search_tool.py :: build_docs_index() — embedding chunks with all-MiniLM-L6-v2 → FAISS add()","INFO");
    const r = await callAgent(
      SYSTEM_PROMPT,
      `You are tools/search_tool.py build_docs_index() (Step 2B). You just chunked a doc into ${chunks.length} chunks of ~${chunkSz} chars with ${overlap} char overlap. Describe: the SentenceTransformer('all-MiniLM-L6-v2').encode() call, the resulting vector shape (${chunks.length},384), and the faiss.IndexFlatIP.add() call. Then state what search_elastic_docs() will return when queried. 3-4 sentences.`
    );
    setEmb(r); setL(false);
    addLog(`build_docs_index() — ${chunks.length} vectors (dim=384) added to FAISS IndexFlatIP`,"INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--purple)"}}>⬡</span> Search Indexing Pipeline <span className="pnl-tag">tools/search_tool.py — _strip_html / _split_text / build_docs_index</span></div>
      </div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>RAW HTML INPUT — crawl_and_index_elastic_docs() fetches each URL</div>
        <textarea className="ta" value={rawHtml} onChange={e=>setRaw(e.target.value)} style={{minHeight:80,marginBottom:8}}/>
        <button className="btn btn-ghost btn-sm" onClick={stripHtml} style={{marginBottom:10}}>_strip_html()</button>

        {stripped && (
          <>
            <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>_strip_html() OUTPUT — plain text ({stripped.length} chars)</div>
            <div className="code" style={{marginBottom:10,fontSize:10,color:"var(--green)"}}>{stripped}</div>
            <div className="g2" style={{marginBottom:8}}>
              {[["chunk_size",chunkSz,setChk],["chunk_overlap",overlap,setOvl]].map(([l,v,s])=>(
                <div key={l}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:4}}>{l}</div>
                  <input className="inp" type="number" value={v} onChange={e=>s(Number(e.target.value))}/></div>
              ))}
            </div>
            <button className="btn btn-ghost btn-sm" onClick={splitText} style={{marginBottom:10}}>_split_text(chunk_size={chunkSz}, chunk_overlap={overlap})</button>
          </>
        )}

        {chunks.length>0 && (
          <>
            <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>_split_text() OUTPUT — {chunks.length} chunks</div>
            {chunks.map((c,i)=>(
              <div key={i} className="chunk">
                <div className="chunk-meta">chunk {c.chunk_idx} | chars {c.start_char}–{c.end_char}</div>
                {c.text}
              </div>
            ))}
            <button className="btn btn-purple btn-sm" onClick={buildIndex} disabled={loading} style={{marginTop:8}}>
              {loading&&<Spin/>} build_docs_index() — embed + FAISS add()
            </button>
          </>
        )}

        {embedResult && (
          <div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--purple)"}}>
            <div className="rbox-lbl">build_docs_index() — all-MiniLM-L6-v2 → FAISS IndexFlatIP</div>
            <div className="rbox-val">{embedResult}</div>
          </div>
        )}
      </div>
    </div>
  );
}


// PANEL: Docker Provisioning 
function PanelSimulationDocker({ addLog }) {
  const [dockerSteps,setDs] = useState([
    { label:"docker rm -f sre-agent-simulation",          status:"idle", detail:"Remove any existing ephemeral container" },
    { label:"docker run -d elasticsearch:8.13.0",         status:"idle", detail:"single-node, xpack.security=false, -Xms512m -Xmx512m, port 9299" },
    { label:"_wait_for_cluster() — poll /_cluster/health",status:"idle", detail:"Poll every 3s until status=green|yellow, timeout=120s" },
    { label:"_seed_test_data() — bulk index 500 docs",    status:"idle", detail:"Seeds from fetch_slowest_queries() rows for realistic benchmark" },
    { label:"_benchmark_query() — 10 iterations each",    status:"idle", detail:"baseline index + optimized index, measure min/max/avg/p95" },
    { label:"_stop_ephemeral_cluster() — docker rm -f",   status:"idle", detail:"Tear down ephemeral container, release port 9299" },
  ]);
  const [running,setRun]   = useState(false);
  const [report,setRep]    = useState("");
  const [currentStep,setCur]= useState(-1);

  async function provision() {
    setRun(true); setRep(""); setCur(-1);
    setDs(p=>p.map(s=>({...s,status:"idle"})));
    addLog("simulation/ephemeral_cluster.py :: _start_ephemeral_cluster() — Docker provisioning sequence","INFO");

    for (let i=0;i<dockerSteps.length;i++) {
      setCur(i);
      setDs(p=>p.map((s,idx)=>idx===i?{...s,status:"active"}:s));
      addLog(`simulation — ${dockerSteps[i].label}`,"INFO");
      await sleep(i===2?1200:700);
      setDs(p=>p.map((s,idx)=>idx===i?{...s,status:"done"}:s));
    }
    setCur(-1);

    const r = await callAgent(
      SYSTEM_PROMPT,
      `You are simulation/ephemeral_cluster.py. Describe the full Docker ephemeral cluster lifecycle: _start_ephemeral_cluster() launching elasticsearch:8.13.0 on port 9299 with single-node discovery, _wait_for_cluster() health polling, _seed_test_data() bulk indexing 500 docs from slowlog, _benchmark_query() running 10 iterations on baseline and optimized indices, and _stop_ephemeral_cluster() teardown. State the DOCKER_IMAGE, port, and container name constants. 4-5 sentences.`
    );
    setRep(r); setRun(false);
    addLog("simulation — _stop_ephemeral_cluster() — docker rm -f sre-agent-simulation","INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--purple)"}}>◈</span> Docker Cluster Provisioning <span className="pnl-tag">simulation/ephemeral_cluster.py — _start/_wait/_stop</span></div>
        <button className="btn btn-purple btn-sm" onClick={provision} disabled={running}>{running&&<Spin/>} Simulate Lifecycle</button>
      </div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:8}}>
          _DOCKER_IMAGE: docker.elastic.co/elasticsearch/elasticsearch:8.13.0 — _EPHEMERAL_PORT: 9299 — _EPHEMERAL_CONTAINER_NAME: sre-agent-simulation
        </div>
        {dockerSteps.map((s,i)=>(
          <div key={i} className={`docker-step ${s.status}`}>
            <div style={{width:18,height:18,borderRadius:"50%",border:`1px solid ${s.status==="done"?"var(--green)":s.status==="active"?"var(--accent)":"var(--border2)"}`,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
              {s.status==="done"?<span style={{color:"var(--green)",fontSize:10}}>✓</span>:s.status==="active"?<Spin/>:<span style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{i+1}</span>}
            </div>
            <div style={{flex:1}}>
              <div style={{color:s.status==="active"?"var(--accent)":s.status==="done"?"var(--green)":"var(--text2)"}}>{s.label}</div>
              <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{s.detail}</div>
            </div>
          </div>
        ))}
        {report && (
          <div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--purple)"}}>
            <div className="rbox-lbl">simulation/ephemeral_cluster.py — full lifecycle report</div>
            <div className="rbox-val">{report}</div>
          </div>
        )}
      </div>
    </div>
  );
}


// PANEL: fetch_index_metadata() ESQL — tools/esql_tool.py

function PanelFetchIndexMetaQ({ addLog }) {
  const [targetIdx,setTgt] = useState("logs-2024");
  const [result,setRes]    = useState(null);
  const [loading,setL]     = useState(false);

  const generatedQuery = `FROM index-metadata
| WHERE index_name == "${targetIdx}"
| KEEP index_name, field_name, field_type, settings, aliases, shard_count, replica_count, doc_count, store_size_bytes, refreshed_at
| SORT field_name ASC`;

  async function fetch() {
    setL(true); setRes(null);
    addLog(`tools/esql_tool.py :: fetch_index_metadata("${targetIdx}") — querying index-metadata via ES|QL`,"INFO");
    const rows = genIndexMeta().filter(m=>m.index===targetIdx);
    const r = await callAgent(
      SYSTEM_PROMPT,
      `You are tools/esql_tool.py fetch_index_metadata() (Step 1.2). The ES|QL query against index-metadata returned these fields for index "${targetIdx}":\n${rows.map(r=>`field="${r.field}", type="${r.type}", docs=${r.docs.toLocaleString()}, size=${fmtB(r.size)}`).join("\n")}\nDescribe what the agent does with this mapping data next — specifically how diagnosis.py uses _fetch_field_type_from_metadata() to look up field types without hitting the production _mapping API. 3 sentences.`
    );
    setRes({ rows, analysis:r });
    setL(false);
    addLog(`fetch_index_metadata() — returned ${rows.length} field records for ${targetIdx}`,"INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--accent)"}}>▸</span> fetch_index_metadata() ES|QL <span className="pnl-tag">tools/esql_tool.py — Step 1.2</span></div>
        <button className="btn btn-primary btn-sm" onClick={fetch} disabled={loading}>{loading&&<Spin/>} Run</button>
      </div>
      <div className="pnl-body">
        <div className="g2" style={{marginBottom:10}}>
          <div>
            <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>TARGET INDEX</div>
            <select className="inp" value={targetIdx} onChange={e=>setTgt(e.target.value)} style={{fontFamily:"var(--mono)",fontSize:11}}>
              {[...new Set(genIndexMeta().map(m=>m.index))].map(i=><option key={i} value={i}>{i}</option>)}
            </select>
          </div>
        </div>
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>GENERATED ES|QL — fetch_index_metadata()</div>
        <div className="code" style={{marginBottom:10}}>{generatedQuery}</div>
        {result && (
          <>
            <table className="tbl" style={{marginBottom:10}}>
              <thead><tr><th>field_name</th><th>field_type</th><th>doc_count</th><th>store_size</th><th>shards</th></tr></thead>
              <tbody>{result.rows.map((r,i)=>(
                <tr key={i}>
                  <td style={{color:"var(--accent)"}}>{r.field}</td>
                  <td><span className="bdg bdg-info">{r.type}</span></td>
                  <td style={{color:"var(--text2)"}}>{(r.docs/1e6).toFixed(1)}M</td>
                  <td style={{color:"var(--text2)"}}>{fmtB(r.size)}</td>
                  <td style={{color:"var(--text2)"}}>{r.shards}</td>
                </tr>
              ))}</tbody>
            </table>
            <div className="rbox" style={{borderLeft:"3px solid var(--accent)"}}>
              <div className="rbox-lbl">fetch_index_metadata() → diagnosis.py :: _fetch_field_type_from_metadata()</div>
              <div className="rbox-val">{result.analysis}</div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}


// PANEL: build_initial_message() — agent/reasoning.py 
function PanelBuildInitialMsg({ addLog }) {
  const [composed,setComp] = useState("");
  const [agentResp,setAr]  = useState("");
  const [loading,setL]     = useState(false);
  const [hours,setHours]   = useState(1);

  async function build() {
    setL(true); setComp(""); setAr("");
    addLog("agent/reasoning.py :: build_initial_message() — composing context from all telemetry sources","INFO");

    const slowQ = genSlowQ();
    const nodes = genNodes();
    const breakers = genBreakers();
    const diagnosisText = `Diagnosis results:\n[1] Statement: ${trunc(slowQ[0].statement,60)}\n    Avg: ${fmtNs(slowQ[0].avg_ns)} | Count: ${slowQ[0].count} | Severity: HIGH\n    Anti-Patterns: Wildcard on high-cardinality field 'user_id' (~2.4M unique values)\n    Recommended searches: "Optimizing wildcard queries Elasticsearch wildcard field type"`;
    const recommendedSearches = ["Optimizing wildcard queries Elasticsearch wildcard field type","Elasticsearch indices.breaker.total.limit CircuitBreakerException configuration"];

    const msg = `A new optimization cycle has started. Here is the current cluster telemetry:

Slowest queries (last ${hours}h):
${slowQ.map((q,i)=>`[${i+1}] ${fmtNs(q.avg_ns)} avg | ${q.count} executions | ${trunc(q.statement,70)}`).join("\n")}

Node metrics:
${nodes.map(n=>`  ${n.name}: CPU=${n.cpu}%, MEM=${n.mem}%, HEAP=${n.heap}%`).join("\n")}

Circuit breaker stats:
${breakers.map(b=>`  ${b.node} [${b.type}]: ${b.used_pct.toFixed(1)}% used`).join("\n")}

Structural diagnosis (Step 4.2):
${diagnosisText}

Diagnosis-recommended Knowledge Tool queries to run first:
${recommendedSearches.map(s=>`  - "${s}"`).join("\n")}

Using the diagnosis above, run the recommended Knowledge Tool queries to research the best-practice fixes. Then propose an optimization plan (Step A: create template, Step B: reindex, Step C: update alias). Do not apply any destructive change without stating the reason and seeking approval.`;

    setComp(msg);
    addLog(`build_initial_message() — composed ${msg.length} char context message with ${slowQ.length} slow queries, ${nodes.length} nodes, ${breakers.length} breakers, diagnosis, ${recommendedSearches.length} recommended searches`,"INFO");

    const r = await callAgent(SYSTEM_PROMPT, msg);
    setAr(r); setL(false);
    addLog("call_reasoning_model() — initial response received from reasoning model","INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--accent)"}}>✉</span> build_initial_message() <span className="pnl-tag">agent/reasoning.py — Step 4.2 → 4.3 context injection</span></div>
        <div style={{display:"flex",gap:8,alignItems:"center"}}>
          <span style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text3)"}}>hours=</span>
          <input className="inp" type="number" value={hours} onChange={e=>setHours(Number(e.target.value))} style={{width:60,padding:"4px 8px"}}/>
          <button className="btn btn-primary btn-sm" onClick={build} disabled={loading}>{loading&&<Spin/>} Build + Call Model</button>
        </div>
      </div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>
          build_initial_message(context) injects: slow_queries + node_metrics + circuit_breakers + diagnosis + top_recommended_searches — agent/reasoning.py
        </div>
        {composed && (
          <>
            <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>COMPOSED MESSAGE — messages[0].content (user role)</div>
            <div className="code" style={{marginBottom:10,color:"var(--text2)",fontSize:10}}>{composed}</div>
          </>
        )}
        {agentResp && (
          <div className="rbox" style={{borderLeft:"3px solid var(--accent)"}}>
            <div className="rbox-lbl">call_reasoning_model() initial response — SYSTEM_PROMPT + build_initial_message()</div>
            <div className="rbox-val">{agentResp}</div>
          </div>
        )}
      </div>
    </div>
  );
}


// PANEL: CLI Commands — main.py
function PanelCLI({ addLog }) {
  const [outputs,setOuts] = useState({});
  const [loading,setL]   = useState({});

  const commands = [
    { id:"bootstrap", cmd:"python main.py bootstrap", desc:"cmd_bootstrap() — Step 1.1+1.2: enable_stack_monitoring() + verify_required_indices() + refresh_index_metadata()", fn:"cmd_bootstrap" },
    { id:"buildkb",   cmd:"python main.py build-kb --max-urls 2000 --chunk-size 500 --chunk-overlap 50", desc:"cmd_build_kb() — Step 2B: discover_docs_urls() + crawl_and_index_elastic_docs()", fn:"cmd_build_kb" },
    { id:"runcycle",  cmd:"python main.py run-cycle --hours 1", desc:"cmd_run_cycle() — Step 4: run_optimization_cycle(time_range_hours=1)", fn:"cmd_run_cycle" },
    { id:"startloop", cmd:"python main.py start-loop", desc:"cmd_start_loop() — Step 4.1: start_scheduler() with LOOP_INTERVAL_SECONDS", fn:"cmd_start_loop" },
    { id:"indexdocs", cmd:"python main.py index-docs --urls-file docs_urls.txt", desc:"cmd_index_docs() — Step 2B manual: crawl_and_index_elastic_docs() from user-supplied URL file", fn:"cmd_index_docs" },
  ];

  async function runCmd(c) {
    setL(p=>({...p,[c.id]:true})); setOuts(p=>({...p,[c.id]:""}));
    addLog(`main.py :: ${c.fn}() — ${c.cmd}`,"INFO");
    const r = await callAgent(
      SYSTEM_PROMPT,
      `You are main.py ${c.fn}() (CLI entry point). The user ran: "${c.cmd}". Describe the exact sequence of function calls made, the log output that would appear on stdout, and the final result. Use realistic log formatting with timestamps. 5-7 lines.`
    );
    setOuts(p=>({...p,[c.id]:r}));
    setL(p=>({...p,[c.id]:false}));
    addLog(`${c.fn}() complete`,"INFO");
  }

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--green)"}}>$</span> CLI Commands <span className="pnl-tag">main.py — argparse subcommands</span></div>
      </div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:8}}>
          main.py — 5 subcommands mapped to all backend setup and agent entry points
        </div>
        {commands.map(c=>(
          <div key={c.id} className="cli-cmd">
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:4}}>
              <div className="cli-cmd-line">$ {c.cmd}</div>
              <button className="btn btn-green btn-sm" onClick={()=>runCmd(c)} disabled={loading[c.id]}>{loading[c.id]&&<Spin/>} Run</button>
            </div>
            <div className="cli-desc">{c.desc}</div>
            {outputs[c.id] && <div className="cli-output">{outputs[c.id]}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}


// PANEL: Test Runner — tests/ all 11 tests
function PanelTestRunner({ addLog }) {
  const [results,setRes] = useState([]);
  const [running,setRun] = useState(false);
  const [progress,setProg]= useState(0);
  const [summary,setSum] = useState(null);

  const TEST_FILES = [
    { file:"tests/test_esql_tool.py",      module:"tools/esql_tool.py",             tests:["test_build_slowest_queries_esql_shape","test_run_esql_query_returns_columns_rows","test_fetch_node_metrics_fields","test_fetch_circuit_breaker_stats"] },
    { file:"tests/test_search_tool.py",    module:"tools/search_tool.py",            tests:["test_strip_html","test_split_text_chunk_count","test_build_docs_index","test_search_elastic_docs_top_k"] },
    { file:"tests/test_execution_tool.py", module:"tools/execution_tool.py",         tests:["test_update_index_settings_routes_to_approval","test_trigger_reindex_approved","test_trigger_reindex_rejected","test_get_reindex_task_status","test_update_alias","test_create_index_template"] },
    { file:"tests/test_approval.py",       module:"workflows/approval.py",           tests:["test_cli_approval_yes","test_cli_approval_no","test_webhook_approval_posts_payload","test_submit_approval_decision","test_get_pending_approvals"] },
    { file:"tests/test_cost_reasoner.py",  module:"cost/cost_reasoner.py",           tests:["test_reindex_proceeds","test_scale_node_rejected","test_get_billing_data_aws","test_get_current_monthly_node_cost"] },
    { file:"tests/test_reindex_workflow.py",module:"workflows/reindex_workflow.py",  tests:["test_full_workflow_all_approved","test_halt_at_step_a","test_halt_at_step_b","test_halt_at_step_c","test_reindex_timeout"] },
    { file:"tests/test_orchestrator.py",   module:"agent/orchestrator.py",           tests:["test_dispatch_esql","test_dispatch_search","test_dispatch_reindex_cost_gate","test_dispatch_cluster_settings_simulation","test_max_rounds_guard"] },
    { file:"tests/test_reasoning.py",      module:"agent/reasoning.py",              tests:["test_system_prompt_verbatim","test_anthropic_adapter","test_openai_adapter","test_build_initial_message_includes_diagnosis"] },
    { file:"tests/test_diagnosis.py",      module:"agent/diagnosis.py",              tests:["test_detect_wildcard_high_cardinality","test_detect_leading_wildcard","test_detect_circuit_breaker","test_detect_unbounded_agg","test_detect_deep_nesting","test_detect_script","test_detect_regexp","test_compute_severity","test_diagnose_orders_by_severity","test_build_diagnosis_context"] },
    { file:"tests/test_bootstrap.py",      module:"setup/bootstrap.py",              tests:["test_enable_xpack_monitoring","test_enables_slowlog","test_verify_required_indices","test_flatten_mappings_nested","test_refresh_index_metadata_writes_bulk","test_skips_system_indices"] },
    { file:"tests/test_docs_indexer.py",   module:"setup/docs_indexer.py",           tests:["test_discovers_elasticsearch_reference_urls","test_excludes_non_docs_urls","test_deduplicates_urls","test_respects_max_urls_cap","test_build_knowledge_base_calls_crawl"] },
  ];

  async function runAll() {
    setRun(true); setRes([]); setSum(null); setProg(0);
    addLog("pytest tests/ — running all 11 test files","INFO");
    const allResults = [];

    for (let i=0;i<TEST_FILES.length;i++) {
      const tf = TEST_FILES[i];
      setProg(Math.round((i/TEST_FILES.length)*100));
      addLog(`pytest ${tf.file}`,"INFO");
      for (const t of tf.tests) {
        // Each test either passes or has a small random chance to flag WARN
        const passed = Math.random() > 0.05;
        const dur = (Math.random()*0.4+0.05).toFixed(3);
        allResults.push({ file:tf.file, test:t, passed, dur });
        setRes([...allResults]);
        await sleep(60);
      }
    }

    setProg(100);
    const passed = allResults.filter(r=>r.passed).length;
    const failed = allResults.filter(r=>!r.passed).length;

    const sumReport = await callAgent(
      SYSTEM_PROMPT,
      `You are the pytest test runner for the Self-Optimizing Elastic SRE Agent. ${passed} tests passed, ${failed} failed out of ${allResults.length} total across 11 test files. If any failed, describe likely causes related to missing mock patches or ES client fixtures. 2-3 sentences.`
    );
    setSum({ passed, failed, total:allResults.length, report:sumReport });
    addLog(`pytest complete — ${passed} passed, ${failed} failed / ${allResults.length} total`,"INFO");
    setRun(false);
  }

  const lc = { INFO:"var(--accent)", WARN:"var(--yellow)" };

  return (
    <div className="pnl">
      <div className="pnl-hdr">
        <div className="pnl-title"><span style={{color:"var(--green)"}}>✓</span> Test Runner <span className="pnl-tag">tests/ — 11 test files — pytest</span></div>
        <button className="btn btn-green btn-sm" onClick={runAll} disabled={running}>{running&&<Spin/>} pytest tests/</button>
      </div>
      <div className="pnl-body">
        {running && (
          <div style={{marginBottom:10}}>
            <div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text2)",marginBottom:4}}>Running tests… {progress}%</div>
            <div className="prog"><div className="prog-fill" style={{width:`${progress}%`,background:"var(--green)"}}/></div>
          </div>
        )}
        {summary && (
          <div style={{display:"flex",gap:10,marginBottom:10}}>
            {[["PASSED",summary.passed,"var(--green)"],["FAILED",summary.failed,"var(--red)"],["TOTAL",summary.total,"var(--text2)"]].map(([l,v,c])=>(
              <div key={l} className="mc" style={{flex:1}}>
                <div className="mc-lbl">{l}</div>
                <div style={{fontFamily:"var(--cond)",fontSize:24,fontWeight:700,color:c,marginTop:4}}>{v}</div>
              </div>
            ))}
          </div>
        )}
        {results.length>0 && (
          <>
            <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>TEST RESULTS — {results.length} tests</div>
            <div style={{maxHeight:320,overflowY:"auto"}}>
              {TEST_FILES.map(tf=>{
                const tfResults = results.filter(r=>r.file===tf.file);
                if (!tfResults.length) return null;
                return (
                  <div key={tf.file} style={{marginBottom:10}}>
                    <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--accent)",padding:"4px 0",borderBottom:"1px solid var(--border)",marginBottom:4}}>{tf.file} — {tf.module}</div>
                    {tfResults.map((r,i)=>(
                      <div key={i} className="test-row">
                        <span className={r.passed?"test-pass":"test-fail"}>{r.passed?"✓":"✗"}</span>
                        <span style={{color:"var(--text2)",fontSize:10}}>{r.test}</span>
                        <span style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{r.dur}s</span>
                        <span className={`bdg bdg-${r.passed?"low":"critical"}`}>{r.passed?"PASS":"FAIL"}</span>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </>
        )}
        {summary?.report && (
          <div className="rbox" style={{marginTop:10,borderLeft:`3px solid ${summary.failed>0?"var(--red)":"var(--green)"}`}}>
            <div className="rbox-lbl">pytest summary — tests/ agent report</div>
            <div className="rbox-val">{summary.report}</div>
          </div>
        )}
      </div>
    </div>
  );
}


// PanelClusterHealth 
function PanelClusterHealth({ addLog }) {
  const [nodes]       = useState(genNodes);
  const [breakers]    = useState(genBreakers);
  const [idxStatus]   = useState({".ds-elasticsearch.slowlog-*":true,"metrics-elasticsearch.node-*":true,"index-metadata":true});
  const [loading,setL]= useState(false);
  const [bsResult,setBs] = useState(null);
  const [metaRefresh,setMetaR] = useState(null);

  async function runBootstrap() {
    setL(true); setBs(null); setMetaR(null);
    addLog("setup/bootstrap.py :: run_bootstrap() — Step 1.1 + 1.2","INFO");
    addLog("enable_stack_monitoring() — xpack.monitoring.elasticsearch.collection.enabled=true","INFO");
    const monResult = await callAgent(SYSTEM_PROMPT,`You are setup/bootstrap.py enable_stack_monitoring() (Step 1.1). Report the result of enabling xpack Stack Monitoring: slowlog thresholds set (warn=2s,info=1s), xpack.monitoring.elasticsearch.collection.interval=10s, remote exporter configured to monitoring cluster. 4 lines.`);
    addLog("verify_required_indices() — checking all 3 required index patterns","INFO");
    addLog("refresh_index_metadata() — crawling production mappings → bulk indexing to index-metadata","INFO");
    const meta = genIndexMeta();
    const totalFields=meta.length; const totalIndices=[...new Set(meta.map(m=>m.index))].length;
    setMetaR({ indices_indexed:totalIndices, fields_indexed:totalFields, refreshed_at:new Date().toISOString() });
    setBs(monResult); setL(false);
    addLog(`refresh_index_metadata() complete — ${totalIndices} indices, ${totalFields} fields indexed`,"INFO");
  }

  return (
    <div>
      <div className="pnl">
        <div className="pnl-hdr">
          <div className="pnl-title"><span style={{color:"var(--green)"}}>◈</span> Cluster Health &amp; Bootstrap <span className="pnl-tag">setup/bootstrap.py — Step 1.1 / 1.2</span></div>
          <button className="btn btn-primary btn-sm" onClick={runBootstrap} disabled={loading}>{loading&&<Spin/>} run_bootstrap()</button>
        </div>
        <div className="pnl-body">
          <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",letterSpacing:".1em",marginBottom:8}}>NODE METRICS — tools/esql_tool.py :: fetch_node_metrics()</div>
          <div className="g4" style={{marginBottom:12}}>
            {nodes.map(n=>(
              <div key={n.name} className="mc">
                <div className="mc-lbl">{n.name}</div>
                {[["CPU",n.cpu,"var(--accent)"],["MEM",n.mem,"var(--green)"],["HEAP",n.heap,n.heap>75?"var(--red)":"var(--yellow)"]].map(([l,v,c])=>(
                  <div key={l} style={{marginTop:5}}>
                    <div style={{display:"flex",justifyContent:"space-between",fontFamily:"var(--mono)",fontSize:9}}>
                      <span style={{color:"var(--text3)"}}>{l}</span><span style={{color:c}}>{v}%</span>
                    </div>
                    <div className="bar"><div className="bar-fill" style={{width:`${v}%`,background:c}}/></div>
                  </div>
                ))}
                <div style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--text3)",marginTop:6}}>R:{fmtB(n.disk_r*1024)}/s W:{fmtB(n.disk_w*1024)}/s</div>
              </div>
            ))}
          </div>
          <Divider/>
          <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",letterSpacing:".1em",marginBottom:8}}>CIRCUIT BREAKER STATS — tools/esql_tool.py :: fetch_circuit_breaker_stats()</div>
          <table className="tbl" style={{marginBottom:12}}>
            <thead><tr><th>Node</th><th>Type</th><th>Used</th><th>Limit</th><th>%</th><th>Status</th></tr></thead>
            <tbody>{breakers.map((b,i)=>(
              <tr key={i}>
                <td style={{color:"var(--accent)"}}>{b.node}</td>
                <td><span className="bdg bdg-info">{b.type}</span></td>
                <td style={{color:"var(--text2)"}}>{fmtB(b.used_bytes)}</td>
                <td style={{color:"var(--text2)"}}>{fmtB(b.limit_bytes)}</td>
                <td style={{color:b.used_pct>75?"var(--red)":"var(--yellow)",fontWeight:600}}>{b.used_pct.toFixed(1)}%</td>
                <td><span className={`bdg bdg-${b.used_pct>75?"critical":"medium"}`}>{b.used_pct>75?"CRITICAL":"WARN"}</span></td>
              </tr>
            ))}</tbody>
          </table>
          <Divider/>
          <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",letterSpacing:".1em",marginBottom:8}}>REQUIRED INDICES — setup/bootstrap.py :: verify_required_indices() — Step 1.2</div>
          {Object.entries(idxStatus).map(([idx,ok])=>(
            <div key={idx} style={{display:"flex",justifyContent:"space-between",padding:"6px 0",borderBottom:"1px solid var(--border)",fontFamily:"var(--mono)",fontSize:11}}>
              <span style={{color:"var(--accent)"}}>{idx}</span>
              <span style={{color:ok?"var(--green)":"var(--red)"}}>{ok?"✓ PRESENT":"✗ MISSING"}</span>
            </div>
          ))}
          {metaRefresh && (
            <div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--green)"}}>
              <div className="rbox-lbl">refresh_index_metadata() — _create_index_metadata_index() + _flatten_mappings() + bulk write</div>
              <div className="g3" style={{marginTop:6}}>
                {[["Indices Indexed",metaRefresh.indices_indexed,"var(--accent)"],["Fields Indexed",metaRefresh.fields_indexed,"var(--green)"],["Refreshed At",metaRefresh.refreshed_at.slice(0,19),"var(--text2)"]].map(([l,v,c])=>(
                  <div key={l}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{l}</div><div style={{fontFamily:"var(--mono)",fontSize:11,color:c,marginTop:2}}>{v}</div></div>
                ))}
              </div>
            </div>
          )}
          {bsResult && <div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--accent)"}}><div className="rbox-lbl">enable_stack_monitoring() — setup/bootstrap.py Step 1.1</div><div className="rbox-val">{bsResult}</div></div>}
        </div>
      </div>
    </div>
  );
}

// PanelDocsIndexer 
function PanelDocsIndexer({ addLog }) {
  const [loading,setL]=useState(false); const [progress,setPr]=useState(0); const [result,setRes]=useState(null); const [urls,setUrls]=useState([]); const [maxUrls,setMax]=useState(2000); const [chunkSz,setChk]=useState(500); const [overlap,setOvl]=useState(50);
  async function runDiscovery() {
    setL(true); setRes(null); setUrls([]); setPr(0);
    addLog("setup/docs_indexer.py :: discover_docs_urls() — _fetch_xml() parsing elastic.co sitemap index","INFO");
    for(let i=0;i<=60;i+=10){await sleep(200);setPr(i);}
    const discoveredUrls=["https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-wildcard-query.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/circuit-breaker.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-analyze.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-slowlog.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/keyword.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/text.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/wildcard-field-type.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-ngram-tokenizer.html","https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html"];
    setUrls(discoveredUrls);
    addLog(`discover_docs_urls() — _SITEMAP_INDEX_URL parsed, ${discoveredUrls.length} URLs matched _RELEVANT_URL_PREFIXES`,"INFO");
    addLog("setup/docs_indexer.py :: build_knowledge_base() → crawl_and_index_elastic_docs()","INFO");
    for(let i=60;i<=100;i+=10){await sleep(300);setPr(i);}
    const totalChunks=Math.floor(discoveredUrls.length*(chunkSz/50));
    const agentReport=await callAgent(SYSTEM_PROMPT,`You are setup/docs_indexer.py build_knowledge_base() (Step 2B). Crawled ${discoveredUrls.length} Elastic docs pages, split into chunks of ${chunkSz} chars with ${overlap} char overlap, embedded with all-MiniLM-L6-v2, written to FAISS IndexFlatIP dim=384. Report chunk count (~${totalChunks}), index file size, and top SRE-relevant sections covered. 4 lines.`);
    setRes({url_count:discoveredUrls.length,chunk_count:totalChunks,status:"indexed",agentReport}); setL(false);
    addLog(`build_knowledge_base() complete — ${discoveredUrls.length} URLs, ~${totalChunks} chunks`,"INFO");
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--purple)"}}>◎</span> Docs Knowledge Base Indexer <span className="pnl-tag">setup/docs_indexer.py — Step 2B</span></div><button className="btn btn-primary btn-sm" onClick={runDiscovery} disabled={loading}>{loading&&<Spin/>} build_knowledge_base()</button></div>
      <div className="pnl-body">
        <div className="g3" style={{marginBottom:12}}>{[["Max URLs",maxUrls,setMax],["Chunk Size",chunkSz,setChk],["Chunk Overlap",overlap,setOvl]].map(([l,v,s])=>(<div key={l}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>{l}</div><input className="inp" type="number" value={v} onChange={e=>s(Number(e.target.value))}/></div>))}</div>
        {loading&&(<div style={{marginBottom:10}}><div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text2)",marginBottom:4}}>{progress<65?"discover_docs_urls() — _fetch_xml() parsing sitemaps…":"crawl_and_index_elastic_docs() — _strip_html → _split_text → embed…"} {progress}%</div><div className="prog"><div className="prog-fill" style={{width:`${progress}%`,background:"var(--accent)"}}/></div></div>)}
        {urls.length>0&&(<div style={{marginBottom:10}}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>DISCOVERED URLs — _RELEVANT_URL_PREFIXES filter</div>{urls.map((u,i)=>(<div key={i} style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--accent2)",padding:"3px 0",borderBottom:"1px solid var(--border)"}}>{u}</div>))}</div>)}
        {result&&(<><div className="g3" style={{marginBottom:10}}>{[["URLs Crawled",result.url_count,"var(--accent)"],["Chunks Indexed",result.chunk_count,"var(--green)"],["Status",result.status,"var(--yellow)"]].map(([l,v,c])=>(<div key={l} className="mc"><div className="mc-lbl">{l}</div><div style={{fontFamily:"var(--cond)",fontSize:22,fontWeight:700,color:c,marginTop:4}}>{v}</div></div>))}</div><div className="rbox" style={{borderLeft:"3px solid var(--purple)"}}><div className="rbox-lbl">build_knowledge_base() report — setup/docs_indexer.py</div><div className="rbox-val">{result.agentReport}</div></div></>)}
      </div>
    </div>
  );
}

// PanelIndexMeta 
function PanelIndexMeta({ addLog }) {
  const [data]=useState(genIndexMeta); const [sel,setSel]=useState(null); const [analysis,setA]=useState(""); const [loading,setL]=useState(false);
  async function analyze(row) {
    setSel(row.field); setA(""); setL(true);
    addLog(`setup/bootstrap.py :: _flatten_mappings() → diagnosis.py :: _fetch_field_type_from_metadata("${row.index}","${row.field}")`,"INFO");
    const r=await callAgent(SYSTEM_PROMPT,`You are setup/bootstrap.py reading index-metadata (Step 1.2). Field: ${row.field}, type: ${row.type}, index: ${row.index}, docs: ${row.docs.toLocaleString()}, size: ${fmtB(row.size)}, shards: ${row.shards}. Is this field type optimal? What mapping optimization? What _estimate_cardinality() call would the diagnoser make next? 3-4 sentences.`);
    setA(r); setL(false);
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--text2)"}}>⊟</span> Index Metadata Browser <span className="pnl-tag">setup/bootstrap.py :: refresh_index_metadata() → _flatten_mappings()</span></div></div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:8}}>_create_index_metadata_index() mapping → _flatten_mappings() recursion → bulk write → queried by diagnosis.py :: _fetch_field_type_from_metadata()</div>
        <table className="tbl">
          <thead><tr><th>Index</th><th>Field</th><th>Type</th><th>Doc Count</th><th>Store Size</th><th>Shards</th><th>Analyze</th></tr></thead>
          <tbody>{data.map((row,i)=>(<tr key={i}><td style={{color:"var(--accent)"}}>{row.index}</td><td>{row.field}</td><td><span className="bdg bdg-info">{row.type}</span></td><td style={{color:"var(--text2)"}}>{(row.docs/1e6).toFixed(1)}M</td><td style={{color:"var(--text2)"}}>{fmtB(row.size)}</td><td style={{color:"var(--text2)"}}>{row.shards}</td><td><button className="btn btn-ghost btn-sm" onClick={()=>analyze(row)}>Analyze</button></td></tr>))}</tbody>
        </table>
        {(analysis||loading)&&(<div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--accent)"}}><div className="rbox-lbl">_fetch_field_type_from_metadata() + mapping analysis</div>{loading?<div style={{display:"flex",gap:6}}><Spin/><span style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text3)"}}>Analyzing…</span></div>:<div className="rbox-val">{analysis}</div>}</div>)}
      </div>
    </div>
  );
}

// PanelEsql 
function PanelEsql({ addLog }) {
  const [query,setQ]=useState(`FROM .ds-elasticsearch.slowlog-*\n| STATS avg_duration = AVG(event.duration), count = COUNT() BY statement\n| WHERE count > 100\n| SORT avg_duration DESC\n| LIMIT 5`); const [result,setRes]=useState(null); const [analysis,setAn]=useState(""); const [loading,setL]=useState(false); const [generatedQ,setGenQ]=useState("");
  async function runQuery() {
    setL(true); setAn(""); setRes(null);
    addLog("tools/esql_tool.py :: run_esql_query() — executing against monitoring cluster","INFO");
    const genQ=`FROM .ds-elasticsearch.slowlog-*\n| WHERE @timestamp >= "${new Date(Date.now()-3600000).toISOString()}"\n| STATS avg_duration = AVG(event.duration), count = COUNT() BY statement\n| WHERE count > 100\n| SORT avg_duration DESC\n| LIMIT 5`;
    setGenQ(genQ);
    addLog("tools/esql_tool.py :: build_slowest_queries_esql(time_range_hours=1) — @timestamp filter injected","INFO");
    const rows=genSlowQ().map(q=>[(q.avg_ns/1e6).toFixed(0),q.count,q.statement]);
    setRes({columns:["avg_duration_ms","count","statement"],rows});
    const an=await callAgent(SYSTEM_PROMPT,`You are tools/esql_tool.py (Step 2A). ES|QL returned:\n${rows.map((r,i)=>`[${i+1}] ${r[0]}ms | ${r[1]} executions | ${trunc(r[2],80)}`).join("\n")}\nAnalyze anti-patterns. 6 lines max.`);
    setAn(an); setL(false);
    addLog("run_esql_query() complete — 5 slow queries returned","INFO");
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--accent)"}}>▸</span> ES|QL Analytical Tool <span className="pnl-tag">tools/esql_tool.py — Step 2A</span></div><button className="btn btn-primary btn-sm" onClick={runQuery} disabled={loading}>{loading&&<Spin/>} run_esql_query()</button></div>
      <div className="pnl-body">
        {generatedQ&&(<div style={{marginBottom:12}}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>build_slowest_queries_esql(time_range_hours=1) — generated query with @timestamp filter</div><div className="code">{generatedQ}</div></div>)}
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>CUSTOM ES|QL</div>
        <textarea className="ta" value={query} onChange={e=>setQ(e.target.value)} style={{minHeight:110}}/>
        {result&&(<div style={{marginTop:12}}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>RESULTS — fetch_slowest_queries()</div><table className="tbl"><thead><tr>{result.columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{result.rows.map((row,i)=>(<tr key={i}><td style={{color:"var(--red)",whiteSpace:"nowrap"}}>{row[0]}ms</td><td style={{color:"var(--yellow)"}}>{row[1]}</td><td style={{color:"var(--text2)",maxWidth:380,wordBreak:"break-all",fontSize:10}}>{trunc(row[2],110)}</td></tr>))}</tbody></table>{analysis&&<div className="rbox" style={{borderLeft:"3px solid var(--accent)"}}><div className="rbox-lbl">Agent analysis — esql_tool → reasoning.py</div><div className="rbox-val">{analysis}</div></div>}</div>)}
      </div>
    </div>
  );
}

// PanelKnowledge 
function PanelKnowledge({ addLog }) {
  const [q,setQ]=useState("Optimizing wildcard queries Elasticsearch n-grams wildcard field type"); const [res,setRes]=useState(null); const [loading,setL]=useState(false);
  async function search() {
    setL(true); setRes(null);
    addLog(`tools/search_tool.py :: search_elastic_docs("${q}") — FAISS IndexFlatIP cosine similarity`,"INFO");
    const raw=await callAgent(SYSTEM_PROMPT,`You are tools/search_tool.py search_elastic_docs() (Step 2B). FAISS index queried.\nQuery: "${q}"\nReturn ONLY valid JSON array of 3 objects: [{"score":float,"title":"string","url":"realistic elastic.co URL","text":"2-3 sentence doc excerpt"}]`);
    try{const c=raw.replace(/\`\`\`json|\`\`\`/g,"").trim();setRes(JSON.parse(c));addLog(`search_elastic_docs() — ${JSON.parse(c).length} results from FAISS IndexFlatIP`,"INFO");}
    catch{setRes([{score:.91,title:"Result",url:"https://www.elastic.co/guide",text:raw}]);}
    setL(false);
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--purple)"}}>◎</span> Knowledge Tool — Vector Search <span className="pnl-tag">tools/search_tool.py — Step 2B</span></div></div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>search_elastic_docs(query, top_k=5) — FAISS IndexFlatIP — all-MiniLM-L6-v2 dim=384</div>
        <div style={{display:"flex",gap:8,marginBottom:10}}><input className="inp" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&search()} placeholder="Knowledge tool query…"/><button className="btn btn-primary" onClick={search} disabled={loading} style={{whiteSpace:"nowrap"}}>{loading&&<Spin/>} Search</button></div>
        {res?.map((r,i)=>(<div key={i} className="kbr"><div className="kbr-score">similarity: {typeof r.score==="number"?r.score.toFixed(3):"n/a"}</div><div className="kbr-title">{r.title}</div><div className="kbr-url">{r.url}</div><div className="kbr-txt">{r.text}</div></div>))}
      </div>
    </div>
  );
}

// PanelToolSchemas
function PanelToolSchemas({ addLog }) {
  const [selected,setSel]=useState(null); const [agentUse,setAgu]=useState(""); const [loading,setL]=useState(false);
  async function showUsage(tool) {
    setSel(tool.name); setAgu(""); setL(true);
    addLog(`config/tool_schemas.py — _dispatch_tool("${tool.name}") — Step ${tool.step}`,"INFO");
    const r=await callAgent(SYSTEM_PROMPT,`You are agent/orchestrator.py _dispatch_tool(). You selected tool "${tool.name}" (Step ${tool.step}). Show a concrete JSON args example for an Elasticsearch optimization scenario and explain the reasoning. 2-3 sentences.`);
    setAgu(r); setL(false);
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--text2)"}}>⬡</span> Tool Schemas <span className="pnl-tag">config/tool_schemas.py — ALL_TOOL_SCHEMAS</span></div></div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:10}}>{TOOL_SCHEMAS.length} tools registered — implementation example: update_index_settings JSON schema from spec</div>
        {TOOL_SCHEMAS.map(t=>(<div key={t.name} className="schema-item" style={{borderLeft:`3px solid ${t.color}`}}><div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}><div><div style={{fontFamily:"var(--mono)",fontSize:11,fontWeight:600,color:t.color}}>{t.name}</div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>Step {t.step}</div></div><button className="btn btn-ghost btn-sm" onClick={()=>showUsage(t)}>Show Usage</button></div><div style={{display:"flex",flexWrap:"wrap",gap:5}}>{t.params.map(p=>{const[pn,pt]=p.split(":");return<span key={p} style={{fontFamily:"var(--mono)",fontSize:9,padding:"2px 7px",background:"var(--bg)",border:"1px solid var(--border)",borderRadius:3}}><span style={{color:t.color}}>{pn}</span><span style={{color:"var(--text3)"}}>:{pt}</span></span>;})}</div>{selected===t.name&&(agentUse||loading)&&(<div className="rbox" style={{marginTop:8}}><div className="rbox-lbl">_dispatch_tool() usage — agent/orchestrator.py</div>{loading?<div style={{display:"flex",gap:6}}><Spin/><span style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text3)"}}>generating…</span></div>:<div className="rbox-val">{agentUse}</div>}</div>)}</div>))}
      </div>
    </div>
  );
}

// PanelReasoningConfig 
function PanelReasoningConfig({ addLog, provider, setProvider }) {
  const [showPrompt,setShowP]=useState(false); const [testResult,setTestR]=useState(""); const [loading,setL]=useState(false);
  async function testModel() {
    setL(true); setTestR("");
    addLog(`agent/reasoning.py :: call_reasoning_model() — _call_${provider}() — provider=${provider}`,"INFO");
    const r=await callAgent(SYSTEM_PROMPT,`You are agent/reasoning.py (Step 3) using provider="${provider}". Respond as the SRE agent: describe your reasoning approach, what tools you call first, and your decision priority. 3-4 sentences.`);
    setTestR(r); setL(false);
    addLog(`call_reasoning_model() → _call_${provider}() — response received`,"INFO");
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--text2)"}}>⚙</span> Reasoning Model Config <span className="pnl-tag">agent/reasoning.py — Step 3</span></div><button className="btn btn-ghost btn-sm" onClick={testModel} disabled={loading}>{loading&&<Spin/>} Test Model</button></div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:6}}>REASONING_PROVIDER — _call_anthropic() / _call_openai() — config/settings.py</div>
        <div className="g2" style={{marginBottom:12}}>{["anthropic","openai"].map(p=>(<div key={p} onClick={()=>{setProvider(p);addLog(`REASONING_PROVIDER=${p} — agent/reasoning.py`,"INFO");}} style={{padding:"10px 14px",border:"1px solid",borderRadius:4,cursor:"pointer",borderColor:provider===p?"var(--accent)":"var(--border)",background:provider===p?"rgba(0,200,255,.06)":"var(--panel2)",fontFamily:"var(--cond)",fontSize:14,fontWeight:600,color:provider===p?"var(--accent)":"var(--text2)"}}>{p==="anthropic"?"Claude 3.5 Sonnet (_call_anthropic)":"GPT-4o (_call_openai)"}<div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginTop:2}}>{p==="anthropic"?"claude-3-5-sonnet-20241022":"gpt-4o via Open Inference API"}</div></div>))}</div>
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>SYSTEM_PROMPT — agent/reasoning.py</div>
        <div onClick={()=>setShowP(!showPrompt)} style={{cursor:"pointer",fontFamily:"var(--mono)",fontSize:10,color:"var(--accent2)",marginBottom:6}}>{showPrompt?"▼ hide":"▶ show"} system prompt</div>
        {showPrompt&&<div className="code" style={{marginBottom:12}}>{SYSTEM_PROMPT}</div>}
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>build_initial_message() injects: slow_queries + node_metrics + circuit_breakers + diagnosis + top_recommended_searches</div>
        {testResult&&<div className="rbox" style={{borderLeft:"3px solid var(--accent)"}}><div className="rbox-lbl">call_reasoning_model() — provider={provider}</div><div className="rbox-val">{testResult}</div></div>}
      </div>
    </div>
  );
}

// PanelOptimizationLoop
function PanelOptimizationLoop({ addLog, setApprovalQueue }) {
  const [running,setRun]=useState(false); const [step,setStep]=useState(-1); const [outs,setOuts]=useState({}); const [toolCalls,setTc]=useState([]); const [done,setDone]=useState(false);
  const STEPS=[{label:"Identify",detail:"fetch_slowest_queries() + fetch_node_metrics() + fetch_circuit_breaker_stats()",color:"var(--accent)"},{label:"Diagnose",detail:"agent/diagnosis.py :: diagnose_slow_queries() — 6 anti-pattern detectors",color:"var(--yellow)"},{label:"Research",detail:"_dispatch_tool('search_elastic_docs') — FAISS knowledge search",color:"var(--purple)"},{label:"Propose",detail:"call_reasoning_model() — generates Plan A / B / C",color:"var(--orange)"},{label:"Execute",detail:"_dispatch_tool('trigger_reindex') → request_approval() — approval queue",color:"var(--green)"}];
  function addTc(name,step,args,result){setTc(prev=>[...prev,{name,step,args,result}]);}
  async function runCycle() {
    setRun(true); setDone(false); setOuts({}); setTc([]); setStep(-1);
    addLog("agent/orchestrator.py :: run_optimization_cycle(time_range_hours=1)","INFO");
    const queries=genSlowQ(); const nodes=genNodes(); const breakers=genBreakers();
    setStep(0); addLog("Step 4.1 — fetch_slowest_queries() + fetch_node_metrics() + fetch_circuit_breaker_stats()","INFO");
    addTc("run_esql_query","2A",{query:"FROM .ds-elasticsearch.slowlog-* | STATS …",time_range_hours:1},{columns:["avg_duration_ms","count","statement"],rows:queries.map(q=>[(q.avg_ns/1e6).toFixed(0),q.count,trunc(q.statement,40)])});
    setOuts(p=>({...p,0:`${queries.length} slow queries. Worst: ${fmtNs(queries[0].avg_ns)} (${queries[0].count} executions). Breakers: ${breakers[0].used_pct.toFixed(1)}% on ${breakers[0].node}. node-2 heap 82%.`}));
    await sleep(700);
    setStep(1); addLog("Step 4.2 — diagnose_slow_queries() — anti-pattern detection","INFO");
    const diagOut=await callAgent(SYSTEM_PROMPT,`Step 4.2: diagnose_slow_queries() top query: ${queries[0].statement}. State worst anti-pattern, field, severity. 2 sentences.`);
    addTc("run_esql_query","2A",{query:"FROM index-metadata | WHERE index_name == 'logs-2024'",index_pattern:"index-metadata"},{field_type:"keyword",cardinality:2400000});
    setOuts(p=>({...p,1:diagOut})); await sleep(600);
    setStep(2); addLog("Step 4.3 — _dispatch_tool('search_elastic_docs') — FAISS knowledge search","INFO");
    const researchOut=await callAgent(SYSTEM_PROMPT,`Step 4.3: search_elastic_docs("Optimizing wildcard queries Elasticsearch wildcard field type"). Key recommendation from docs. 2-3 sentences.`);
    addTc("search_elastic_docs","2B",{query:"Optimizing wildcard queries wildcard field type",top_k:5},{results:[{score:.94,title:"Wildcard field type"},{score:.89,title:"Analysis with n-grams"}]});
    setOuts(p=>({...p,2:researchOut})); await sleep(600);
    setStep(3); addLog("Step 4.4 — call_reasoning_model() — generating Plan A/B/C","INFO");
    const proposeOut=await callAgent(SYSTEM_PROMPT,`Step 4.4: Generate 3-step plan. A: create_index_template wildcard mapping for logs-2024-optimized. B: trigger_reindex logs-2024 → logs-2024-optimized. C: update_alias logs-current. Specific and technical. 4-5 sentences.`);
    setOuts(p=>({...p,3:proposeOut})); await sleep(500);
    setStep(4); addLog("Step 4.5 — _dispatch_tool('trigger_reindex') → request_approval()","WARN");
    setApprovalQueue(prev=>[...prev,{id:Date.now(),action:"trigger_reindex",target:"logs-2024 → logs-2024-optimized",reason:proposeOut.slice(0,180),payload:{source_index:"logs-2024",destination_index:"logs-2024-optimized"},module:"agent/orchestrator.py"}]);
    addTc("trigger_reindex","4B/4.5",{source_index:"logs-2024",destination_index:"logs-2024-optimized",reason:"Wildcard field optimization"},{status:"approval_pending",approval_id:"appr_"+Date.now()});
    setOuts(p=>({...p,4:"Approval sent to queue — workflows/approval.py :: request_approval(). Cost gate passed ($0 vs $200/mo scaling)."}));
    setStep(5); setDone(true); setRun(false);
    addLog("run_optimization_cycle() complete — status: awaiting_approval","INFO");
  }
  return (
    <div>
      <div className="pnl">
        <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--green)"}}>⟳</span> Optimization Loop — Full Cycle <span className="pnl-tag">agent/orchestrator.py — Step 4</span></div><button className="btn btn-green btn-sm" onClick={runCycle} disabled={running}>{running&&<Spin/>} run_optimization_cycle()</button></div>
        <div className="pnl-body">
          <div className="sf">{STEPS.map((s,i)=>{const st=step>i?"done":step===i?"active":"idle";return(<div key={i} className={`si ${st}`}><div className="si-num">{st==="done"?"✓":st==="active"?<Spin/>:i+1}</div><div style={{flex:1}}><div className="si-lbl" style={st==="active"?{color:s.color}:{}}>{s.label}</div><div className="si-det">{s.detail}</div>{outs[i]&&<div className="si-out">{outs[i]}</div>}</div></div>);})}</div>
          {done&&<div style={{marginTop:10,padding:"9px 13px",borderRadius:4,background:"rgba(0,229,160,.05)",border:"1px solid var(--green2)",fontFamily:"var(--mono)",fontSize:10,color:"var(--green)"}}>Cycle complete — check Approval Queue.</div>}
        </div>
      </div>
      {toolCalls.length>0&&(<div className="pnl"><div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--green)"}}>▸</span> Tool Call Trace <span className="pnl-tag">agent/orchestrator.py :: _dispatch_tool()</span></div></div><div className="pnl-body">{toolCalls.map((tc,i)=>(<div key={i} className="tc"><div style={{display:"flex",alignItems:"center",gap:10}}><div className="tc-name">{tc.name}()</div><span className="bdg bdg-info">Step {tc.step}</span></div><div className="tc-args">args: {JSON.stringify(tc.args,null,0)}</div><div className="tc-result">result: {JSON.stringify(tc.result,null,0)}</div></div>))}</div></div>)}
    </div>
  );
}

// PanelDiagnoser 
function PanelDiagnoser({ addLog }) {
  const [queries]=useState(genSlowQ); const [sel,setSel]=useState(0); const [diag,setD]=useState(null); const [loading,setL]=useState(false); const [cardinality,setCard]=useState(null);
  async function diagnose() {
    setL(true); setD(null); setCard(null);
    addLog("agent/diagnosis.py :: diagnose_slow_queries() — 6 detectors + _estimate_cardinality()","INFO");
    const q=queries[sel];
    // _estimate_cardinality()
    const estCard=Math.floor(Math.random()*3000000+500000);
    addLog(`agent/diagnosis.py :: _estimate_cardinality("${sel===0?"user_id":sel===3?"email":"hostname"}") — cardinality_check agg → ~${estCard.toLocaleString()} unique values`,"INFO");
    setCard({ field:sel===0?"user_id":sel===3?"email":"hostname", estimate:estCard, high:estCard>1000 });
    const raw=await callAgent(SYSTEM_PROMPT,`You are agent/diagnosis.py diagnose_slow_queries() (Step 4.2). Run all 6 detectors (_detect_wildcard_anti_patterns, _detect_circuit_breaker, _detect_unbounded_aggregations, _detect_deep_nesting, _detect_script_queries, _detect_regexp_queries) + _compute_severity() + _estimate_cardinality().\nQuery: ${q.statement}\nAvg: ${fmtNs(q.avg_ns)} | Count: ${q.count} | Estimated cardinality: ${estCard.toLocaleString()}\nReturn ONLY valid JSON: {"antiPatterns":[],"affectedFields":[],"fieldTypes":{},"severity":"critical|high|medium|low","recommendedSearches":[],"explanation":"","detectorsFired":[]}`);
    try{const c=raw.replace(/\`\`\`json|\`\`\`/g,"").trim();setD(JSON.parse(c));addLog(`diagnose_slow_queries() — severity: ${JSON.parse(c).severity}`,"WARN");}
    catch{setD({antiPatterns:[raw],affectedFields:[],fieldTypes:{},severity:"medium",recommendedSearches:[],explanation:raw,detectorsFired:[]});}
    setL(false);
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--yellow)"}}>⬡</span> Query Structure Diagnoser <span className="pnl-tag">agent/diagnosis.py — Step 4.2</span></div><button className="btn btn-primary btn-sm" onClick={diagnose} disabled={loading}>{loading&&<Spin/>} diagnose_slow_queries()</button></div>
      <div className="pnl-body">
        {queries.map((q,i)=>(<div key={i} onClick={()=>setSel(i)} style={{padding:"8px 11px",border:"1px solid",borderRadius:4,cursor:"pointer",marginBottom:5,borderColor:sel===i?"var(--accent)":"var(--border)",background:sel===i?"rgba(0,200,255,.05)":"var(--panel2)"}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}><span style={{fontFamily:"var(--cond)",fontSize:12,color:sel===i?"var(--accent)":"var(--text2)"}}>Query {i+1}</span><span style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--red)"}}>{fmtNs(q.avg_ns)}</span></div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{trunc(q.statement,90)}</div></div>))}
        {/*_estimate_cardinality() result */}
        {cardinality&&(<div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--yellow)"}}><div className="rbox-lbl">_estimate_cardinality() — cardinality aggregation on field "{cardinality.field}"</div><div style={{display:"flex",gap:14,marginTop:4}}><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>Estimated Unique Values</div><div style={{fontFamily:"var(--cond)",fontSize:22,fontWeight:700,color:cardinality.high?"var(--red)":"var(--green)"}}>{cardinality.estimate.toLocaleString()}</div></div><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>High Cardinality</div><div style={{fontFamily:"var(--cond)",fontSize:22,fontWeight:700,color:cardinality.high?"var(--red)":"var(--green)"}}>{cardinality.high?"YES":"NO"}</div></div><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>Threshold</div><div style={{fontFamily:"var(--cond)",fontSize:22,fontWeight:700,color:"var(--text2)"}}>1,000</div></div></div></div>)}
        {diag&&(<div style={{marginTop:12}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:10}}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>DIAGNOSIS — build_diagnosis_context()</div><span className={`bdg bdg-${diag.severity}`}>{diag.severity}</span></div>
          {diag.detectorsFired?.length>0&&(<div style={{marginBottom:8,display:"flex",gap:5,flexWrap:"wrap"}}>{diag.detectorsFired.map(d=><span key={d} className="bdg bdg-purple">{d}</span>)}</div>)}
          {diag.antiPatterns?.map((ap,i)=><div key={i} className={`ap ap-${diag.severity}`}>{ap}</div>)}
          {diag.affectedFields?.length>0&&(<div className="rbox"><div className="rbox-lbl">Affected Fields — _fetch_field_type_from_metadata()</div>{diag.affectedFields.map(f=>(<div key={f} style={{fontFamily:"var(--mono)",fontSize:10,display:"flex",gap:10,padding:"3px 0"}}><span style={{color:"var(--accent)"}}>{f}</span><span style={{color:"var(--text3)"}}>→ {diag.fieldTypes?.[f]||"unknown"}</span></div>))}</div>)}
          {diag.recommendedSearches?.length>0&&(<div className="rbox" style={{marginTop:8}}><div className="rbox-lbl">Recommended Knowledge Tool Queries — Step 4.3</div>{diag.recommendedSearches.map((r,i)=><div key={i} style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--yellow)",padding:"2px 0"}}>→ "{r}"</div>)}</div>)}
          {diag.explanation&&<div className="rbox" style={{marginTop:8,borderLeft:"3px solid var(--yellow)"}}><div className="rbox-lbl">build_diagnosis_context() — explanation</div><div className="rbox-val">{diag.explanation}</div></div>}
        </div>)}
      </div>
    </div>
  );
}

// PanelReindexWorkflow Plan A→B→C
function PanelReindexWorkflow({ addLog, setApprovalQueue }) {
  const [srcIdx,setSrc]=useState("logs-2024"); const [dstIdx,setDst]=useState("logs-2024-optimized"); const [alias,setAlias]=useState("logs-current"); const [tmpl,setTmpl]=useState("logs-optimized-template"); const [running,setRun]=useState(false);
  const [steps,setSteps]=useState([{label:"Plan Step A — create_index_template()",status:"idle",module:"tools/execution_tool.py",detail:"Creates new index template with wildcard field mappings.",output:""},{label:"Plan Step B — trigger_reindex()",status:"idle",module:"tools/execution_tool.py",detail:"Triggers _reindex from source to destination index.",output:""},{label:"Plan Step C — update_alias()",status:"idle",module:"tools/execution_tool.py",detail:"Swaps alias from old index to newly reindexed index.",output:""}]);
  function setStepStatus(i,status,output=""){setSteps(p=>p.map((s,idx)=>idx===i?{...s,status,output}:s));}
  async function runWorkflow() {
    setRun(true); setSteps(p=>p.map(s=>({...s,status:"idle",output:""})));
    addLog("workflows/reindex_workflow.py :: run_reindex_workflow() — Step 4.4 + 4.5","INFO");
    setStepStatus(0,"active"); addLog("Plan Step A — create_index_template() → request_approval()","WARN");
    setApprovalQueue(prev=>[...prev,{id:Date.now(),action:"create_index_template",target:tmpl,reason:`Creating optimized template for ${dstIdx} with wildcard field mappings.`,payload:{template_name:tmpl,index_patterns:[`${dstIdx}*`],mappings:{properties:{user_id:{type:"wildcard"},log_message:{type:"text"}}}},module:"workflows/reindex_workflow.py"}]);
    const outA=await callAgent(SYSTEM_PROMPT,`workflows/reindex_workflow.py Plan A: create_index_template "${tmpl}", index_patterns=["${dstIdx}*"], wildcard mapping for user_id. Approval queued. Describe what the template creates and what optimization it applies. 2-3 sentences.`);
    setStepStatus(0,"done",outA); addLog("Plan Step A — approval queued","INFO");
    setStepStatus(1,"active"); addLog("Plan Step B — trigger_reindex() → request_approval()","WARN");
    setApprovalQueue(prev=>[...prev,{id:Date.now()+1,action:"trigger_reindex",target:`${srcIdx} → ${dstIdx}`,reason:`Reindex to apply wildcard mapping from ${srcIdx} to ${dstIdx}.`,payload:{source_index:srcIdx,destination_index:dstIdx},module:"workflows/reindex_workflow.py"}]);
    const outB=await callAgent(SYSTEM_PROMPT,`workflows/reindex_workflow.py Plan B: trigger_reindex(source="${srcIdx}", destination="${dstIdx}"). Describe the reindex, estimated duration for 45M docs, task polling via get_reindex_task_status(). 2-3 sentences.`);
    setStepStatus(1,"done",outB); addLog("Plan Step B — approval queued","INFO");
    setStepStatus(2,"active"); addLog("Plan Step C — update_alias() → request_approval()","WARN");
    setApprovalQueue(prev=>[...prev,{id:Date.now()+2,action:"update_alias",target:alias,reason:`Swap alias "${alias}" from ${srcIdx} to ${dstIdx}.`,payload:{alias_name:alias,remove_index:srcIdx,add_index:dstIdx},module:"workflows/reindex_workflow.py"}]);
    const outC=await callAgent(SYSTEM_PROMPT,`workflows/reindex_workflow.py Plan C: update_alias(alias="${alias}", remove="${srcIdx}", add="${dstIdx}"). Describe zero-downtime switchover and verification. 2-3 sentences.`);
    setStepStatus(2,"done",outC); addLog("Plan Step C — approval queued — workflow complete","INFO");
    setRun(false);
  }
  const sc={idle:"var(--border2)",active:"var(--accent)",done:"var(--green2)",rejected:"rgba(255,61,90,.4)"};
  const cls={idle:"",active:"wf-active",done:"wf-done",rejected:"wf-rejected"};
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--green)"}}>⟳</span> Reindex Workflow — Plan A→B→C <span className="pnl-tag">workflows/reindex_workflow.py — Step 4.4 / 4.5</span></div><button className="btn btn-green btn-sm" onClick={runWorkflow} disabled={running}>{running&&<Spin/>} run_reindex_workflow()</button></div>
      <div className="pnl-body">
        <div className="g2" style={{marginBottom:8}}>{[["Source Index",srcIdx,setSrc],["Destination Index",dstIdx,setDst],["Alias Name",alias,setAlias],["Template Name",tmpl,setTmpl]].map(([l,v,s])=>(<div key={l}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:4}}>{l}</div><input className="inp" value={v} onChange={e=>s(e.target.value)}/></div>))}</div>
        {steps.map((s,i)=>(<div key={i} className={`wf-step ${cls[s.status]}`}><div className="wf-step-hdr"><div style={{width:22,height:22,borderRadius:"50%",border:`1px solid ${sc[s.status]}`,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>{s.status==="done"?<span style={{color:"var(--green)",fontSize:10}}>✓</span>:s.status==="active"?<Spin/>:<span style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{i+1}</span>}</div><div><div className="wf-step-lbl" style={{color:s.status==="active"?"var(--accent)":s.status==="done"?"var(--green)":"var(--text2)"}}>{s.label}</div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{s.module} — {s.detail}</div></div></div>{s.output&&<div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text2)",padding:"7px 10px",background:"var(--bg)",borderRadius:3,lineHeight:1.6}}>{s.output}</div>}</div>))}
      </div>
    </div>
  );
}

// PanelExecutionTool 
function PanelExecutionTool({ addLog, setApprovalQueue }) {
  const [action,setAct]=useState("update_index_settings"); const [indexName,setIn]=useState("logs-2024"); const [reason,setReason]=useState("Switching user_id field from keyword to wildcard type to optimize partial-match queries."); const [payload,setPay]=useState(`{\n  "mappings": {\n    "properties": {\n      "user_id": { "type": "wildcard" }\n    }\n  }\n}`); const [taskResult,setTr]=useState(null); const [taskId,setTid]=useState(null); const [loading,setL]=useState(false);
  const actions=["update_index_settings","update_cluster_settings","create_index_template","trigger_reindex","update_alias","get_reindex_task_status"];
  async function executeAction() {
    setL(true); setTr(null);
    addLog(`tools/execution_tool.py :: ${action}() → workflows/approval.py :: request_approval()`,"WARN");
    const approvalItem={id:Date.now(),action,target:indexName,reason,payload:(()=>{try{return JSON.parse(payload);}catch{return payload;}})(),module:"tools/execution_tool.py"};
    setApprovalQueue(prev=>[...prev,approvalItem]);
    addLog(`request_approval() — ${action} on ${indexName} — queued for operator decision`,"WARN");
    const result=await callAgent(SYSTEM_PROMPT,`You are tools/execution_tool.py ${action}() (Step 2C). Approval sent to queue. Describe the exact Elasticsearch endpoint that will be called on approval, expected response, and post-action verification. 3-4 sentences.`);
    if(action==="trigger_reindex")setTid(`node-2:task_${Math.floor(Math.random()*999999)}`);
    setTr(result); setL(false);
    addLog(`${action}() — execution blocked — pending approval`,"INFO");
  }
  async function checkTaskStatus() {
    if(!taskId)return;
    addLog(`tools/execution_tool.py :: get_reindex_task_status("${taskId}") — polling /_tasks/${taskId}`,"INFO");
    const r=await callAgent(SYSTEM_PROMPT,`You are tools/execution_tool.py get_reindex_task_status("${taskId}"). Return realistic task status JSON: status, total, created, duration_ms, running. Return ONLY JSON.`);
    addLog(`Task ${taskId} status: ${r.slice(0,80)}`,"INFO");
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--orange)"}}>⚡</span> Execution Tool <span className="pnl-tag">tools/execution_tool.py — Step 2C</span></div><div style={{display:"flex",gap:6}}>{taskId&&<button className="btn btn-ghost btn-sm" onClick={checkTaskStatus}>get_reindex_task_status()</button>}<button className="btn btn-orange btn-sm" onClick={executeAction} disabled={loading}>{loading&&<Spin/>} Execute → Approval</button></div></div>
      <div className="pnl-body">
        <div className="g2" style={{marginBottom:10}}><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>ACTION</div><select className="inp" value={action} onChange={e=>setAct(e.target.value)} style={{fontFamily:"var(--mono)",fontSize:11}}>{actions.map(a=><option key={a} value={a}>{a}()</option>)}</select></div><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>INDEX / TARGET</div><input className="inp" value={indexName} onChange={e=>setIn(e.target.value)}/></div></div>
        <div style={{marginBottom:10}}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>PAYLOAD (JSON)</div><textarea className="ta" value={payload} onChange={e=>setPay(e.target.value)}/></div>
        <div style={{marginBottom:10}}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>REASON — required by all execution tool schemas</div><textarea className="ta" style={{minHeight:50}} value={reason} onChange={e=>setReason(e.target.value)}/></div>
        <div className="rbox" style={{background:"rgba(255,124,42,.04)",borderColor:"rgba(255,124,42,.2)"}}><div className="rbox-lbl" style={{color:"var(--orange)"}}>Safety Guardrail — workflows/approval.py :: request_approval()</div><div className="rbox-val">Every execution_tool.py call routes through request_approval() before hitting any Elasticsearch endpoint. The action is held until the operator decides.</div></div>
        {taskId&&<div className="rbox" style={{marginTop:8}}><div className="rbox-lbl">get_reindex_task_status() — task ID</div><div className="rbox-val" style={{color:"var(--green)"}}>{taskId}</div></div>}
        {taskResult&&<div className="rbox" style={{marginTop:8,borderLeft:"3px solid var(--orange)"}}><div className="rbox-lbl">Execution plan — tools/execution_tool.py</div><div className="rbox-val">{taskResult}</div></div>}
      </div>
    </div>
  );
}

// PanelApproval 
function PanelApproval({ queue, setQueue, addLog }) {
  const [decisions,setDec]=useState({}); const [execResults,setExr]=useState({});
  async function decide(id,approved) {
    addLog(`workflows/approval.py :: submit_approval_decision("${id}", approved=${approved})`,"INFO");
    setDec(p=>({...p,[id]:approved?"approved":"rejected"}));
    const item=queue.find(q=>q.id===id);
    if(approved&&item){
      addLog(`tools/execution_tool.py :: ${item.action}() — executing after approval`,"INFO");
      const r=await callAgent(SYSTEM_PROMPT,`You are tools/execution_tool.py ${item.action}() post-approval (Step 2C). Target: ${item.target}. Describe the Elasticsearch API call, response, and post-action verification. 2-3 sentences.`);
      setExr(p=>({...p,[id]:r}));
    }
  }
  const pending=queue.filter(q=>!decisions[q.id]); const resolved=queue.filter(q=>decisions[q.id]);
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--yellow)"}}>⚠</span> Approval Queue <span className="pnl-tag">workflows/approval.py — Step 2C Safety Guardrail</span></div>{pending.length>0&&<span className="nbadge">{pending.length}</span>}</div>
      <div className="pnl-body">
        {queue.length===0&&<div style={{fontFamily:"var(--mono)",fontSize:11,color:"var(--text3)",textAlign:"center",padding:"20px 0"}}>No pending approvals. Run an optimization cycle or execution tool action.</div>}
        {pending.map(item=>(<div key={item.id} className="acard"><div className="acard-action">{item.action}()</div><div className="acard-target">Target: {item.target} — {item.module}</div><div className="acard-reason">{trunc(item.reason,200)}</div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:8}}>request_approval() — operator decision required before Elasticsearch endpoint is called</div>{item.payload&&<div className="code" style={{marginBottom:8,fontSize:9}}>{JSON.stringify(item.payload,null,2)}</div>}<div style={{display:"flex",gap:7}}><button className="btn btn-green btn-sm" onClick={()=>decide(item.id,true)}>Approve</button><button className="btn btn-red btn-sm" onClick={()=>decide(item.id,false)}>Reject</button></div></div>))}
        {resolved.map(item=>(<div key={item.id} style={{border:"1px solid var(--border)",borderRadius:4,padding:"10px 12px",marginBottom:8,background:"var(--panel2)"}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}><span style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text2)"}}>{item.action}() → {item.target}</span><span className={`bdg bdg-${decisions[item.id]==="approved"?"low":"high"}`}>{decisions[item.id]}</span></div>{execResults[item.id]&&<div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text2)",lineHeight:1.6}}>{execResults[item.id]}</div>}</div>))}
      </div>
    </div>
  );
}

// PanelCostReasoner 
function PanelCostReasoner({ addLog }) {
  const [action,setAct]=useState("reindex"); const [nodeCost,setNc]=useState("200"); const [provider,setPrv]=useState("aws"); const [result,setRes]=useState(null); const [billing,setBill]=useState(null); const [nodeCostResult,setNcr]=useState(null); const [loading,setL]=useState(false);
  const actions=["reindex","query_rewrite","mapping_change","scale_node","new_node"];
  const providers=["aws","gcp","azure"];
  async function evaluate() {
    setL(true); setRes(null); setBill(null); setNcr(null);
    addLog(`cost/cost_reasoner.py :: evaluate_cost_tradeoff("${action}") — Step 5.1`,"INFO");
    // get_current_monthly_node_cost() — distinct from get_billing_data()
    addLog("cost/cost_reasoner.py :: get_current_monthly_node_cost() — reads CLOUD_COST_PER_NODE_MONTHLY from config","INFO");
    const ncResult={source:"config/settings.py::CLOUD_COST_PER_NODE_MONTHLY",value:parseFloat(nodeCost),currency:"USD",note:"Overridable via BILLING_API_KEY by get_billing_data()"};
    setNcr(ncResult);
    // get_billing_data() — calls cloud billing API
    addLog(`cost/cost_reasoner.py :: get_billing_data() — _fetch_${provider}_billing()`,"INFO");
    const billingData={month_to_date_cost:1240.50+Math.random()*200,projected_monthly_cost:parseFloat(nodeCost)*6+800+Math.random()*300,currency:"USD",provider};
    setBill(billingData);
    const costMap={reindex:0,query_rewrite:0,mapping_change:0,scale_node:parseFloat(nodeCost),new_node:parseFloat(nodeCost)};
    const actionCost=costMap[action]||0; const savings=parseFloat(nodeCost)-actionCost; const proceed=actionCost===0;
    const r=await callAgent(SYSTEM_PROMPT,`You are cost/cost_reasoner.py evaluate_cost_tradeoff() (Step 5.1). MTD=$${billingData.month_to_date_cost.toFixed(2)}, projected=$${billingData.projected_monthly_cost.toFixed(2)}/mo. Action="${action}", actionCost=$${actionCost}/mo, scalingCost=$${nodeCost}/mo, savings=$${savings}/mo, proceed=${proceed}. Write reasoning: "Scaling up this node costs $X/mo, but optimizing this query costs $Y. I will prioritize the query fix." 3-4 sentences.`);
    setRes({proceed,actionCost,savings,reasoning:r}); setL(false);
    addLog(`evaluate_cost_tradeoff() — decision: ${proceed?"PROCEED":"REJECT"}, savings: $${savings}/mo`,"INFO");
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--green)"}}>$</span> Cost-Aware Reasoner <span className="pnl-tag">cost/cost_reasoner.py — Step 5.1</span></div><button className="btn btn-primary btn-sm" onClick={evaluate} disabled={loading}>{loading&&<Spin/>} evaluate_cost_tradeoff()</button></div>
      <div className="pnl-body">
        <div className="g3" style={{marginBottom:12}}><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>ACTION</div><select className="inp" value={action} onChange={e=>setAct(e.target.value)} style={{fontFamily:"var(--mono)",fontSize:11}}>{actions.map(a=><option key={a} value={a}>{a}</option>)}</select></div><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>CLOUD_COST_PER_NODE_MONTHLY ($)</div><input className="inp" type="number" value={nodeCost} onChange={e=>setNc(e.target.value)}/></div><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>CLOUD_PROVIDER</div><select className="inp" value={provider} onChange={e=>setPrv(e.target.value)} style={{fontFamily:"var(--mono)",fontSize:11}}>{providers.map(p=><option key={p} value={p}>{p}</option>)}</select></div></div>
        {/*get_current_monthly_node_cost() distinct display */}
        {nodeCostResult&&(<div className="rbox" style={{marginBottom:10,borderLeft:"3px solid var(--text3)"}}><div className="rbox-lbl">get_current_monthly_node_cost() — cost/cost_reasoner.py</div><div style={{display:"flex",gap:20,marginTop:6}}>{[["Source",nodeCostResult.source,"var(--text3)"],["Value","$"+nodeCostResult.value+"/mo","var(--yellow)"],["Currency",nodeCostResult.currency,"var(--text2)"]].map(([l,v,c])=>(<div key={l}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{l}</div><div style={{fontFamily:"var(--mono)",fontSize:11,color:c,marginTop:2}}>{v}</div></div>))}</div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginTop:6}}>{nodeCostResult.note}</div></div>)}
        {billing&&(<div className="rbox" style={{marginBottom:10}}><div className="rbox-lbl">get_billing_data() — _fetch_{provider}_billing() — cost/cost_reasoner.py</div><div className="g3" style={{marginTop:6}}>{[["MTD Cost","$"+billing.month_to_date_cost.toFixed(2),"var(--text)"],["Projected/Mo","$"+billing.projected_monthly_cost.toFixed(2),"var(--yellow)"],["Provider",billing.provider,"var(--text2)"]].map(([l,v,c])=>(<div key={l}><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{l}</div><div style={{fontFamily:"var(--mono)",fontSize:12,color:c,marginTop:2}}>{v}</div></div>))}</div></div>)}
        {result&&(<><div style={{display:"flex",gap:10,marginBottom:10}}>{[["Action Cost/Mo","$"+result.actionCost,"var(--green)"],["Scaling Cost/Mo","$"+nodeCost,"var(--red)"],["Savings/Mo","$"+result.savings,"var(--yellow)"]].map(([l,v,c])=>(<div key={l} className="ccard"><div className="ccard-amt" style={{color:c}}>{v}</div><div className="ccard-lbl">{l}</div></div>))}</div><div className="rbox" style={{borderLeft:`3px solid ${result.proceed?"var(--green)":"var(--red)"}`}}><div className="rbox-lbl">evaluate_cost_tradeoff() reasoning</div><div className="rbox-val">{result.reasoning}</div></div><div style={{marginTop:10,textAlign:"center"}}><span className={`bdg bdg-${result.proceed?"low":"critical"}`} style={{fontSize:11,padding:"4px 14px"}}>{result.proceed?"PROCEED — OPTIMIZATION IS FREE":"REJECT — OPTIMIZE QUERIES FIRST"}</span></div></>)}
      </div>
    </div>
  );
}

// PanelSimulation 
function PanelSimulation({ addLog }) {
  const [simType,setSimType]=useState("mapping"); const [result,setRes]=useState(null); const [progress,setProg]=useState(0); const [loading,setL]=useState(false); const [phase,setPhase]=useState("");
  async function runSim() {
    setL(true); setRes(null); setProg(0); setPhase("");
    addLog(`simulation/ephemeral_cluster.py :: ${simType==="mapping"?"run_simulation":"simulate_cluster_settings_change"}()`,"INFO");
    setPhase("_start_ephemeral_cluster() — docker run elasticsearch:8.13.0 single-node port 9299…");
    for(let i=0;i<=30;i+=5){await sleep(200);setProg(i);}
    addLog("_wait_for_cluster() — polling /_cluster/health until green","INFO");
    setPhase(simType==="mapping"?"_seed_test_data() — bulk 500 docs from fetch_slowest_queries()…":"Seeding 200 test documents…");
    for(let i=30;i<=60;i+=5){await sleep(200);setProg(i);}
    if(simType==="cluster_settings"){setPhase("_benchmark_query() BEFORE cluster.put_settings()…");for(let i=60;i<=75;i+=5){await sleep(200);setProg(i);}setPhase("cluster.put_settings() applying proposed settings…");await sleep(400);setPhase("_benchmark_query() AFTER cluster.put_settings()…");for(let i=75;i<=100;i+=5){await sleep(200);setProg(i);}}
    else{setPhase("_benchmark_query() baseline index (keyword mapping)…");for(let i=60;i<=80;i+=5){await sleep(200);setProg(i);}setPhase("_benchmark_query() optimized index (wildcard field type)…");for(let i=80;i<=100;i+=5){await sleep(200);setProg(i);}}
    const baseline={avg_ms:3400+Math.random()*800,p95_ms:6200+Math.random()*1400,min_ms:1100,max_ms:9200,iterations:10};
    const optimized={avg_ms:baseline.avg_ms*(0.3+Math.random()*0.25),p95_ms:baseline.p95_ms*(0.32+Math.random()*0.28),min_ms:280,max_ms:2400,iterations:10};
    const pct=((baseline.avg_ms-optimized.avg_ms)/baseline.avg_ms*100);
    const fn=simType==="mapping"?"run_simulation":"simulate_cluster_settings_change";
    const agentReport=await callAgent(SYSTEM_PROMPT,`You are simulation/ephemeral_cluster.py ${fn}() (Step 5.2). Ephemeral elasticsearch:8.13.0 single-node benchmarked ${10} iterations.\nBaseline avg: ${baseline.avg_ms.toFixed(0)}ms p95: ${baseline.p95_ms.toFixed(0)}ms. Optimized avg: ${optimized.avg_ms.toFixed(0)}ms p95: ${optimized.p95_ms.toFixed(0)}ms. Improvement: ${pct.toFixed(1)}%. improvement_confirmed=${pct>0}.\nReport: apply to production? What change caused it? 3-4 sentences.`);
    setRes({baseline,optimized,pct:pct.toFixed(1),agentReport,confirmed:pct>0}); setPhase(""); setL(false);
    addLog(`${fn}() complete — ${pct.toFixed(1)}% improvement — improvement_confirmed=${pct>0} — _stop_ephemeral_cluster()`,"INFO");
  }
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--purple)"}}>◈</span> Ephemeral Cluster Simulation <span className="pnl-tag">simulation/ephemeral_cluster.py — Step 5.2</span></div><div style={{display:"flex",gap:8,alignItems:"center"}}>{["mapping","cluster_settings"].map(t=>(<button key={t} className={`btn btn-sm ${simType===t?"btn-primary":"btn-ghost"}`} onClick={()=>setSimType(t)}>{t==="mapping"?"run_simulation()":"simulate_cluster_settings_change()"}</button>))}<button className="btn btn-primary btn-sm" onClick={runSim} disabled={loading}>{loading&&<Spin/>} Run</button></div></div>
      <div className="pnl-body">
        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:8}}>{simType==="mapping"?"run_simulation() — baseline (keyword) vs optimized (wildcard) on ephemeral cluster":"simulate_cluster_settings_change() — _benchmark_query() BEFORE and AFTER cluster.put_settings()"}</div>
        {loading&&(<div style={{marginBottom:12}}><div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text2)",marginBottom:5}}>{phase}</div><div className="prog"><div className="prog-fill" style={{width:`${progress}%`,background:"var(--accent)"}}/></div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginTop:3}}>_DOCKER_IMAGE: elasticsearch:8.13.0 — _EPHEMERAL_PORT: 9299 — BENCHMARK_ITERATIONS: 10</div></div>)}
        {result&&(<><div className="g2" style={{marginBottom:10}}><div className="sim-card"><div className="sim-lbl">{simType==="mapping"?"Baseline (keyword)":"Before settings"}</div>{[["avg",result.baseline.avg_ms],["p95",result.baseline.p95_ms],["min",result.baseline.min_ms],["max",result.baseline.max_ms],["iterations",result.baseline.iterations]].map(([k,v])=>(<div key={k} className="sim-row"><span style={{color:"var(--text3)"}}>{k}</span><span style={{color:"var(--red)"}}>{typeof v==="number"&&v>10?`${v.toFixed(0)}ms`:v}</span></div>))}</div><div className="sim-card"><div className="sim-lbl">{simType==="mapping"?"Optimized (wildcard)":"After settings"}</div>{[["avg",result.optimized.avg_ms],["p95",result.optimized.p95_ms],["min",result.optimized.min_ms],["max",result.optimized.max_ms],["iterations",result.optimized.iterations]].map(([k,v])=>(<div key={k} className="sim-row"><span style={{color:"var(--text3)"}}>{k}</span><span style={{color:"var(--green)"}}>{typeof v==="number"&&v>10?`${v.toFixed(0)}ms`:v}</span></div>))}</div></div><div style={{textAlign:"center",padding:"12px",borderRadius:5,background:result.confirmed?"rgba(0,229,160,.08)":"rgba(255,61,90,.06)",border:`1px solid ${result.confirmed?"var(--green2)":"rgba(255,61,90,.2)"}`,fontFamily:"var(--cond)",fontSize:20,fontWeight:700,color:result.confirmed?"var(--green)":"var(--red)"}}>{result.confirmed?`▼ ${result.pct}% Latency Reduction — improvement_confirmed=True`:`▲ ${Math.abs(result.pct)}% Regression — improvement_confirmed=False`}</div><div className="rbox" style={{marginTop:10,borderLeft:"3px solid var(--purple)"}}><div className="rbox-lbl">{simType==="mapping"?"run_simulation()":"simulate_cluster_settings_change()"} report</div><div className="rbox-val">{result.agentReport}</div></div></>)}
      </div>
    </div>
  );
}

// PanelScheduler 
function PanelScheduler({ addLog }) {
  const [interval,setInt]=useState(3600); const [active,setActive]=useState(false); const [nextRun,setNext]=useState(null); const [runCount,setRc]=useState(0); const [report,setRep]=useState("");
  async function start() {
    setActive(true);
    addLog(`agent/loop.py :: start_scheduler() — LOOP_INTERVAL_SECONDS=${interval}`,"INFO");
    setNext(new Date(Date.now()+interval*1000).toISOString().replace("T"," ").slice(0,19));
    addLog("agent/loop.py :: _cycle_job() — immediate first cycle on startup","INFO");
    setRc(p=>p+1);
    const r=await callAgent(SYSTEM_PROMPT,`You are agent/loop.py _cycle_job() — APScheduler IntervalTrigger every ${interval}s. Report: cycle triggered, orchestrator called, status, next run in ${interval}s. 2-3 lines.`);
    setRep(r); addLog(`_cycle_job() complete — next run in ${interval}s`,"INFO");
  }
  function stop(){setActive(false);setNext(null);addLog("agent/loop.py :: scheduler.shutdown() — optimization loop stopped","WARN");}
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--accent)"}}>⏱</span> Optimization Scheduler <span className="pnl-tag">agent/loop.py — Step 4.1 scheduled</span></div><div style={{display:"flex",gap:7}}>{active?<button className="btn btn-red btn-sm" onClick={stop}>scheduler.shutdown()</button>:<button className="btn btn-green btn-sm" onClick={start}>start_scheduler()</button>}</div></div>
      <div className="pnl-body">
        <div className="g3" style={{marginBottom:12}}><div><div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)",marginBottom:5}}>LOOP_INTERVAL_SECONDS</div><input className="inp" type="number" value={interval} onChange={e=>setInt(Number(e.target.value))} disabled={active}/></div><div className="mc"><div className="mc-lbl">Status</div><div style={{fontFamily:"var(--mono)",fontSize:13,fontWeight:600,color:active?"var(--green)":"var(--text3)",marginTop:5}}>{active?"RUNNING":"STOPPED"}</div></div><div className="mc"><div className="mc-lbl">Cycles Run</div><div style={{fontFamily:"var(--cond)",fontSize:26,fontWeight:700,color:"var(--accent)",marginTop:5}}>{runCount}</div></div></div>
        {nextRun&&(<div className="rbox" style={{marginBottom:10}}><div className="rbox-lbl">Next run — APScheduler IntervalTrigger</div><div className="rbox-val" style={{color:"var(--yellow)"}}>{nextRun} UTC</div></div>)}
        <div className="rbox" style={{marginBottom:10}}><div className="rbox-lbl">start_scheduler() config — agent/loop.py</div><div className="code" style={{fontSize:10}}>{`scheduler.add_job(\n  _cycle_job,\n  trigger=IntervalTrigger(seconds=${interval}),\n  id="optimization_loop",\n  replace_existing=True,\n)`}</div></div>
        {report&&<div className="rbox" style={{borderLeft:"3px solid var(--green)"}}><div className="rbox-lbl">_cycle_job() output</div><div className="rbox-val">{report}</div></div>}
      </div>
    </div>
  );
}

// PanelLog — activity log
function PanelLog({ logs }) {
  const ref=useRef(null);
  useEffect(()=>{if(ref.current)ref.current.scrollTop=ref.current.scrollHeight;},[logs]);
  const lc={INFO:"var(--accent)",WARN:"var(--yellow)",ERROR:"var(--red)",DEBUG:"var(--text3)"};
  return (
    <div className="pnl">
      <div className="pnl-hdr"><div className="pnl-title"><span style={{color:"var(--text3)"}}>≡</span> Agent Activity Log <span className="pnl-tag">orchestrator cycle_log — all modules</span></div><span style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--text3)"}}>{logs.length} entries</span></div>
      <div className="pnl-body" style={{padding:0}}>
        <div ref={ref} style={{maxHeight:380,overflowY:"auto",padding:"4px 0"}}>
          {logs.length===0&&<div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--text3)",padding:"12px 14px"}}>No activity yet.</div>}
          {logs.map((l,i)=>(<div key={i} className="log-row"><span className="log-t">{l.t}</span><span className="log-l" style={{color:lc[l.lvl]||"var(--text2)"}}>{l.lvl}</span><span className="log-m">{l.msg}</span></div>))}
        </div>
      </div>
    </div>
  );
}

// ── NAV ───────────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id:"health",    label:"Cluster Health",        sec:"Stage 1 — FOUNDATIONS",   col:"var(--green)" },
  { id:"docsidx",   label:"Docs KB Indexer",        sec:"Stage 1 — FOUNDATIONS",   col:"var(--purple)" },
  { id:"meta",      label:"Index Metadata",         sec:"Stage 1 — FOUNDATIONS",   col:"var(--text2)" },
  { id:"fetchmeta", label:"fetch_index_metadata()", sec:"Stage 1 — FOUNDATIONS",   col:"var(--accent)" },
  { id:"settings",  label:"Configuration",          sec:"Stage 1 — FOUNDATIONS",   col:"var(--text3)" },
  { id:"esql",      label:"ES|QL Runner",           sec:"Stage 2 — TOOLSET",       col:"var(--accent)" },
  { id:"searchpipe",label:"Search Pipeline",        sec:"Stage 2 — TOOLSET",       col:"var(--purple)" },
  { id:"kb",        label:"Knowledge Search",       sec:"Stage 2 — TOOLSET",       col:"var(--purple)" },
  { id:"tools",     label:"Tool Schemas",           sec:"Stage 2 — TOOLSET",       col:"var(--text2)" },
  { id:"appcfg",    label:"Approval Flow Config",   sec:"Stage 2 — TOOLSET",       col:"var(--yellow)" },
  { id:"reasoning", label:"Reasoning Model",        sec:"Stage 3 — REASONING",     col:"var(--text2)" },
  { id:"initmsg",   label:"build_initial_message()",sec:"Stage 3 — REASONING",     col:"var(--accent)" },
  { id:"loop",      label:"Optimization Loop",      sec:"Stage 4 — LOOP",          col:"var(--green)" },
  { id:"diagnoser", label:"Query Diagnoser",        sec:"Stage 4 — LOOP",          col:"var(--yellow)" },
  { id:"reindex",   label:"Reindex Workflow",       sec:"Stage 4 — LOOP",          col:"var(--green)" },
  { id:"execution", label:"Execution Tool",         sec:"Stage 4 — LOOP",          col:"var(--orange)" },
  { id:"approval",  label:"Approval Queue",         sec:"Stage 4 — LOOP",          col:"var(--yellow)" },
  { id:"cost",      label:"Cost Reasoner",          sec:"Stage 5 — ADVANCED",      col:"var(--green)" },
  { id:"sim",       label:"Simulation",             sec:"Stage 5 — ADVANCED",      col:"var(--purple)" },
  { id:"docker",    label:"Docker Provisioning",    sec:"Stage 5 — ADVANCED",      col:"var(--purple)" },
  { id:"scheduler", label:"Scheduler",              sec:"Stage 5 — ADVANCED",      col:"var(--accent)" },
  // SYSTEM
  { id:"cli",       label:"CLI Commands",           sec:"SYSTEM",                 col:"var(--green)" },
  { id:"tests",     label:"Test Runner",            sec:"SYSTEM",                 col:"var(--green)" },
  { id:"log",       label:"Activity Log",           sec:"SYSTEM",                 col:"var(--text3)" },
];

// ── ROOT 
export default function App() {
  const [active,setActive]  = useState("health");
  const [logs,addLog]       = useLog();
  const [approvalQ,setAppQ] = useState([]);
  const [provider,setProv]  = useState("anthropic");

  const sections=[...new Set(NAV_ITEMS.map(n=>n.sec))];
  const pendingCount=approvalQ.filter(q=>true).length;

  function render() {
    switch(active) {
      case "health":    return <PanelClusterHealth addLog={addLog}/>;
      case "docsidx":   return <PanelDocsIndexer addLog={addLog}/>;
      case "meta":      return <PanelIndexMeta addLog={addLog}/>;
      case "fetchmeta": return <PanelFetchIndexMetaQ addLog={addLog}/>;
      case "settings":  return <PanelSettings addLog={addLog}/>;
      case "esql":      return <PanelEsql addLog={addLog}/>;
      case "searchpipe":return <PanelSearchPipeline addLog={addLog}/>;
      case "kb":        return <PanelKnowledge addLog={addLog}/>;
      case "tools":     return <PanelToolSchemas addLog={addLog}/>;
      case "appcfg":    return <PanelApprovalConfig addLog={addLog}/>;
      case "reasoning": return <PanelReasoningConfig addLog={addLog} provider={provider} setProvider={setProv}/>;
      case "initmsg":   return <PanelBuildInitialMsg addLog={addLog}/>;
      case "loop":      return <PanelOptimizationLoop addLog={addLog} setApprovalQueue={setAppQ}/>;
      case "diagnoser": return <PanelDiagnoser addLog={addLog}/>;
      case "reindex":   return <PanelReindexWorkflow addLog={addLog} setApprovalQueue={setAppQ}/>;
      case "execution": return <PanelExecutionTool addLog={addLog} setApprovalQueue={setAppQ}/>;
      case "approval":  return <PanelApproval queue={approvalQ} setQueue={setAppQ} addLog={addLog}/>;
      case "cost":      return <PanelCostReasoner addLog={addLog}/>;
      case "sim":       return <PanelSimulation addLog={addLog}/>;
      case "docker":    return <PanelSimulationDocker addLog={addLog}/>;
      case "scheduler": return <PanelScheduler addLog={addLog}/>;
      case "cli":       return <PanelCLI addLog={addLog}/>;
      case "tests":     return <PanelTestRunner addLog={addLog}/>;
      case "log":       return <PanelLog logs={logs}/>;
      default:          return null;
    }
  }

  return (
    <>
      <style>{STYLE}</style>
      <div className="scanline"/>
      <div className="app">
        <header className="hdr">
          <div className="hdr-logo">
            <div className="hdr-hex"/>
            <div>
              <div className="hdr-title">ELASTIC SRE AGENT</div>
              <div className="hdr-sub">Self-Optimizing Infra Intelligence — {NAV_ITEMS.length} panels — all backend modules active</div>
            </div>
          </div>
          <div className="hdr-meta">
            <div className="hdr-pill"><div className="dot dot-green"/><span>Cluster Online</span></div>
            <div className="hdr-pill"><div className="dot dot-yellow"/><span>{pendingCount} Approval{pendingCount!==1?"s":""}</span></div>
            <div className="hdr-pill"><span style={{color:"var(--text3)"}}>provider:</span><span style={{color:"var(--accent)"}}>{provider}</span></div>
            <Clock/>
          </div>
        </header>

        <nav className="sidebar">
          {sections.map(sec=>(
            <div key={sec}>
              <div className="sb-sec">{sec}</div>
              {NAV_ITEMS.filter(n=>n.sec===sec).map(n=>(
                <div key={n.id} className={`nav ${active===n.id?"on":""}`} onClick={()=>setActive(n.id)}>
                  <div className="nav-ico" style={{background:n.col}}/>
                  {n.label}
                  {n.id==="approval"&&pendingCount>0&&<span className="nbadge">{pendingCount}</span>}
                </div>
              ))}
            </div>
          ))}
        </nav>

        <main className="main">{render()}</main>
      </div>
    </>
  );
}