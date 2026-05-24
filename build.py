#!/usr/bin/env python3
"""
Play Archive — 정적 HTML 빌드 스크립트
================================================================
_games/*.md 파일을 읽어 정적 HTML 사이트를 빌드합니다.
출력: docs/index.html + docs/games/<slug>.html + docs/assets/...

사용법:
    python3 build.py

GitHub Pages 설정:
    Settings → Pages → Source: Deploy from a branch
    Branch: main / Folder: /docs
"""
import os
import re
import shutil
import yaml
import markdown
from pathlib import Path
from html import escape

# ----- 경로 -----
ROOT = Path(__file__).parent
GAMES_DIR = ROOT / "_games"
ASSETS_DIR = ROOT / "assets"
OUT_DIR = ROOT / "docs"
OUT_GAMES = OUT_DIR / "games"
OUT_ASSETS = OUT_DIR / "assets"

# ----- 설정 로드 -----
def load_config():
    with open(ROOT / "_config.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----- Markdown front matter 파서 -----
def parse_md(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1]) or {}
            body = parts[2].lstrip("\n")
            return fm, body
    return {}, text

# ----- Markdown → HTML 변환 -----
def md_to_html(text):
    md = markdown.Markdown(
        extensions=[
            "extra",           # 테이블, 약어, fenced code, attr_list 등
            "md_in_html",      # markdown="1" 지원
            "sane_lists",
            "toc",
        ],
        extension_configs={
            "toc": {"toc_depth": "2-3"},
        },
    )
    return md.convert(text)

