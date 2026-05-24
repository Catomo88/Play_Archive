# =============================================================
# Play Archive - GitHub 저장소 초기 설정 스크립트
# =============================================================
# 실행 방법:
#   1) PowerShell을 열고 이 폴더로 이동
#      cd "C:\Users\ljk90\OneDrive\문서\Claude\Projects\Play_Archive"
#   2) 실행 정책 임시 허용
#      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   3) 스크립트 실행
#      ./setup-github.ps1
# =============================================================

Write-Host ""
Write-Host "=== Play Archive GitHub 초기화 시작 ===" -ForegroundColor Cyan
Write-Host ""

# 0) 필수 도구 확인
Write-Host "[1/7] git, gh 설치 확인..." -ForegroundColor Yellow
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  [에러] git이 설치되어 있지 않습니다." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "  [에러] GitHub CLI(gh)가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "  설치: winget install --id GitHub.cli"
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# 1) gh 인증 확인
Write-Host "[2/7] GitHub 인증 확인..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  GitHub 인증이 안 되어 있습니다. 로그인을 진행합니다..." -ForegroundColor Yellow
    gh auth login
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
$ghUser = (gh api user --jq '.login')
Write-Host "  로그인 사용자: $ghUser" -ForegroundColor Green

# 2) git 초기화
Write-Host "[3/7] git 저장소 초기화..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    git init -b main | Out-Null
    Write-Host "  git init 완료" -ForegroundColor Green
} else {
    Write-Host "  이미 git 저장소가 있습니다 (skip)" -ForegroundColor Gray
}

# 3) 첫 커밋
Write-Host "[4/7] 파일 스테이징 및 커밋..." -ForegroundColor Yellow
git add .
$diff = git diff --cached --name-only
if ([string]::IsNullOrWhiteSpace($diff)) {
    Write-Host "  커밋할 변경사항이 없습니다 (skip)" -ForegroundColor Gray
} else {
    git commit -m "Initial commit: Jekyll skeleton for Play Archive" | Out-Null
    Write-Host "  첫 커밋 완료" -ForegroundColor Green
}

# 4) 원격 저장소 생성
Write-Host "[5/7] GitHub 저장소 생성 (play-archive, public)..." -ForegroundColor Yellow
$repoCheck = gh repo view "$ghUser/play-archive" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  저장소가 이미 존재합니다. 원격만 연결합니다." -ForegroundColor Gray
    $existingRemote = git remote get-url origin 2>$null
    if (-not $existingRemote) {
        git remote add origin "https://github.com/$ghUser/play-archive.git"
    }
} else {
    gh repo create play-archive --public --source=. --remote=origin --description "내 게임 100% 공략 아카이브" --disable-wiki | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [에러] 저장소 생성 실패" -ForegroundColor Red
        exit 1
    }
    Write-Host "  저장소 생성 완료" -ForegroundColor Green
}

# 5) 푸시
Write-Host "[6/7] main 브랜치 푸시..." -ForegroundColor Yellow
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [에러] 푸시 실패" -ForegroundColor Red
    exit 1
}
Write-Host "  푸시 완료" -ForegroundColor Green

# 6) GitHub Pages 활성화
Write-Host "[7/7] GitHub Pages 활성화..." -ForegroundColor Yellow
$pagesResult = gh api -X POST "repos/$ghUser/play-archive/pages" -f "source[branch]=main" -f "source[path]=/" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Pages 활성화 완료" -ForegroundColor Green
} else {
    if ($pagesResult -match "already exists") {
        Write-Host "  이미 활성화되어 있습니다 (skip)" -ForegroundColor Gray
    } else {
        Write-Host "  Pages 활성화 응답: $pagesResult" -ForegroundColor Yellow
        Write-Host "  수동으로 확인: GitHub 저장소 > Settings > Pages" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== 완료 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "저장소: https://github.com/$ghUser/play-archive" -ForegroundColor White
Write-Host "사이트: https://$ghUser.github.io/play-archive/" -ForegroundColor White
Write-Host ""
Write-Host "GitHub Pages 빌드는 1~2분 정도 소요됩니다." -ForegroundColor Gray
Write-Host "배포 상태 확인: gh run list -R $ghUser/play-archive" -ForegroundColor Gray
Write-Host ""
