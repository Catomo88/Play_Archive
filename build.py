#!/usr/bin/env python3
"""
Play Archive — 정적 HTML 빌드 스크립트 (v2: 탭 UI 지원)
================================================================
_games/*.md 파일을 읽어 정적 HTML 사이트를 빌드합니다.

탭 마커 지원:
    마크다운 본문에 `<!-- tab:이름 -->` 주석을 넣으면
    해당 위치부터 새 탭으로 분리됩니다.

챕터 탭의 특수 기능:
    - 탭 이름에 "챕터"가 포함되면 자동으로
      챕터 점프 네비게이션 + 책갈피 별 토글이 추가됩니다.

출력: docs/index.html + docs/games/<slug>.html + docs/assets/...

사용법:
    python3 build.py
"""
import os
import re
import shutil
import yaml
import markdown
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent
GAMES_DIR = ROOT / "_games"
ASSETS_DIR = ROOT / "assets"
OUT_DIR = ROOT / "docs"
OUT_GAMES = OUT_DIR / "games"
OUT_ASSETS = OUT_DIR / "assets"

TAB_MARKER = re.compile(r"<!--\s*tab\s*:\s*(.+?)\s*-->")


def load_config():
    with open(ROOT / "_config.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_md(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1]) or {}
            body = parts[2].lstrip("\n")
            return fm, body
    return {}, text


def md_to_html(text):
    md = markdown.Markdown(
        extensions=["extra", "md_in_html", "sane_lists", "toc"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    return md.convert(text)


def slugify_tab(name):
    """탭 이름을 URL 슬러그로 변환."""
    mapping = {
        "개요": "overview",
        "챕터": "chapters",
        "챕터별 공략": "chapters",
        "히든": "hidden",
        "히든 보스": "hidden",
        "업적": "achievements",
        "엔딩": "endings",
        "팁": "tips",
        "팁/faq": "tips",
        "FAQ": "tips",
    }
    key = name.strip().lower()
    if key in mapping:
        return mapping[key]
    # fallback: 영문/숫자만 추출
    s = re.sub(r"[^\w가-힣]+", "-", name.strip()).strip("-").lower()
    return s or "tab"


def split_into_tabs(body):
    """본문을 <!-- tab:name --> 마커로 분리."""
    tabs = []
    # 마커 위치 찾기
    matches = list(TAB_MARKER.finditer(body))
    if not matches:
        # 마커가 없으면 단일 탭
        return [{"name": "전체", "slug": "all", "body": body}]
    # 첫 마커 이전 내용 (있으면 "intro" 탭으로)
    first_start = matches[0].start()
    if first_start > 0:
        intro = body[:first_start].strip()
        if intro:
            tabs.append({"name": "소개", "slug": "intro", "body": intro})
    # 각 마커별로 분리
    for i, m in enumerate(matches):
        name = m.group(1)
        slug = slugify_tab(name)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section = body[start:end].strip()
        tabs.append({"name": name, "slug": slug, "body": section})
    return tabs


def add_chapter_features(html, tab_slug):
    """챕터 탭에서 챕터 점프 네비 + 책갈피 별 토글을 추가."""
    if "chapter" not in tab_slug.lower():
        return html, []
    # h3 추출 (챕터 후보)
    h3_pattern = re.compile(r'<h3([^>]*)>(.*?)</h3>', re.DOTALL)
    chapters = []
    for m in h3_pattern.finditer(html):
        attrs = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        # h3 id 추출 (markdown extension이 자동 생성)
        id_match = re.search(r'id="([^"]+)"', attrs)
        h_id = id_match.group(1) if id_match else re.sub(r'[^\w가-힣]+', '-', title).strip('-').lower()
        chapters.append({"id": h_id, "title": title})
    # 각 h3 옆에 책갈피 버튼 삽입
    def inject_bookmark(m):
        attrs = m.group(1)
        inner = m.group(2)
        id_match = re.search(r'id="([^"]+)"', attrs)
        h_id = id_match.group(1) if id_match else ""
        # 책갈피 별 버튼
        btn = f'<button class="bookmark-btn" data-chapter-id="{escape(h_id)}" title="책갈피 토글" aria-label="책갈피 토글">★</button>'
        return f'<h3{attrs}>{btn}{inner}</h3>'
    html_with_btns = h3_pattern.sub(inject_bookmark, html)
    return html_with_btns, chapters


CSS = """
:root {
  --bg-base: #0a0a0f; --bg-elevated: #14141c; --bg-card: #1a1a25;
  --bg-card-hover: #20202d;
  --text-primary: #e6e6f0; --text-secondary: #a0a0b8; --text-muted: #6a6a82;
  --accent-cyan: #00f0ff; --accent-magenta: #ff00aa; --accent-amber: #ffb800;
  --accent-success: #00ff88; --accent-danger: #ff3355;
  --border-subtle: rgba(255,255,255,0.08); --border-strong: rgba(255,255,255,0.16);
  --font-display: 'Orbitron', 'Bebas Neue', system-ui, sans-serif;
  --font-body: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --max-width: 1280px; --content-max: 920px;
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
  background: rgba(10,10,15,0.92); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px); border-bottom: 1px solid var(--border-subtle); }
.site-header-inner { max-width: var(--max-width); margin: 0 auto;
  padding: 0.9rem 1.2rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.site-logo { display: inline-flex; align-items: center; gap: 0.5rem;
  color: var(--text-primary); font-family: var(--font-display);
  font-weight: 900; font-size: 1rem; letter-spacing: 0.12em; }
.site-logo:hover { color: var(--accent-cyan); }
.logo-mark { color: var(--accent-cyan); text-shadow: 0 0 12px rgba(0,240,255,0.6); }
.site-nav { display: flex; gap: 1.2rem; }
.site-nav .nav-link { color: var(--text-secondary); font-size: 0.88rem; font-weight: 500; }
.site-nav .nav-link:hover { color: var(--text-primary); }

.site-main { max-width: var(--max-width); margin: 0 auto;
  padding: 1.5rem 1.2rem 4rem; position: relative; z-index: 2; }

.hero { position: relative; padding: 3rem 0 2.5rem; text-align: center; overflow: hidden; }
.hero-glow { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 600px; height: 600px; max-width: 100%;
  background: radial-gradient(circle, rgba(0,240,255,0.12) 0%, transparent 60%);
  pointer-events: none; z-index: 0; }
.hero-inner { position: relative; z-index: 1; }
.hero-title { font-family: var(--font-display); font-weight: 900;
  font-size: clamp(2.5rem, 8vw, 5rem); letter-spacing: 0.05em;
  margin: 0 0 0.4rem; line-height: 1;
  text-shadow: 0 0 40px rgba(0,240,255,0.25); }
.hero-title .accent {
  background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-magenta) 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; }
.hero-tagline { font-size: 1rem; color: var(--text-secondary); margin: 0 0 1.2rem; }
.hero-meta { display: inline-flex; flex-wrap: wrap; gap: 0.4rem; justify-content: center; }
.chip { display: inline-block; padding: 0.3rem 0.75rem;
  border: 1px solid var(--border-strong); border-radius: 999px;
  font-size: 0.75rem; color: var(--text-secondary);
  background: rgba(255,255,255,0.03); }

.games-section { margin-top: 1.5rem; }
.games-section-header { display: flex; align-items: center;
  justify-content: space-between; gap: 1rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.section-title { font-family: var(--font-display); font-weight: 700;
  font-size: 1.3rem; letter-spacing: 0.05em; margin: 0; }
.section-title::before { content: '◆ '; color: var(--accent-cyan); }
.game-search { background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  border-radius: 6px; padding: 0.55rem 0.9rem; color: var(--text-primary);
  font-family: inherit; font-size: 0.9rem; min-width: 200px;
  transition: border-color 0.15s, box-shadow 0.15s; }
.game-search:focus { outline: none; border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(0,240,255,0.15); }
.game-search::placeholder { color: var(--text-muted); }

.games-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.2rem; }
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
  font-family: var(--font-display); font-size: 3.5rem; font-weight: 900;
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
.game-card-info { padding: 0.9rem 1rem 1.1rem; }
.game-card-title { font-family: var(--font-display); font-weight: 700;
  font-size: 1rem; margin: 0 0 0.3rem; letter-spacing: 0.02em; transition: color 0.2s; }
.game-card-meta { font-size: 0.78rem; color: var(--text-muted); margin: 0 0 0.5rem; }
.game-card-summary { font-size: 0.85rem; color: var(--text-secondary); margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.empty-state { text-align: center; padding: 4rem 1rem; color: var(--text-muted);
  border: 1px dashed var(--border-subtle); border-radius: 12px; }

/* ===== 게임 페이지 ===== */
.game-page { position: relative; }
.game-hero { position: relative; padding: 2.5rem 1.2rem 2rem; margin: -1.5rem -1.2rem 0;
  background-color: var(--bg-elevated); background-size: cover; background-position: center;
  border-bottom: 1px solid var(--border-subtle); }
.game-hero-inner { max-width: var(--content-max); margin: 0 auto; }
.back-link { display: inline-block; color: var(--text-secondary);
  font-size: 0.82rem; margin-bottom: 0.8rem; }
.back-link:hover { color: var(--accent-cyan); }
.game-title { font-family: var(--font-display); font-weight: 900;
  font-size: clamp(1.8rem, 5vw, 3rem); letter-spacing: 0.04em;
  margin: 0 0 0.4rem; line-height: 1.1;
  text-shadow: 0 2px 24px rgba(0,0,0,0.8); }
.game-subtitle { font-size: 0.95rem; color: var(--text-secondary); margin: 0 0 1rem; }
.game-meta { display: flex; flex-wrap: wrap; gap: 0.8rem 1.5rem; margin-top: 1rem; }
.meta-item { display: flex; flex-direction: column; gap: 0.1rem; }
.meta-label { font-size: 0.68rem; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.08em; }
.meta-value { font-size: 0.88rem; color: var(--text-primary); font-weight: 500; }
.game-status { display: inline-block; margin-top: 1rem;
  padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.72rem;
  font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  background: rgba(10,10,15,0.6); border: 1px solid var(--border-strong); }

/* ===== 탭 UI ===== */
.tabs-wrapper {
  position: sticky;
  top: 54px; /* 헤더 높이만큼 */
  z-index: 50;
  background: rgba(10,10,15,0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-subtle);
  margin: 0 -1.2rem;
  padding: 0 1.2rem;
}
.tabs {
  display: flex;
  gap: 0.4rem;
  max-width: var(--max-width);
  margin: 0 auto;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 0.6rem 0;
}
.tabs::-webkit-scrollbar { display: none; }
.tab {
  flex: 0 0 auto;
  padding: 0.55rem 1.1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.tab:hover { background: var(--bg-card-hover); color: var(--text-primary); }
.tab.active {
  background: linear-gradient(135deg, rgba(0,240,255,0.18), rgba(255,0,170,0.12));
  border-color: var(--accent-cyan);
  color: var(--text-primary);
  box-shadow: 0 0 16px rgba(0,240,255,0.25);
}

.tab-panels {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 1.5rem 0;
}
.tab-panel { display: none; }
.tab-panel.active { display: block; animation: fadein 0.2s; }
@keyframes fadein { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

/* ===== 챕터 점프 네비 ===== */
.chapter-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.9rem 1rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  margin-bottom: 1.5rem;
}
.chapter-nav-title {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent-cyan);
  text-transform: uppercase;
  width: 100%;
  margin-bottom: 0.3rem;
}
.chapter-jump {
  padding: 0.35rem 0.7rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 0.82rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}
.chapter-jump:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--accent-cyan);
}
.chapter-jump.bookmarked::before {
  content: '★';
  color: var(--accent-amber);
}

/* ===== 책갈피 ===== */
.bookmarks-panel {
  padding: 0.8rem 1rem;
  background: rgba(255,184,0,0.06);
  border: 1px solid rgba(255,184,0,0.25);
  border-radius: 12px;
  margin-bottom: 1rem;
  font-size: 0.88rem;
}
.bookmarks-panel.empty { display: none; }
.bookmarks-panel-title {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent-amber);
  text-transform: uppercase;
  margin-bottom: 0.4rem;
}
.bookmarks-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.bookmarks-list a {
  padding: 0.25rem 0.65rem;
  background: rgba(255,184,0,0.12);
  border: 1px solid rgba(255,184,0,0.3);
  border-radius: 999px;
  font-size: 0.8rem;
  color: var(--accent-amber);
}
.bookmarks-list a:hover {
  background: rgba(255,184,0,0.2);
  color: #ffd95e;
}

.bookmark-btn {
  background: none;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.85rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  margin-right: 0.6rem;
  transition: all 0.15s;
  vertical-align: middle;
  line-height: 1;
  padding: 0;
}
.bookmark-btn:hover {
  border-color: var(--accent-amber);
  color: var(--accent-amber);
}
.bookmark-btn.active {
  background: var(--accent-amber);
  border-color: var(--accent-amber);
  color: var(--bg-base);
}

/* ===== 본문 ===== */
.tab-content { font-size: 0.98rem; line-height: 1.75; }
.tab-content h1 { display: none; }
.tab-content h2 { font-family: var(--font-display); font-weight: 700;
  font-size: 1.4rem; letter-spacing: 0.03em; margin: 2.2rem 0 0.8rem;
  padding-bottom: 0.4rem; border-bottom: 1px solid var(--border-subtle);
  scroll-margin-top: 130px; }
.tab-content h2::before { content: '▸ '; color: var(--accent-cyan); }
.tab-content h2:first-child { margin-top: 0; }
.tab-content h3 { font-family: var(--font-display); font-weight: 600;
  font-size: 1.1rem; margin: 1.7rem 0 0.7rem;
  color: var(--accent-cyan); scroll-margin-top: 130px;
  display: flex; align-items: center; flex-wrap: wrap; }
.tab-content h4 { font-size: 1rem; font-weight: 700; margin: 1.2rem 0 0.5rem; }
.tab-content p { margin: 0 0 0.9rem; }
.tab-content ul, .tab-content ol { margin: 0 0 0.9rem; padding-left: 1.4rem; }
.tab-content li { margin-bottom: 0.3rem; }
.tab-content input[type="checkbox"] { margin-right: 0.5rem; accent-color: var(--accent-cyan); }
.tab-content blockquote { margin: 1.3rem 0; padding: 0.9rem 1.1rem;
  background: rgba(0,240,255,0.05); border-left: 3px solid var(--accent-cyan);
  border-radius: 0 6px 6px 0; color: var(--text-secondary); }
.tab-content blockquote p:last-child { margin-bottom: 0; }
.tab-content table { width: 100%; border-collapse: collapse;
  margin: 1.3rem 0; font-size: 0.88rem; }
.tab-content th, .tab-content td { padding: 0.6rem 0.8rem; text-align: left;
  border-bottom: 1px solid var(--border-subtle); }
.tab-content th { background: var(--bg-elevated); color: var(--accent-cyan);
  font-weight: 700; font-family: var(--font-display); font-size: 0.78rem;
  letter-spacing: 0.05em; text-transform: uppercase; }
.tab-content tr:hover td { background: rgba(255,255,255,0.02); }
.tab-content hr { border: none; border-top: 1px solid var(--border-subtle); margin: 2rem 0; }
.tip, .warn, .boss, .secret { margin: 1.3rem 0; padding: 0.9rem 1.1rem;
  border-radius: 12px; border-left: 4px solid; font-size: 0.93rem; }
.tip { background: rgba(0,255,136,0.06); border-left-color: var(--accent-success); }
.warn { background: rgba(255,184,0,0.06); border-left-color: var(--accent-amber); }
.boss { background: rgba(255,51,85,0.06); border-left-color: var(--accent-danger); }
.secret { background: rgba(255,0,170,0.06); border-left-color: var(--accent-magenta); }
.tip p:last-child, .warn p:last-child, .boss p:last-child, .secret p:last-child { margin-bottom: 0; }
.spoiler { background: var(--text-primary); color: var(--text-primary);
  border-radius: 3px; padding: 0 0.2em; cursor: pointer; transition: background 0.2s; }
body.show-spoilers .spoiler { background: transparent; color: inherit; }
.spoiler-banner { padding: 0.7rem 1rem; margin-bottom: 1.5rem;
  background: rgba(255,51,85,0.08); border: 1px solid rgba(255,51,85,0.3);
  border-radius: 12px; color: var(--accent-danger); font-size: 0.88rem; }

.spoiler-toolbar {
  display: flex; align-items: center; gap: 0.5rem;
  margin: 0 0 1rem; padding: 0.5rem 0.8rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  font-size: 0.82rem; color: var(--text-secondary);
  width: fit-content;
}
.switch { position: relative; display: inline-block; width: 32px; height: 18px; }
.switch input { opacity: 0; width: 0; height: 0; }
.switch .slider { position: absolute; inset: 0; background: var(--bg-card);
  border: 1px solid var(--border-strong); border-radius: 999px;
  cursor: pointer; transition: background 0.2s; }
.switch .slider::before { content: ''; position: absolute;
  width: 12px; height: 12px; left: 2px; top: 2px;
  background: var(--text-secondary); border-radius: 50%; transition: transform 0.2s; }
.switch input:checked + .slider { background: var(--accent-cyan); border-color: var(--accent-cyan); }
.switch input:checked + .slider::before { transform: translateX(14px); background: var(--bg-base); }

.sources { margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--border-subtle); }
.sources h2 { font-family: var(--font-display); font-size: 1rem;
  color: var(--text-muted); border: none; padding: 0; margin: 0 0 0.7rem; }
.sources h2::before { content: ''; }
.sources-list { list-style: none; padding: 0; font-size: 0.84rem; color: var(--text-muted); }
.sources-list li { margin-bottom: 0.35rem; }

.site-footer { border-top: 1px solid var(--border-subtle);
  padding: 1.8rem 1.2rem; margin-top: 3rem; position: relative; z-index: 2; }
.site-footer-inner { max-width: var(--max-width); margin: 0 auto; text-align: center; }
.footer-text { color: var(--text-muted); font-size: 0.82rem; margin: 0.25rem 0; }
.footer-text.small { font-size: 0.74rem; }

/* 모바일 */
@media (max-width: 600px) {
  .site-header-inner { padding: 0.8rem 1rem; }
  .site-main { padding: 1.2rem 1rem 3rem; }
  .games-grid { grid-template-columns: 1fr; }
  .game-search { min-width: 0; width: 100%; }
  .games-section-header { flex-direction: column; align-items: stretch; }
  .game-meta { gap: 0.7rem 1.2rem; }
  .game-hero { margin: -1.2rem -1rem 0; padding: 2rem 1rem 1.5rem; }
  .tabs-wrapper { margin: 0 -1rem; padding: 0 1rem; top: 50px; }
  .tabs { padding: 0.5rem 0; gap: 0.3rem; }
  .tab { padding: 0.45rem 0.85rem; font-size: 0.76rem; }
  .tab-content h2 { font-size: 1.25rem; scroll-margin-top: 120px; }
  .tab-content h3 { font-size: 1.05rem; scroll-margin-top: 120px; }
  .chapter-nav { padding: 0.8rem; }
  .chapter-jump { padding: 0.4rem 0.7rem; font-size: 0.8rem; }
}
"""

JS = r"""
// ===== 게임 카드 검색 =====
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

// ===== 탭 전환 =====
function showTab(slug, pushState = true) {
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.tab-panel');
  let found = false;
  tabs.forEach(t => {
    const active = t.dataset.tab === slug;
    t.classList.toggle('active', active);
    if (active) found = true;
  });
  panels.forEach(p => {
    p.classList.toggle('active', p.dataset.tab === slug);
  });
  if (found && pushState) {
    const newHash = '#tab=' + slug;
    if (location.hash !== newHash) history.replaceState(null, '', newHash);
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
}

document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => showTab(t.dataset.tab));
});

// 초기 탭 (URL 해시 기반)
(function () {
  const hash = location.hash;
  const m = hash.match(/^#tab=([\w가-힣-]+)/);
  if (m) {
    const slug = decodeURIComponent(m[1]);
    showTab(slug, false);
  } else {
    // 첫 번째 탭 활성화
    const first = document.querySelector('.tab');
    if (first) showTab(first.dataset.tab, false);
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
})();

// ===== 챕터 점프 네비 =====
document.querySelectorAll('.chapter-jump').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.target;
    const target = document.getElementById(id);
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// ===== 책갈피 =====
const PAGE_KEY = 'bookmarks:' + location.pathname;

function loadBookmarks() {
  try { return JSON.parse(localStorage.getItem(PAGE_KEY) || '[]'); }
  catch { return []; }
}
function saveBookmarks(arr) {
  localStorage.setItem(PAGE_KEY, JSON.stringify(arr));
}
function getChapterTitle(id) {
  const el = document.getElementById(id);
  if (!el) return id;
  // h3 안의 텍스트만 (책갈피 버튼 제외)
  return el.textContent.replace(/^★\s*/, '').trim();
}

function refreshBookmarkUI() {
  const bookmarks = loadBookmarks();
  // 별 버튼
  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    const id = btn.dataset.chapterId;
    btn.classList.toggle('active', bookmarks.includes(id));
  });
  // 점프 버튼
  document.querySelectorAll('.chapter-jump').forEach(btn => {
    btn.classList.toggle('bookmarked', bookmarks.includes(btn.dataset.target));
  });
  // 책갈피 패널
  const panel = document.getElementById('bookmarks-panel');
  if (panel) {
    if (bookmarks.length === 0) {
      panel.classList.add('empty');
    } else {
      panel.classList.remove('empty');
      const list = panel.querySelector('.bookmarks-list');
      list.innerHTML = '';
      bookmarks.forEach(id => {
        const a = document.createElement('a');
        a.href = '#' + id;
        a.textContent = '★ ' + getChapterTitle(id);
        a.addEventListener('click', e => {
          e.preventDefault();
          const target = document.getElementById(id);
          if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        list.appendChild(a);
      });
    }
  }
}

document.querySelectorAll('.bookmark-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    e.preventDefault();
    const id = btn.dataset.chapterId;
    let bookmarks = loadBookmarks();
    if (bookmarks.includes(id)) {
      bookmarks = bookmarks.filter(x => x !== id);
    } else {
      bookmarks.push(id);
    }
    saveBookmarks(bookmarks);
    refreshBookmarkUI();
  });
});

refreshBookmarkUI();

// ===== 스포일러 토글 =====
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
  if (e.target && e.target.classList && e.target.classList.contains('spoiler')) {
    e.target.style.background = 'transparent';
    e.target.style.color = 'inherit';
  }
});

// ===== 체크리스트 상태 저장 =====
const tabContents = document.querySelectorAll('.tab-content');
if (tabContents.length) {
  const slug = window.location.pathname;
  tabContents.forEach(c => {
    c.querySelectorAll('input[type="checkbox"]').forEach((cb, idx) => {
      const key = 'check:' + slug + ':' + idx;
      if (localStorage.getItem(key) === '1') cb.checked = true;
      cb.addEventListener('change', () => {
        localStorage.setItem(key, cb.checked ? '1' : '0');
      });
    });
  });
}
"""

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

STATUS_BADGE_CLASS = {"완료": "badge-complete", "진행중": "badge-progress", "계획": "badge-plan"}

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
        cover_style = f"background-image: url('{escape(cover)}');"
        placeholder = ''
    else:
        cover_style = f"background: {grad};"
        first_char = title[0] if title else '?'
        placeholder = f'<div class="cover-placeholder">{escape(first_char)}</div>'
    meta_parts = [p for p in [genre, dev] if p]
    meta = ' · '.join(meta_parts)
    status_html = f'<span class="game-card-badge {badge_cls}">{escape(status)}</span>' if status else ''
    meta_html = f'<p class="game-card-meta">{escape(meta)}</p>' if meta else ''
    summary_html = f'<p class="game-card-summary">{summary}</p>' if summary else ''
    return (
        f'<a href="{base}/games/{slug}.html" class="game-card" '
        f'data-title="{escape(fm.get("title","").lower())}" '
        f'data-genre="{escape(genre.lower())}">'
        f'<div class="game-card-cover" style="{cover_style}">{placeholder}'
        f'<div class="game-card-overlay"></div>{status_html}</div>'
        f'<div class="game-card-info">'
        f'<h3 class="game-card-title">{title}</h3>'
        f'{meta_html}{summary_html}</div></a>'
    )


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


def render_tab_panel(tab, fm):
    html_body = md_to_html(tab["body"])
    html_body, chapters = add_chapter_features(html_body, tab["slug"])
    extras = ""
    if chapters:
        extras += (
            '<div id="bookmarks-panel" class="bookmarks-panel empty">'
            '<div class="bookmarks-panel-title">📌 책갈피</div>'
            '<div class="bookmarks-list"></div>'
            '</div>'
        )
        jumps = "\n".join(
            f'<button class="chapter-jump" data-target="{escape(c["id"])}">{escape(c["title"])}</button>'
            for c in chapters
        )
        extras += (
            '<nav class="chapter-nav">'
            '<div class="chapter-nav-title">⚡ 챕터 빠른 이동</div>'
            f'{jumps}</nav>'
        )
    return f'<div class="tab-panel tab-content" data-tab="{escape(tab["slug"])}">{extras}{html_body}</div>'


def render_game(game, base, user, author):
    fm = game["fm"]
    tabs = game["tabs"]
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
            meta_html += (
                f'<div class="meta-item">'
                f'<span class="meta-label">{label}</span>'
                f'<span class="meta-value">{escape(str(val))}</span></div>\n'
            )

    status = fm.get("status", "")
    status_html = f'<div class="game-status">{escape(status)}</div>' if status else ""

    tab_buttons = "\n".join(
        f'<button class="tab" data-tab="{escape(t["slug"])}">{escape(t["name"])}</button>'
        for t in tabs
    )
    tab_panels = "\n".join(render_tab_panel(t, fm) for t in tabs)

    spoiler_tool = ""
    if fm.get("spoiler"):
        spoiler_tool = (
            '<div class="spoiler-toolbar">'
            '<label class="switch"><input type="checkbox" id="spoiler-switch" />'
            '<span class="slider"></span></label>'
            '<span>스포일러 표시</span></div>'
        )

    spoiler_banner = (
        '<div class="spoiler-banner">⚠️ 스토리 스포일러 포함. 토글로 가려진 텍스트 표시 가능</div>'
        if fm.get("spoiler") else ""
    )

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
        sources_html = (
            f'<section class="sources"><h2>출처</h2>'
            f'<ul class="sources-list">{items}</ul></section>'
        )

    head = HEAD_TPL.format(
        title=f"{fm.get('title', game['slug'])} · Play Archive",
        description=escape(fm.get("summary", "")),
        base=base,
    )
    header = HEADER_TPL.format(base=base, user=user)
    footer = FOOTER_TPL.format(author=escape(author), base=base)

    return f"""{head}{header}
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

  <div class="tabs-wrapper">
    <div class="tabs">{tab_buttons}</div>
  </div>

  <main class="site-main">
    {spoiler_banner}
    {spoiler_tool}
    <div class="tab-panels">
      {tab_panels}
    </div>
    {sources_html}
  </main>
</article>
{footer}"""


def main():
    config = load_config()
    base_raw = config.get("baseurl", "") or ""
    base = base_raw.rstrip("/")
    user = config.get("github_username", "")
    author = config.get("author", "")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    OUT_GAMES.mkdir(parents=True)
    OUT_ASSETS.mkdir(parents=True)

    games = []
    for md_file in sorted(GAMES_DIR.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        slug = md_file.stem
        fm, body = parse_md(md_file)
        if not fm.get("title"):
            continue
        tabs = split_into_tabs(body)
        games.append({"slug": slug, "fm": fm, "body": body, "tabs": tabs})

    games.sort(key=lambda g: g["fm"].get("title", ""))
    for i, g in enumerate(games):
        g["idx"] = i

    (OUT_ASSETS / "style.css").write_text(CSS, encoding="utf-8")
    (OUT_ASSETS / "main.js").write_text(JS, encoding="utf-8")

    img_src = ASSETS_DIR / "images"
    if img_src.exists():
        shutil.copytree(img_src, OUT_ASSETS / "images")

    index_html = render_index(games, config, base, user, author)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    for g in games:
        page = render_game(g, base, user, author)
        (OUT_GAMES / f"{g['slug']}.html").write_text(page, encoding="utf-8")

    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"✅ 빌드 완료: {len(games)} 게임")
    for g in games:
        tab_names = ", ".join(t["name"] for t in g["tabs"])
        print(f"   - {g['slug']}.html ({g['fm'].get('title')}) → 탭: {tab_names}")


if __name__ == "__main__":
    main()
