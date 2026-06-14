"""HTML/CSS/JS template constants for the HTML output."""

HTML_OPENING = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>repo-notes: {title}</title>
{css}
</head>
<body>
<div class="topbar">
<button class="sidebar-toggle" onclick="toggleSidebar()" aria-label="Toggle sidebar">&#9776;</button>
<span class="topbar-title">repo-notes: {title}</span>
<input class="search" id="search" placeholder="Search sections..." oninput="filterSections(this.value)">
<button class="theme-toggle" onclick="toggleTheme()" id="themeBtn" aria-label="Toggle theme">&#9790;</button>
</div>
<div class="layout">
<div class="backdrop" id="backdrop" onclick="toggleSidebar()"></div>
<nav class="sidebar" id="sidebar">
<ul>{sidebar}</ul>
</nav>
<main class="content" id="content">
{badges}"""

HTML_CLOSING = """</main>
</div>
{js}
</body>
</html>"""

HTML_WRAPPER = HTML_OPENING + "\n{sections}\n" + HTML_CLOSING

SIDEBAR_ITEM = '<li><a href="#section-{id}" class="sidebar-link" data-section="{id}">{icon} {label}</a></li>'

BADGES_HTML = '<div class="badges" id="section-badges">{badges}</div>'

SECTION_WRAPPER = """
<section class="section section-{id}" id="section-{id}">
<h2 class="section-title">{icon} {title}</h2>
{content}
</section>"""


CSS = """<style>
:root {
--bg: #ffffff;
--bg-secondary: #f6f8fa;
--text: #1f2328;
--text-secondary: #656d76;
--border: #d0d7de;
--accent: #0969da;
--accent-hover: #0550ae;
--sidebar-bg: #f6f8fa;
--card-bg: #ffffff;
--warning-bg: #fff8c5;
--danger-bg: #ffebe9;
--success: #1a7f37;
--danger: #cf222e;
--warning: #9a6700;
--shadow: 0 1px 3px rgba(0,0,0,0.08);
--shadow-hover: 0 4px 12px rgba(0,0,0,0.12);
}
.dark {
--bg: #0d1117;
--bg-secondary: #161b22;
--text: #e6edf3;
--text-secondary: #8b949e;
--border: #30363d;
--accent: #58a6ff;
--accent-hover: #79c0ff;
--sidebar-bg: #161b22;
--card-bg: #161b22;
--warning-bg: #3a2d00;
--danger-bg: #3d1414;
--shadow: 0 1px 3px rgba(0,0,0,0.3);
--shadow-hover: 0 4px 12px rgba(0,0,0,0.4);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif;font-size:14px;line-height:1.6;color:var(--text);background:var(--bg);transition:background 0.3s,color 0.3s}
.topbar{position:sticky;top:0;z-index:100;display:flex;align-items:center;gap:12px;padding:8px 16px;background:var(--bg);border-bottom:1px solid var(--border);height:48px;transition:background 0.3s,border 0.3s}
.sidebar-toggle{background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);padding:4px 8px;border-radius:6px;transition:background 0.15s,transform 0.15s}
.sidebar-toggle:hover{background:var(--bg-secondary);transform:scale(1.1)}
.sidebar-toggle:active{transform:scale(0.95)}
.topbar-title{font-weight:600;font-size:15px;flex-shrink:0}
.search{flex:1;max-width:360px;padding:6px 12px;border:1px solid var(--border);border-radius:6px;font-size:13px;background:var(--bg-secondary);color:var(--text);transition:border-color 0.2s,box-shadow 0.2s}
.search:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(9,105,218,0.15)}
.dark .search:focus{box-shadow:0 0 0 3px rgba(88,166,255,0.15)}
.theme-toggle{background:none;border:1px solid var(--border);border-radius:6px;cursor:pointer;font-size:16px;padding:4px 8px;color:var(--text);transition:all 0.2s}
.theme-toggle:hover{background:var(--bg-secondary);transform:rotate(15deg)}
.layout{display:flex;min-height:calc(100vh - 48px);position:relative}
.backdrop{position:fixed;inset:0;top:48px;background:rgba(0,0,0,0.3);z-index:98;opacity:0;pointer-events:none;transition:opacity 0.25s ease}
.backdrop.show{opacity:1;pointer-events:auto}
.sidebar{position:fixed;left:0;top:48px;height:calc(100vh - 48px);width:240px;z-index:99;background:var(--sidebar-bg);transform:translateX(-100%);transition:transform 0.25s cubic-bezier(0.4,0,0.2,1);border-right:1px solid var(--border);overflow-y:auto;padding:16px 0}
.sidebar.open{transform:translateX(0)}
.sidebar ul{list-style:none;padding:0}
.sidebar-link{display:block;padding:8px 20px;color:var(--text-secondary);text-decoration:none;font-size:13px;border-left:3px solid transparent;transition:all 0.15s}
.sidebar-link:hover{color:var(--text);background:var(--bg);padding-left:24px}
.sidebar-link.active{color:var(--accent);border-left-color:var(--accent);font-weight:500;background:var(--bg)}
.content{flex:1;padding:24px 32px;max-width:960px;margin-left:0;transition:margin-left 0.25s cubic-bezier(0.4,0,0.2,1)}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.section{animation:fadeIn 0.4s ease both;margin-bottom:32px;scroll-margin-top:56px}
.section-title{font-size:20px;font-weight:600;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border);transition:border 0.3s}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;animation:fadeIn 0.4s ease both;animation-delay:0.05s}
.badge{display:inline-block;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:500;background:var(--bg-secondary);border:1px solid var(--border);color:var(--text);transition:background 0.2s,border 0.2s}
.badge-success{background:#dafbe1;border-color:#1a7f37;color:#1a7f37}
.dark .badge-success{background:#1a3d2a;border-color:#3fb950;color:#3fb950}
.badge-danger{background:#ffebe9;border-color:#cf222e;color:#cf222e}
.dark .badge-danger{background:#3d1414;border-color:#ff7b72;color:#ff7b72}
.badge-warning{background:#fff8c5;border-color:#9a6700;color:#9a6700}
.dark .badge-warning{background:#3a2d00;border-color:#d29922;color:#d29922}
.tree{font-family:'Cascadia Code','Fira Code','JetBrains Mono',monospace;font-size:13px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.tb{display:flex;gap:6px;padding:8px 12px;border-bottom:1px solid var(--border);background:var(--bg);flex-wrap:wrap}
.tbtn{padding:3px 10px;border:1px solid var(--border);border-radius:5px;font-size:11px;cursor:pointer;background:var(--bg-secondary);color:var(--text);font-family:inherit;transition:background .1s}
.tbtn:hover{background:var(--border)}
.tsrc{flex:1;min-width:120px;padding:4px 8px;border:1px solid var(--border);border-radius:5px;font-size:11px;font-family:inherit;background:var(--bg-secondary);color:var(--text);outline:none}
.tsrc:focus{border-color:var(--accent)}
.tscroll{padding:6px 0;max-height:500px;overflow-y:auto}
.tscroll ul{list-style:none;padding-left:20px;margin:0;position:relative}
.tscroll>ul{padding-left:0}
.tscroll li{position:relative;padding:1px 0}
.th{display:inline-flex;align-items:center;gap:3px;cursor:pointer;border-radius:3px;padding:1px 4px 1px 0;user-select:none}
.th:hover{background:var(--bg)}
.tt{display:inline-block;width:12px;text-align:center;font-size:8px;color:var(--text-secondary);transition:transform .12s;line-height:1;flex-shrink:0}
.tf.collapsed>.th>.tt{transform:rotate(-90deg)}
.tf.collapsed>ul{display:none!important}
.ti{flex-shrink:0;font-size:13px}
.tn{font-size:13px;color:var(--text)}
.td{color:var(--accent);font-weight:500}
.fcount{color:var(--text-secondary);font-size:12px;padding:6px 12px;border-top:1px solid var(--border);background:var(--bg)}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px}
.stat-card{padding:16px;background:var(--card-bg);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow);transition:transform 0.2s,box-shadow 0.2s}
.stat-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-hover)}
.stat-card .stat-value{font-size:24px;font-weight:600;color:var(--accent)}
.stat-card .stat-label{font-size:12px;color:var(--text-secondary);margin-top:4px}
.lang-bar{margin:4px 0;display:flex;align-items:center;gap:8px}
.lang-bar .bar{flex:1;height:8px;background:var(--bg-secondary);border-radius:4px;overflow:hidden}
.lang-bar .bar-fill{height:100%;border-radius:4px;background:var(--accent);transition:width 0.6s ease}
.table-wrap{overflow-x:auto;margin:8px 0}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--border);transition:background 0.15s}
th{background:var(--bg-secondary);font-weight:600;cursor:pointer;user-select:none;position:relative}
th:hover{background:var(--bg-secondary)}
th.sort-asc::after{content:' \\25B2';font-size:10px}
th.sort-desc::after{content:' \\25BC';font-size:10px}
tr:hover td{background:var(--bg-secondary)}
.collapse summary{cursor:pointer;font-weight:500;padding:8px 0;color:var(--accent);transition:color 0.2s}
.collapse summary:hover{color:var(--accent-hover)}
.collapse[open]{margin-bottom:8px}
.file-list{list-style:none;padding:0}
.file-list li{padding:4px 0;font-size:13px;font-family:monospace;display:flex;align-items:center;gap:6px}
.file-icon{flex-shrink:0;font-size:12px}
.layer-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.layer-card{padding:12px 16px;background:var(--card-bg);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow);transition:transform 0.2s,box-shadow 0.2s}
.layer-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-hover)}
.layer-card h4{font-size:14px;margin-bottom:4px}
.layer-card .file-count{font-size:12px;color:var(--text-secondary);margin-bottom:6px}
.entry-points{display:flex;flex-wrap:wrap;gap:8px}
.entry-point{padding:4px 10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:6px;font-family:monospace;font-size:12px;transition:background 0.2s,border 0.2s}
.entry-point:hover{background:var(--card-bg);border-color:var(--accent)}
.commit-list{list-style:none;padding:0}
.commit-item{padding:10px 14px;border-left:3px solid var(--accent);margin-bottom:6px;background:var(--bg-secondary);border-radius:0 8px 8px 0;transition:background 0.2s}
.commit-item:hover{background:var(--card-bg)}
.commit-item .commit-msg{font-weight:500;font-size:13px}
.commit-item .commit-meta{font-size:12px;color:var(--text-secondary);margin-top:3px}
.alert{padding:12px 16px;border-radius:8px;margin:8px 0;border:1px solid;transition:background 0.2s,border 0.2s}
.alert-warning{background:var(--warning-bg);border-color:var(--warning)}
.alert-danger{background:var(--danger-bg);border-color:var(--danger)}
.see-more summary{cursor:pointer;font-weight:500;padding:6px 0;color:var(--text-secondary);font-size:13px;transition:color 0.2s}
.see-more summary:hover{color:var(--accent)}
.hidden{display:none!important}
@media(max-width:768px){
.content{padding:16px}
.stats-grid{grid-template-columns:repeat(2,1fr)}
}
@media print{
.topbar,.sidebar,.search,.theme-toggle,.sidebar-toggle,.backdrop{display:none!important}
.layout{display:block}
.content{max-width:100%;padding:0}
.section{animation:none}
}
</style>"""


JS = """<script>
function toggleTheme(){const t=document.body;t.classList.toggle('dark');const d=t.classList.contains('dark');localStorage.setItem('rn-theme',d?'dark':'light')}
function toggleSidebar(){const s=document.getElementById('sidebar'),b=document.getElementById('backdrop');s.classList.toggle('open');b.classList.toggle('show')}
function filterSections(q){const v=q.toLowerCase();document.querySelectorAll('.section').forEach(s=>{s.classList.toggle('hidden',v&&!s.textContent.toLowerCase().includes(v))});document.querySelectorAll('.sidebar-link').forEach(l=>{const s=document.getElementById('section-'+l.dataset.section);l.style.opacity=s&&!s.classList.contains('hidden')?'1':'0.3'})}
function toggleTreeFolder(e){e.parentElement.classList.toggle('collapsed')}
function collapseAll(){document.querySelectorAll('.tf').forEach(f=>f.classList.add('collapsed'))}
function expandAll(){document.querySelectorAll('.tf').forEach(f=>f.classList.remove('collapsed'))}
function filterTree(i){const q=i.value.toLowerCase().trim(),s=i.closest('.tree').querySelector('.tscroll');if(!q){s.querySelectorAll('li').forEach(l=>l.hidden=false);return}
s.querySelectorAll('li').forEach(l=>l.hidden=true);s.querySelectorAll('.tn').forEach(n=>{if(n.textContent.toLowerCase().includes(q)){let p=n.closest('li');while(p&&p.closest('.tscroll')){p.hidden=false;if(p.classList.contains('tf'))p.classList.remove('collapsed');p=p.parentElement?p.parentElement.closest('li'):null}}}})
document.addEventListener('DOMContentLoaded',function(){
if(localStorage.getItem('rn-theme')==='dark'){document.body.classList.add('dark')}
const sections=document.querySelectorAll('.section');
sections.forEach((s,i)=>{s.style.animationDelay=(0.05*i+0.1)+'s'});
const o=new IntersectionObserver(e=>{e.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('.sidebar-link').forEach(l=>l.classList.toggle('active',l.dataset.section===e.target.id.replace('section-','')))}})},{rootMargin:'-56px 0px -80% 0px'});
sections.forEach(s=>o.observe(s));
document.querySelectorAll('th').forEach(th=>{th.addEventListener('click',function(){const t=this.closest('table'),i=Array.from(this.parentElement.children).indexOf(this),d=this.classList.contains('sort-asc')?-1:1;Array.from(t.querySelectorAll('tbody tr')).sort((a,b)=>d*a.children[i].textContent.localeCompare(b.children[i].textContent)).forEach(r=>t.querySelector('tbody').appendChild(r));this.closest('table').querySelectorAll('th').forEach(h=>h.classList.remove('sort-asc','sort-desc'));this.classList.add(d===1?'sort-asc':'sort-desc')})});
document.querySelectorAll('.sidebar-link').forEach(l=>{l.addEventListener('click',function(){const w=window.innerWidth;if(w<769){document.getElementById('sidebar').classList.remove('open');document.getElementById('backdrop').classList.remove('show')}})});
});
</script>"""