# ----- 스타일 (단일 CSS 문자열) -----
CSS = """
:root {
  --bg-base: #0a0a0f; --bg-elevated: #14141c; --bg-card: #1a1a25;
  --text-primary: #e6e6f0; --text-secondary: #a0a0b8; --text-muted: #6a6a82;
  --accent-cyan: #00f0ff; --accent-magenta: #ff00aa; --accent-amber: #ffb800;
  --accent-success: #00ff88; --accent-danger: #ff3355;
  --border-subtle: rgba(255,255,255,0.08); --border-strong: rgba(255,255,255,0.16);
  --font-display: 'Orbitron', 'Bebas Neue', system-ui, sans-serif;
  --font-body: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --max-width: 1280px; --content-max: 880px;
}
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; font-family: var(--font-body); background: var(--bg-base);
  background-image:
    radial-gradient(ellipse at top, rgba(0,240,255,0.04) 0%, transparent 50%),
    radial-gradient(ellipse at bottom, rgba(255,0,170,0.03) 0%, transparent 50%);
  background-attachment: fixed; color: var(--text-primary);
  font-size: 16px; line-height: 1.7; min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}
body::before {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 1;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' /%3E%3C/svg%3E");
}
a { color: var(--accent-cyan); text-decoration: none; transition: color 0.15s; }
a:hover { color: #66f5ff; }
code { font-family: 'JetBrains Mono', monospace; font-size: 0.92em;
  background: rgba(0,240,255,0.08); color: var(--accent-cyan);
  padding: 0.15em 0.4em; border-radius: 4px; }
pre { background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  border-radius: 12px; padding: 1.2em; overflow-x: auto; }
pre code { background: none; color: var(--text-primary); padding: 0; }

.site-header { position: sticky; top: 0; z-index: 100;
  background: rgba(10,10,15,0.85); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px); border-bottom: 1px solid var(--border-subtle); }
.site-header-inner { max-width: var(--max-width); margin: 0 auto;
  padding: 1rem 1.5rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.site-logo { display: inline-flex; align-items: center; gap: 0.6rem;
  color: var(--text-primary); font-family: var(--font-display);
  font-weight: 900; font-size: 1.1rem; letter-spacing: 0.12em; }
.site-logo:hover { color: var(--accent-cyan); }
.logo-mark { color: var(--accent-cyan); text-shadow: 0 0 12px rgba(0,240,255,0.6); }
.site-nav { display: flex; gap: 1.5rem; }
.site-nav .nav-link { color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; }
.site-nav .nav-link:hover { color: var(--text-primary); }

.site-main { max-width: var(--max-width); margin: 0 auto;
  padding: 2rem 1.5rem 4rem; position: relative; z-index: 2; }

.hero { position: relative; padding: 4rem 0 3rem; text-align: center; overflow: hidden; }
.hero-glow { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(0,240,255,0.12) 0%, transparent 60%);
  pointer-events: none; z-index: 0; }
.hero-inner { position: relative; z-index: 1; }
.hero-title { font-family: var(--font-display); font-weight: 900;
  font-size: clamp(3rem, 8vw, 6rem); letter-spacing: 0.05em;
  margin: 0 0 0.5rem; line-height: 1;
  text-shadow: 0 0 40px rgba(0,240,255,0.25); }
.hero-title .accent {
  background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-magenta) 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; }
.hero-tagline { font-size: 1.1rem; color: var(--text-secondary); margin: 0 0 1.5rem; }
.hero-meta { display: inline-flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; }
.chip { display: inline-block; padding: 0.35rem 0.85rem;
  border: 1px solid var(--border-strong); border-radius: 999px;
  font-size: 0.78rem; color: var(--text-secondary);
  background: rgba(255,255,255,0.03); }

.games-section { margin-top: 2rem; }
.games-section-header { display: flex; align-items: center;
  justify-content: space-between; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.section-title { font-family: var(--font-display); font-weight: 700;
  font-size: 1.5rem; letter-spacing: 0.05em; margin: 0; }
.section-title::before { content: '◆ '; color: var(--accent-cyan); }
.game-search { background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  border-radius: 6px; padding: 0.55rem 0.9rem; color: var(--text-primary);
  font-family: inherit; font-size: 0.9rem; min-width: 240px;
  transition: border-color 0.15s, box-shadow 0.15s; }
.game-search:focus { outline: none; border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(0,240,255,0.15); }
.game-search::placeholder { color: var(--text-muted); }

.games-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }
.game-card { background: var(--bg-card); border: 1px solid var(--border-subtle);
  border-radius: 12px; overflow: hidden; color: var(--text-primary);
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
  display: flex; flex-direction: column; }
.game-card:hover { transform: translateY(-4px); border-color: var(--accent-cyan);
  box-shadow: 0 12px 32px rgba(0,0,0,0.4), 0 0 24px rgba(0,240,255,0.2); }
.game-card:hover .game-card-title { color: var(--accent-cyan); }
.game-card-cover { position: relative; aspect-ratio: 16 / 9;
  background-color: var(--bg-elevated); background-size: cover; background-position: center; }
.cover-placeholder { position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 4rem; font-weight: 900;
  color: rgba(0,240,255,0.3);
  background: linear-gradient(135deg, rgba(0,240,255,0.05), rgba(255,0,170,0.05)); }
.game-card-overlay { position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 40%, rgba(10,10,15,0.7) 100%); }
.game-card-badge { position: absolute; top: 0.6rem; right: 0.6rem;
  padding: 0.2rem 0.55rem; border-radius: 4px; font-size: 0.7rem;
  font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  background: rgba(10,10,15,0.85); border: 1px solid var(--border-subtle); }
.badge-complete { color: var(--accent-success); border-color: rgba(0,255,136,0.4) !important; }
.badge-progress { color: var(--accent-amber); border-color: rgba(255,184,0,0.4) !important; }
.badge-plan { color: var(--text-muted); }
.game-card-info { padding: 1rem 1.1rem 1.2rem; }
.game-card-title { font-family: var(--font-display); font-weight: 700;
  font-size: 1.05rem; margin: 0 0 0.3rem; letter-spacing: 0.02em; transition: color 0.2s; }
.game-card-meta { font-size: 0.8rem; color: var(--text-muted); margin: 0 0 0.5rem; }
.game-card-summary { font-size: 0.88rem; color: var(--text-secondary); margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.empty-state { text-align: center; padding: 4rem 1rem; color: var(--text-muted);
  border: 1px dashed var(--border-subtle); border-radius: 12px; }

.game-page { position: relative; }
.game-hero { position: relative; padding: 4rem 1.5rem 3rem; margin: -2rem -1.5rem 0;
  background-color: var(--bg-elevated); background-size: cover; background-position: center;
  border-bottom: 1px solid var(--border-subtle); }
.game-hero-inner { max-width: var(--content-max); margin: 0 auto; }
.back-link { display: inline-block; color: var(--text-secondary);
  font-size: 0.85rem; margin-bottom: 1rem; }
.back-link:hover { color: var(--accent-cyan); }
.game-title { font-family: var(--font-display); font-weight: 900;
  font-size: clamp(2rem, 5vw, 3.5rem); letter-spacing: 0.04em;
  margin: 0 0 0.4rem; line-height: 1.1;
  text-shadow: 0 2px 24px rgba(0,0,0,0.8); }
.game-subtitle { font-size: 1.05rem; color: var(--text-secondary); margin: 0 0 1.5rem; }
.game-meta { display: flex; flex-wrap: wrap; gap: 1.2rem 2rem; margin-top: 1.5rem; }
.meta-item { display: flex; flex-direction: column; gap: 0.15rem; }
.meta-label { font-size: 0.72rem; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.08em; }
.meta-value { font-size: 0.95rem; color: var(--text-primary); font-weight: 500; }
.game-status { display: inline-block; margin-top: 1.2rem;
  padding: 0.3rem 0.7rem; border-radius: 4px; font-size: 0.78rem;
  font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  background: rgba(10,10,15,0.6); border: 1px solid var(--border-strong); }

.game-body { max-width: var(--max-width); margin: 0 auto; padding: 2.5rem 0;
  display: grid; grid-template-columns: 240px 1fr; gap: 3rem; }
@media (max-width: 900px) {
  .game-body { grid-template-columns: 1fr; }
  .game-toc { display: none; }
}
.toc-sticky { position: sticky; top: 5rem; max-height: calc(100vh - 6rem);
  overflow-y: auto; padding-right: 0.5rem; }
.toc-title { font-family: var(--font-display); font-size: 0.85rem; font-weight: 700;
  letter-spacing: 0.1em; color: var(--accent-cyan); margin: 0 0 1rem; text-transform: uppercase; }
.toc-nav { display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.88rem; }
.toc-nav a { color: var(--text-secondary); padding: 0.25rem 0.6rem;
  border-left: 2px solid transparent; transition: all 0.15s; }
.toc-nav a:hover, .toc-nav a.active { color: var(--text-primary);
  border-left-color: var(--accent-cyan); background: rgba(0,240,255,0.05); }
.toc-nav a.toc-h3 { padding-left: 1.4rem; font-size: 0.83rem; color: var(--text-muted); }
.spoiler-toggle { margin-top: 2rem; padding-top: 1.2rem;
  border-top: 1px solid var(--border-subtle);
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 0.85rem; color: var(--text-secondary); }
.switch { position: relative; display: inline-block; width: 36px; height: 20px; }
.switch input { opacity: 0; width: 0; height: 0; }
.switch .slider { position: absolute; inset: 0; background: var(--bg-elevated);
  border: 1px solid var(--border-strong); border-radius: 999px;
  cursor: pointer; transition: background 0.2s; }
.switch .slider::before { content: ''; position: absolute;
  width: 14px; height: 14px; left: 2px; top: 2px;
  background: var(--text-secondary); border-radius: 50%; transition: transform 0.2s; }
.switch input:checked + .slider { background: var(--accent-cyan); border-color: var(--accent-cyan); }
.switch input:checked + .slider::before { transform: translateX(16px); background: var(--bg-base); }

.game-content { max-width: var(--content-max); font-size: 1rem; line-height: 1.8; }
.game-content h1 { display: none; }
.game-content h2 { font-family: var(--font-display); font-weight: 700;
  font-size: 1.7rem; letter-spacing: 0.03em; margin: 3rem 0 1rem;
  padding-bottom: 0.5rem; border-bottom: 1px solid var(--border-subtle);
  scroll-margin-top: 5rem; }
.game-content h2::before { content: '▸ '; color: var(--accent-cyan); }
.game-content h2:first-child { margin-top: 0; }
.game-content h3 { font-family: var(--font-display); font-weight: 600;
  font-size: 1.25rem; margin: 2rem 0 0.8rem;
  color: var(--accent-cyan); scroll-margin-top: 5rem; }
.game-content h4 { font-size: 1.05rem; font-weight: 700; margin: 1.5rem 0 0.5rem; }
.game-content p { margin: 0 0 1rem; }
.game-content ul, .game-content ol { margin: 0 0 1rem; padding-left: 1.5rem; }
.game-content li { margin-bottom: 0.4rem; }
.game-content input[type="checkbox"] { margin-right: 0.5rem; accent-color: var(--accent-cyan); }
.game-content blockquote { margin: 1.5rem 0; padding: 1rem 1.2rem;
  background: rgba(0,240,255,0.05); border-left: 3px solid var(--accent-cyan);
  border-radius: 0 6px 6px 0; color: var(--text-secondary); }
.game-content blockquote p:last-child { margin-bottom: 0; }
.game-content table { width: 100%; border-collapse: collapse;
  margin: 1.5rem 0; font-size: 0.92rem; }
.game-content th, .game-content td { padding: 0.7rem 0.9rem; text-align: left;
  border-bottom: 1px solid var(--border-subtle); }
.game-content th { background: var(--bg-elevated); color: var(--accent-cyan);
  font-weight: 700; font-family: var(--font-display); font-size: 0.82rem;
  letter-spacing: 0.05em; text-transform: uppercase; }
.game-content tr:hover td { background: rgba(255,255,255,0.02); }
.game-content hr { border: none; border-top: 1px solid var(--border-subtle); margin: 2.5rem 0; }
.tip, .warn, .boss, .secret { margin: 1.5rem 0; padding: 1rem 1.2rem;
  border-radius: 12px; border-left: 4px solid; }
.tip { background: rgba(0,255,136,0.06); border-left-color: var(--accent-success); }
.warn { background: rgba(255,184,0,0.06); border-left-color: var(--accent-amber); }
.boss { background: rgba(255,51,85,0.06); border-left-color: var(--accent-danger); }
.secret { background: rgba(255,0,170,0.06); border-left-color: var(--accent-magenta); }
.tip p:last-child, .warn p:last-child, .boss p:last-child, .secret p:last-child { margin-bottom: 0; }
.spoiler { background: var(--text-primary); color: var(--text-primary);
  border-radius: 3px; padding: 0 0.2em; cursor: pointer; transition: background 0.2s; }
body.show-spoilers .spoiler { background: transparent; color: inherit; }
.spoiler-banner { padding: 0.8rem 1.2rem; margin-bottom: 2rem;
  background: rgba(255,51,85,0.08); border: 1px solid rgba(255,51,85,0.3);
  border-radius: 12px; color: var(--accent-danger); font-size: 0.92rem; }
.sources { margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--border-subtle); }
.sources h2 { font-family: var(--font-display); font-size: 1.1rem;
  color: var(--text-muted); border: none; padding: 0; margin: 0 0 0.8rem; }
.sources h2::before { content: ''; }
.sources-list { list-style: none; padding: 0; font-size: 0.88rem; color: var(--text-muted); }
.sources-list li { margin-bottom: 0.4rem; }

.site-footer { border-top: 1px solid var(--border-subtle);
  padding: 2rem 1.5rem; margin-top: 4rem; position: relative; z-index: 2; }
.site-footer-inner { max-width: var(--max-width); margin: 0 auto; text-align: center; }
.footer-text { color: var(--text-muted); font-size: 0.85rem; margin: 0.3rem 0; }
.footer-text.small { font-size: 0.78rem; }

@media (max-width: 600px) {
  .games-grid { grid-template-columns: 1fr; }
  .game-search { min-width: 0; width: 100%; }
  .games-section-header { flex-direction: column; align-items: stretch; }
  .game-meta { gap: 1rem; }
}
"""

