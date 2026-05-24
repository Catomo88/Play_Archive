
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
        .replace(/\s+/g, '-')
        .replace(/[^\w가-힣-]/g, '');
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
