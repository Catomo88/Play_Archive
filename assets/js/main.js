// =============================================================
// Play Archive — 인터랙션
// =============================================================

(function () {
  'use strict';

  // ---------------------------------------------------------
  // 1) 게임 검색 (메인 페이지)
  // ---------------------------------------------------------
  const search = document.getElementById('game-search');
  const grid = document.getElementById('games-grid');

  if (search && grid) {
    search.addEventListener('input', function (e) {
      const q = e.target.value.trim().toLowerCase();
      const cards = grid.querySelectorAll('.game-card');
      cards.forEach(function (card) {
        const title = card.getAttribute('data-game-title') || '';
        const genre = card.getAttribute('data-game-genre') || '';
        const match = !q || title.includes(q) || genre.includes(q);
        card.style.display = match ? '' : 'none';
      });
    });
  }

  // ---------------------------------------------------------
  // 2) 게임 페이지 — 목차 자동 생성
  // ---------------------------------------------------------
  const tocNav = document.getElementById('toc-nav');
  const content = document.querySelector('.game-content');

  if (tocNav && content) {
    const headings = content.querySelectorAll('h2, h3');
    if (headings.length === 0) {
      const tocAside = document.getElementById('game-toc');
      if (tocAside) tocAside.style.display = 'none';
    } else {
      headings.forEach(function (h) {
        if (!h.id) {
          h.id = h.textContent
            .trim()
            .toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/[^\w가-힣-]/g, '');
        }
        const link = document.createElement('a');
        link.href = '#' + h.id;
        link.textContent = h.textContent;
        link.className = h.tagName === 'H3' ? 'toc-h3' : 'toc-h2';
        tocNav.appendChild(link);
      });

      // 스크롤 시 현재 섹션 하이라이트
      const observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            const id = entry.target.id;
            const link = tocNav.querySelector('a[href="#' + id + '"]');
            if (!link) return;
            if (entry.isIntersecting) {
              tocNav.querySelectorAll('a').forEach(function (a) {
                a.classList.remove('active');
              });
              link.classList.add('active');
            }
          });
        },
        { rootMargin: '-80px 0px -70% 0px' }
      );
      headings.forEach(function (h) { observer.observe(h); });
    }
  }

  // ---------------------------------------------------------
  // 3) 스포일러 토글
  // ---------------------------------------------------------
  const spoilerSwitch = document.getElementById('spoiler-switch');
  if (spoilerSwitch) {
    const saved = localStorage.getItem('show-spoilers') === '1';
    spoilerSwitch.checked = saved;
    document.body.classList.toggle('show-spoilers', saved);

    spoilerSwitch.addEventListener('change', function () {
      document.body.classList.toggle('show-spoilers', spoilerSwitch.checked);
      localStorage.setItem('show-spoilers', spoilerSwitch.checked ? '1' : '0');
    });
  }

  // ---------------------------------------------------------
  // 4) 인라인 스포일러 클릭으로 표시
  // ---------------------------------------------------------
  document.addEventListener('click', function (e) {
    const target = e.target;
    if (target && target.classList && target.classList.contains('spoiler')) {
      target.classList.add('revealed');
      target.style.background = 'transparent';
      target.style.color = 'inherit';
    }
  });

  // ---------------------------------------------------------
  // 5) 체크리스트 상태 localStorage 저장 (게임별)
  // ---------------------------------------------------------
  if (content) {
    const slug = window.location.pathname;
    const checkboxes = content.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(function (cb, idx) {
      const key = 'check:' + slug + ':' + idx;
      const saved = localStorage.getItem(key);
      if (saved === '1') cb.checked = true;
      cb.addEventListener('change', function () {
        localStorage.setItem(key, cb.checked ? '1' : '0');
      });
    });
  }
})();