JS = """
// 게임 카드 검색
const search = document.getElementById('game-search');
const grid = document.getElementById('games-grid');
if (search && grid) {
  search.addEventListener('input', e => {
    const q = e.target.value.trim().toLowerCase();
    grid.querySelectorAll('.game-card').forEach(card => {
      const t = (card.dataset.title || '') + ' ' + (card.dataset.genre || '');
      card.style.display = (!q || t.includes(q)) ? '' : 'none';
    });
  });
}

// 게임 페이지 목차 자동 생성
function buildTOC() {
  const tocNav = document.getElementById('toc-nav');
  const content = document.querySelector('.game-content');
  if (!tocNav || !content) return;
  const headings = content.querySelectorAll('h2, h3');
  if (headings.length === 0) {
    const aside = document.getElementById('game-toc');
    if (aside) aside.style.display = 'none';
    return;
  }
  headings.forEach(h => {
    if (!h.id) {
      h.id = h.textContent.trim().toLowerCase()
        .replace(/\\s+/g, '-')
        .replace(/[^\\w가-힣-]/g, '');
    }
    const link = document.createElement('a');
    link.href = '#' + h.id;
    link.textContent = h.textContent;
    link.className = h.tagName === 'H3' ? 'toc-h3' : 'toc-h2';
    tocNav.appendChild(link);
  });
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      const link = tocNav.querySelector('a[href="#' + e.target.id + '"]');
      if (link && e.isIntersecting) {
        tocNav.querySelectorAll('a').forEach(a => a.classList.remove('active'));
        link.classList.add('active');
      }
    });
  }, { rootMargin: '-80px 0px -70% 0px' });
  headings.forEach(h => obs.observe(h));
}
window.addEventListener('load', buildTOC);

// 스포일러 토글
const sw = document.getElementById('spoiler-switch');
if (sw) {
  const saved = localStorage.getItem('show-spoilers') === '1';
  sw.checked = saved;
  document.body.classList.toggle('show-spoilers', saved);
  sw.addEventListener('change', () => {
    document.body.classList.toggle('show-spoilers', sw.checked);
    localStorage.setItem('show-spoilers', sw.checked ? '1' : '0');
  });
}

// 인라인 스포일러 클릭 표시
document.addEventListener('click', e => {
  if (e.target?.classList?.contains('spoiler')) {
    e.target.style.background = 'transparent';
    e.target.style.color = 'inherit';
  }
});

// 체크리스트 상태 저장
const content = document.querySelector('.game-content');
if (content) {
  const slug = window.location.pathname;
  content.querySelectorAll('input[type="checkbox"]').forEach((cb, idx) => {
    const key = 'check:' + slug + ':' + idx;
    if (localStorage.getItem(key) === '1') cb.checked = true;
    cb.addEventListener('change', () => {
      localStorage.setItem(key, cb.checked ? '1' : '0');
    });
  });
}
"""

