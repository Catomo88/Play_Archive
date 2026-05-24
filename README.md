# Play Archive

> 내가 플레이한 게임들의 100% 공략 아카이브

Jekyll + GitHub Pages 기반의 게임 공략 정적 사이트. 한국어 위키/커뮤니티 자료를 기반으로 챕터별 공략, 업적 100% 가이드, 히든 요소(장소·아이템·보스) 파훼법을 정리합니다.

## 구조

```
play-archive/
├── _config.yml              Jekyll 설정
├── index.md                 메인 페이지 (게임 카드 그리드)
├── _layouts/
│   ├── default.html         공통 레이아웃 (다크 테마)
│   ├── home.html            메인 페이지
│   └── game.html            게임 공략 페이지
├── _includes/
│   ├── header.html / footer.html / game-card.html
├── _games/
│   ├── _TEMPLATE.md         새 공략 추가 시 복사할 템플릿
│   └── *.md                 각 게임별 공략
├── assets/
│   ├── css/style.scss       다크 테마 + 게임 감성 스타일
│   ├── js/main.js           검색, TOC, 스포일러, 체크리스트
│   └── images/games/        게임 키 비주얼
└── README.md
```

## 새 게임 공략 추가하기

1. `_games/_TEMPLATE.md`를 복사해 새 파일 생성 (파일명은 영문 슬러그)
   - 예: `_games/elden-ring.md`, `_games/baldurs-gate-3.md`
2. front matter(상단 메타 정보)를 채움
3. 본문에 챕터별 공략, 업적 가이드, 히든 요소 등을 작성
4. 키 비주얼 이미지를 `assets/images/games/`에 저장하고 `cover` 경로 지정
5. `git add → commit → push` → GitHub Pages가 자동 빌드/배포

### Front matter 필드

| 필드 | 설명 |
|---|---|
| `title` | 게임 제목 (필수) |
| `subtitle` | 부제 |
| `genre` | 장르 |
| `developer` / `publisher` | 개발사 / 퍼블리셔 |
| `release` | 발매일 |
| `platform` | 플랫폼 |
| `difficulty` | 난이도 (별점 표기 가능) |
| `playtime` | 본편/100% 플레이타임 |
| `status` | `완료` / `진행중` / `계획` |
| `cover` | 카드/헤더 배경 이미지 경로 |
| `summary` | 카드에 표시될 한 줄 요약 |
| `spoiler` | `true`면 스포일러 토글 표시 |
| `sources` | 참고 출처 목록 (제목/URL/메모) |

### 본문에서 쓸 수 있는 박스

```markdown
<div class="tip" markdown="1">팁 (녹색)</div>
<div class="warn" markdown="1">주의 (주황)</div>
<div class="boss" markdown="1">보스 정보 (빨강)</div>
<div class="secret" markdown="1">히든 요소 (자홍)</div>
```

### 인라인 스포일러

```markdown
<span class="spoiler">진실은 ○○입니다</span>
```

가린 상태로 표시되며, 클릭 또는 사이드바의 스포일러 토글로 공개됩니다.

### 체크리스트

```markdown
- [ ] 수집 아이템 1
- [ ] 수집 아이템 2
```

체크 상태는 브라우저 `localStorage`에 게임별로 저장됩니다.

## 로컬 미리보기

Jekyll 환경이 설치되어 있다면:

```bash
bundle install
bundle exec jekyll serve
# http://localhost:4000/play-archive/ 접속
```

설치되어 있지 않다면 푸시 후 GitHub Pages 빌드 결과로 확인하면 됩니다 (보통 1~2분 소요).

## GitHub Pages 배포

저장소 Settings → Pages → Source를 **"Deploy from a branch"** / **`main` / `/ (root)`** 로 설정하면 자동 배포됩니다.

배포 URL: `https://<username>.github.io/play-archive/`

## 라이선스

공략 텍스트는 출처를 명시한 한국 위키/커뮤니티 자료를 기반으로 재정리되었습니다. 개인 학습 및 비상업적 공유 목적으로 사용해주세요.
