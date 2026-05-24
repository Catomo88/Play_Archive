
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
  if (window.refreshMenuActiveState) window.refreshMenuActiveState();
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
    if (window.refreshMenuBookmarks) window.refreshMenuBookmarks();
  });
});

refreshBookmarkUI();
if (window.refreshMenuBookmarks) window.refreshMenuBookmarks();

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

// ===== 햄버거 + 슬라이드 사이드 메뉴 (v3) =====
(function () {
  const toggle = document.getElementById('menu-toggle');
  const menu = document.getElementById('side-menu');
  const overlay = document.getElementById('side-menu-overlay');
  const closeBtn = document.getElementById('menu-close');
  if (!toggle || !menu || !overlay) return;

  function openMenu() {
    menu.classList.add('open');
    overlay.classList.add('open');
    menu.setAttribute('aria-hidden', 'false');
    refreshMenuActiveState();
    refreshMenuBookmarks();
  }
  function closeMenu() {
    menu.classList.remove('open');
    overlay.classList.remove('open');
    menu.setAttribute('aria-hidden', 'true');
  }

  toggle.addEventListener('click', openMenu);
  overlay.addEventListener('click', closeMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMenu);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.classList.contains('open')) closeMenu();
  });

  // 메뉴의 카테고리 항목 → 탭 전환 + 닫기
  document.querySelectorAll('.menu-item-tab').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const slug = btn.dataset.tab;
      showTab(slug);
      closeMenu();
    });
  });

  // 현재 활성 탭에 active 클래스
  function refreshMenuActiveState() {
    const activePanel = document.querySelector('.tab-panel.active');
    const activeSlug = activePanel ? activePanel.dataset.tab : null;
    document.querySelectorAll('.menu-item-tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === activeSlug);
    });
  }

  // 메뉴의 책갈피 목록 갱신
  function refreshMenuBookmarks() {
    const list = document.getElementById('menu-bookmarks-list');
    if (!list) return;
    const bookmarks = loadBookmarks();
    if (bookmarks.length === 0) {
      list.innerHTML = '<div class="menu-empty">아직 책갈피가 없습니다</div>';
      return;
    }
    list.innerHTML = '';
    bookmarks.forEach(id => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'menu-item menu-bookmark-item';
      btn.innerHTML = '<span class="icon star">★</span><span class="label">' +
        escapeHtml(getChapterTitle(id)) + '</span>';
      btn.addEventListener('click', e => {
        e.preventDefault();
        // 책갈피는 챕터 탭에 있음 → 탭 전환 후 스크롤
        showTab('chapters');
        setTimeout(() => {
          const target = document.getElementById(id);
          if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
        closeMenu();
      });
      list.appendChild(btn);
    });
  }
  // refreshBookmarkUI에서 호출할 수 있도록 전역 노출
  window.refreshMenuBookmarks = refreshMenuBookmarks;
  window.refreshMenuActiveState = refreshMenuActiveState;

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // 최초 1회
  refreshMenuActiveState();
  refreshMenuBookmarks();
})();

// 기존 책갈피/탭 변경 훅에서 메뉴 갱신 호출
(function () {
  const origRefresh = window.refreshBookmarkUI;
  if (typeof origRefresh === 'function') {
    // (이미 정의된 경우 — 안전장치, 보통 위 IIFE보다 위에 있어서 사용 안됨)
  }
})();