# ----- HTML 템플릿 -----
HEAD_TPL = """<!DOCTYPE html>
<html lang="ko-KR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{description}" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Bebas+Neue&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="{base}/assets/style.css">
</head>
<body class="theme-dark">
"""

HEADER_TPL = """<header class="site-header">
  <div class="site-header-inner">
    <a href="{base}/" class="site-logo">
      <span class="logo-mark">▶</span>
      <span class="logo-text">PLAY ARCHIVE</span>
    </a>
    <nav class="site-nav">
      <a href="{base}/" class="nav-link">라이브러리</a>
      <a href="https://github.com/{user}/Play_Archive" class="nav-link" target="_blank" rel="noopener">GitHub</a>
    </nav>
  </div>
</header>
"""

FOOTER_TPL = """<footer class="site-footer">
  <div class="site-footer-inner">
    <p class="footer-text">© 2026 {author} · Play Archive</p>
    <p class="footer-text small">공략 내용은 한국 위키/커뮤니티(나무위키, 인벤, 디시인사이드 등)의 출처를 기반으로 재정리되었습니다.</p>
  </div>
</footer>
<script src="{base}/assets/main.js"></script>
</body>
</html>
"""

STATUS_BADGE_CLASS = {
    "완료": "badge-complete",
    "진행중": "badge-progress",
    "계획": "badge-plan",
}

