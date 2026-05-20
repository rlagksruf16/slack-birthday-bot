# Slack 생일 알림 봇

직원 생일 스프레드시트를 읽어 매일 자동으로 Slack 채널에 생일 축하 메시지를 보내는 툴입니다.

## 빠른 시작

### 1. 패키지 설치

```bash
cd slack-birthday-bot
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 값들을 채웁니다:

| 변수 | 설명 |
|------|------|
| `SLACK_BOT_TOKEN` | Slack Bot Token (`xoxb-...`) |
| `SLACK_CHANNEL` | 메시지 전송 채널 (예: `#생일축하`) |
| `SPREADSHEET_PATH` | 엑셀/CSV 파일 경로 |

### 3. Slack 앱 설정

1. [https://api.slack.com/apps](https://api.slack.com/apps) 접속 → **Create New App**
2. **OAuth & Permissions** → Bot Token Scopes에 `chat:write` 추가
3. 워크스페이스에 앱 설치 → **Bot User OAuth Token** 복사 → `.env`에 붙여넣기
4. 알림 채널에 봇을 초대: `/invite @봇이름`

### 4. 직원 스프레드시트 준비

엑셀(`.xlsx`) 또는 CSV 파일에 아래 컬럼이 필요합니다:

| 이름 | 부서 | 생일 | 이메일 |
|------|------|------|--------|
| 김철수 | 개발팀 | 1990-05-20 | ... |

- **필수 컬럼**: `이름`, `생일`
- **선택 컬럼**: `부서`, `이메일`
- 생일 형식: `YYYY-MM-DD`, `MM/DD/YYYY`, `YYYY.MM.DD` 모두 지원

샘플 파일 생성:
```bash
python create_sample_spreadsheet.py
```

### 5. 테스트 실행

```bash
python birthday_notifier.py
```

### 6. 매일 자동 실행 (cron 등록)

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

기본 실행 시간: **매일 오전 9:00**

실행 시간을 바꾸려면 `setup_cron.sh`에서 `0 9 * * *` 부분을 수정하세요.  
([cron 표현식 참고](https://crontab.guru))

## 로그 확인

```bash
tail -f birthday_notifier.log
```

## Slack 메시지 예시

```
🎂 오늘은 *김철수*님의 생일입니다! 🎉
모두 함께 축하해 주세요~ 🎁🎊
> 소속: 개발팀
```
