# 차량사고 뉴스 봇 — 운영 이관 완료

2026-10-14부터 뉴스 수집·전송은 비공개 통합 알림 저장소에서 운영합니다. 발송 이력은 입찰과 함께 암호화하여 보존하며, 이 저장소의 예약 및 직접 실행 발송은 중지했습니다.

기존 코드는 이전 동작 확인을 위해 보존했습니다. 아래 문서는 과거 배포 방법이며 현재 운영 절차가 아닙니다. 이전 워크플로를 다시 켜지 마세요.

---

# 🚗 차량사고 뉴스 텔레그램 알림 봇

5분마다 자동으로 차량사고 뉴스를 검색해서 텔레그램으로 알림!

---

## 🚀 GitHub 배포 가이드 (10분)

### 1단계: 텔레그램 봇 만들기

1. 텔레그램 → **@BotFather** 검색 → `/newbot`
2. 봇 이름/username 입력
3. **토큰** 복사 (예: `7123456789:AAHxxxx...`)
4. 만든 봇에 아무 메시지 보내기
5. 브라우저에서 Chat ID 확인:
   ```
   https://api.telegram.org/bot여기에토큰/getUpdates
   ```
   → `"chat":{"id": 숫자}` 에서 숫자가 Chat ID

---

### 2단계: GitHub 저장소 만들기

1. https://github.com 로그인
2. 오른쪽 위 **+** → **New repository**
3. Repository name: `vehicle-accident-bot`
4. **Private** 선택 (권장)
5. **Create repository** 클릭

---

### 3단계: 파일 업로드

1. 생성된 저장소에서 **uploading an existing file** 클릭
2. 압축 풀어서 **모든 파일/폴더** 드래그 앤 드롭
   - `.github` 폴더 (숨김폴더!)
   - `config.py`
   - `main.py`
   - `news_fetcher.py`
   - `telegram_bot.py`
   - `requirements.txt`
   - `sent_news.json`
3. **Commit changes** 클릭

⚠️ **중요**: `.github` 폴더가 안 보이면 파일 탐색기에서 "숨김 항목 표시" 켜기!

---

### 4단계: Secrets 설정 (토큰 입력)

1. 저장소 → **Settings** 탭
2. 왼쪽 메뉴 **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. 두 개 추가:

| Name | Secret |
|------|--------|
| `TELEGRAM_BOT_TOKEN` | 봇 토큰 (예: `7123456789:AAHxxxx...`) |
| `TELEGRAM_CHAT_ID` | 챗 ID (예: `123456789`) |

---

### 5단계: Actions 활성화

1. 저장소 → **Actions** 탭
2. **I understand my workflows, go ahead and enable them** 클릭
3. 왼쪽에서 **차량사고 뉴스 알림** 클릭
4. **Run workflow** → **Run workflow** 클릭해서 테스트

✅ 텔레그램에 알림 오면 성공!

---

## ⏰ 실행 주기

- **5분마다** 자동 실행
- 새 뉴스가 있을 때만 알림
- 중복 뉴스 자동 필터링

---

## 📁 파일 구조

```
vehicle-accident-bot/
├── .github/
│   └── workflows/
│       └── news_alert.yml   ← 자동 실행 설정
├── config.py
├── main.py
├── news_fetcher.py
├── telegram_bot.py
├── requirements.txt
└── sent_news.json           ← 전송 기록 (자동 업데이트)
```

---

## ❓ 문제 해결

**알림이 안 와요**
→ Actions 탭에서 실행 로그 확인
→ Secrets 설정 다시 확인

**Actions가 비활성화됐어요**
→ 60일 동안 커밋 없으면 자동 비활성화
→ 아무 파일이나 수정해서 커밋하면 재활성화