PLACEHOLDER_GRADIENTS = [
    "linear-gradient(135deg, #1a1a3a 0%, #003344 50%, #001122 100%)",
    "linear-gradient(135deg, #2a1810 0%, #4a2810 50%, #1a0808 100%)",
    "linear-gradient(135deg, #2a1a3a 0%, #4a1a4a 50%, #1a0a2a 100%)",
    "linear-gradient(135deg, #1a2a3a 0%, #2a3a5a 50%, #0a1a2a 100%)",
    "linear-gradient(135deg, #1a3a2a 0%, #2a5a3a 50%, #0a2a1a 100%)",
    "linear-gradient(135deg, #3a1a1a 0%, #5a2a2a 50%, #2a0a0a 100%)",
]

def card_html(game, base):
    fm = game["fm"]
    slug = game["slug"]
    title = escape(fm.get("title", slug))
    genre = escape(fm.get("genre", ""))
    dev = escape(fm.get("developer", ""))
    summary = escape(fm.get("summary", ""))
    status = fm.get("status", "")
    badge_cls = STATUS_BADGE_CLASS.get(status, "badge-plan")
    cover = fm.get("cover")
    idx = game.get("idx", 0)
    grad = PLACEHOLDER_GRADIENTS[idx % len(PLACEHOLDER_GRADIENTS)]
    if cover:
        cover_style = f'background-image: url(\'{escape(cover)}\');'
        placeholder = ''
    else:
        cover_style = f'background: {grad};'
        first_char = title[0] if title else '?'
        placeholder = f'<div class="cover-placeholder">{escape(first_char)}</div>'
    meta_parts = [p for p in [genre, dev] if p]
    meta = ' · '.join(meta_parts)
    return f"""<a href="{base}/games/{slug}.html" class="game-card" data-title="{escape(fm.get('title','').lower())}" data-genre="{escape(genre.lower())}">
  <div class="game-card-cover" style="{cover_style}">
    {placeholder}
    <div class="game-card-overlay"></div>
    {f'<span class="game-card-badge {badge_cls}">{escape(status)}</span>' if status else ''}
  </div>
  <div class="game-card-info">
    <h3 class="game-card-title">{title}</h3>
    {f'<p class="game-card-meta">{escape(meta)}</p>' if meta else ''}
    {f'<p class="game-card-summary">{summary}</p>' if summary else ''}
  </div>
</a>"""


def render_index(games, config, base, user, author):
    cards = "\n".join(card_html(g, base) for g in games)
    if not games:
        body = '<div class="empty-state"><p>아직 등록된 게임이 없습니다.</p></div>'
    else:
        body = f'<div class="games-grid" id="games-grid">{cards}</div>'
    head = HEAD_TPL.format(
        title="Play Archive",
        description=escape(config.get("description", "")),
        base=base,
    )
    header = HEADER_TPL.format(base=base, user=user)
    footer = FOOTER_TPL.format(author=escape(author), base=base)
    return f"""{head}{header}
<main class="site-main">
  <section class="hero">
    <div class="hero-inner">
      <h1 class="hero-title">PLAY <span class="accent">ARCHIVE</span></h1>
      <p class="hero-tagline">{escape(config.get('description', ''))}</p>
      <div class="hero-meta">
        <span class="chip">총 {len(games)} 작품</span>
        <span class="chip">100% 공략 추구</span>
        <span class="chip">한글 가이드</span>
      </div>
    </div>
    <div class="hero-glow" aria-hidden="true"></div>
  </section>
  <section class="games-section">
    <div class="games-section-header">
      <h2 class="section-title">게임 라이브러리</h2>
      <input type="search" id="game-search" class="game-search" placeholder="게임 검색..." aria-label="게임 검색" />
    </div>
    {body}
  </section>
</main>
{footer}"""


def render_game(game, base, user, author):
    fm = game["fm"]
    content_html = game["html"]
    title = escape(fm.get("title", game["slug"]))
    subtitle = fm.get("subtitle", "")

    cover = fm.get("cover")
    idx = game.get("idx", 0)
    grad = PLACEHOLDER_GRADIENTS[idx % len(PLACEHOLDER_GRADIENTS)]
    if cover:
        hero_style = (
            f"background-image: linear-gradient(180deg, rgba(14,14,18,0.3) 0%, rgba(14,14,18,0.95) 80%), "
            f"url('{escape(cover)}');"
        )
    else:
        hero_style = (
            f"background-image: linear-gradient(180deg, rgba(14,14,18,0.3) 0%, rgba(14,14,18,0.95) 80%), {grad};"
            f"background-color: var(--bg-elevated);"
        )

    meta_html = ""
    for key, label in [("genre", "장르"), ("developer", "개발사"), ("release", "발매"),
                       ("platform", "플랫폼"), ("difficulty", "난이도"), ("playtime", "플레이타임")]:
        val = fm.get(key)
        if val:
            meta_html += f'<div class="meta-item"><span class="meta-label">{label}</span><span class="meta-value">{escape(str(val))}</span></div>\n'

    status = fm.get("status", "")
    status_html = f'<div class="game-status">{escape(status)}</div>' if status else ""

    spoiler_banner = '<div class="spoiler-banner">⚠️ 이 페이지에는 스토리 스포일러가 포함되어 있습니다.</div>' if fm.get("spoiler") else ""
    spoiler_toggle = ''
    if fm.get("spoiler"):
        spoiler_toggle = """<div class="spoiler-toggle">
          <label class="switch">
            <input type="checkbox" id="spoiler-switch" />
            <span class="slider"></span>
          </label>
          <span>스포일러 표시</span>
        </div>"""

    sources_html = ""
    sources = fm.get("sources", [])
    if sources:
        items = ""
        for s in sources:
            t = escape(s.get("title", ""))
            u = escape(s.get("url", "#"))
            note = s.get("note", "")
            note_html = f' — <span class="src-note">{escape(note)}</span>' if note else ""
            items += f'<li><a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>{note_html}</li>\n'
        sources_html = f'<section class="sources"><h2>출처</h2><ul class="sources-list">{items}</ul></section>'

    head = HEAD_TPL.format(
        title=f"{fm.get('title', game['slug'])} · Play Archive",
        description=escape(fm.get("summary", "")),
        base=base,
    )
    header = HEADER_TPL.format(base=base, user=user)
    footer = FOOTER_TPL.format(author=escape(author), base=base)

    return f"""{head}{header}
<main class="site-main">
  <article class="game-page">
    <header class="game-hero" style="{hero_style}">
      <div class="game-hero-inner">
        <a href="{base}/" class="back-link">← 라이브러리</a>
        <h1 class="game-title">{title}</h1>
        {f'<p class="game-subtitle">{escape(subtitle)}</p>' if subtitle else ''}
        <div class="game-meta">{meta_html}</div>
        {status_html}
      </div>
    </header>
    <div class="game-body">
      <aside class="game-toc" id="game-toc">
        <div class="toc-sticky">
          <h3 class="toc-title">목차</h3>
          <nav id="toc-nav" class="toc-nav"></nav>
          {spoiler_toggle}
        </div>
      </aside>
      <div class="game-content">
        {spoiler_banner}
        {content_html}
        {sources_html}
      </div>
    </div>
  </article>
</main>
{footer}"""


def main():
    config = load_config()
    base_raw = config.get("baseurl", "") or ""
    base = base_raw.rstrip("/")  # 예: "/Play_Archive"
    user = config.get("github_username", "")
    author = config.get("author", "")

    # 출력 디렉토리 초기화
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    OUT_GAMES.mkdir(parents=True)
    OUT_ASSETS.mkdir(parents=True)

    # 게임 파일 수집
    games = []
    for md_file in sorted(GAMES_DIR.glob("*.md")):
        if md_file.name.startswith("_"):
            continue  # _TEMPLATE.md 제외
        slug = md_file.stem
        fm, body = parse_md(md_file)
        if not fm.get("title"):
            continue
        html = md_to_html(body)
        games.append({"slug": slug, "fm": fm, "body": body, "html": html})

    # 정렬 (제목 가나다)
    games.sort(key=lambda g: g["fm"].get("title", ""))
    for i, g in enumerate(games):
        g["idx"] = i

    # CSS / JS
    (OUT_ASSETS / "style.css").write_text(CSS, encoding="utf-8")
    (OUT_ASSETS / "main.js").write_text(JS, encoding="utf-8")

    # 게임 이미지 폴더 복사 (있으면)
    img_src = ASSETS_DIR / "images"
    if img_src.exists():
        shutil.copytree(img_src, OUT_ASSETS / "images")

    # 메인 페이지
    index_html = render_index(games, config, base, user, author)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # 각 게임 페이지
    for g in games:
        page = render_game(g, base, user, author)
        (OUT_GAMES / f"{g['slug']}.html").write_text(page, encoding="utf-8")

    # .nojekyll (GitHub Pages가 Jekyll 처리 건너뛰도록)
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"✅ 빌드 완료: {len(games)} 게임")
    print(f"   출력: {OUT_DIR}")
    for g in games:
        print(f"   - {g['slug']}.html ({g['fm'].get('title')})")


if __name__ == "__main__":
    main()
