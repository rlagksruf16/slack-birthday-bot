"""
직원 생일 & 입사 기념일 Slack 알림 봇
- Google Sheets에서 직원 데이터를 읽어 오늘 생일/기념일인 직원에게 Slack 메시지를 전송합니다.
"""

import json
import os
import sys
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN   = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL     = os.getenv("SLACK_CHANNEL", "#general")
GOOGLE_SHEET_ID   = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Employee Data")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

NAME_COL        = "영문이름"
BIRTHDAY_COL    = "생년월일"
JOIN_DATE_COL   = "입사일"
HEADER_ROW      = 2

BIRTHDAY_MESSAGE = (
    "*[ 공지 | 🎂 생일 안내 ]*\n\n"
    ":tada::tada: 오늘은 *{name}*​의 생일입니다 :tada::tada:\n\n"
    ":confetti_ball: *{name}*​가 오늘 행복한 하루를 보낼 수 있도록 다 같이 축하해 주세요 :gift:"
)

ANNIVERSARY_MESSAGE = (
    "*[ 공지 | 🎊 입사 기념일 안내 ]*\n\n"
    "🏆 오늘은 *{name}*​님의 입사 *{years}*​주년 기념일입니다!\n\n"
    "ALLSALE과 *{years}*​년 동안 함께해 주셔서 감사합니다\n"
    ":allsale: 앞으로도 잘 부탁드리며, 모두 *{name}*​님에게 응원의 한마디 부탁드려요! 🙌"
)

# IMAGE_URL = (
#     "https://raw.githubusercontent.com/rlagksruf16/"
#     "slack-birthday-bot/main/ALLSALE_HBD.png"
# )
# IMAGE_URL = (
#     "https://raw.githubusercontent.com/rlagksruf16/"
#     "slack-birthday-bot/main/HBD_photo.jpg"
# )


def get_sheet_data() -> list[dict]:
    """Google Sheets에서 직원 데이터를 읽어 dict 리스트로 반환합니다."""
    if not GOOGLE_CREDS_JSON:
        print("[오류] GOOGLE_CREDENTIALS_JSON 환경변수가 설정되지 않았습니다.")
        sys.exit(1)
    if not GOOGLE_SHEET_ID:
        print("[오류] GOOGLE_SHEET_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    creds = Credentials.from_service_account_info(
        json.loads(GOOGLE_CREDS_JSON),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(GOOGLE_SHEET_NAME)

    all_values = worksheet.get_all_values()

    if len(all_values) < HEADER_ROW:
        print("[오류] 시트에 데이터가 없습니다.")
        sys.exit(1)

    headers = all_values[HEADER_ROW - 1]
    data_rows = all_values[HEADER_ROW:]

    try:
        name_idx     = headers.index(NAME_COL)
        bday_idx     = headers.index(BIRTHDAY_COL)
        join_idx     = headers.index(JOIN_DATE_COL)
    except ValueError as e:
        print(f"[오류] 컬럼을 찾을 수 없습니다: {e}")
        print(f"현재 헤더: {headers}")
        sys.exit(1)

    records = []
    for row in data_rows:
        if any("퇴사자" in str(cell) for cell in row):
            break

        if len(row) <= max(name_idx, bday_idx, join_idx):
            continue
        name      = row[name_idx].strip()
        birthday  = row[bday_idx].strip()
        join_date = row[join_idx].strip()
        if name and name != NAME_COL:
            records.append({
                "name":      name,
                "birthday":  birthday,
                "join_date": join_date,
            })

    return records


def find_birthdays_today(records: list[dict]) -> list[dict]:
    """오늘 생일인 직원 목록을 반환합니다."""
    today = datetime.now()
    result = []
    for r in records:
        try:
            bday = datetime.strptime(r["birthday"], "%Y-%m-%d")
        except ValueError:
            continue
        if bday.month == today.month and bday.day == today.day:
            result.append(r)
    return result


def find_anniversaries_today(records: list[dict]) -> list[dict]:
    """오늘 입사 기념일(1주년 이상)인 직원 목록을 반환합니다."""
    today = datetime.now()
    result = []
    for r in records:
        if not r["join_date"]:
            continue
        try:
            join = datetime.strptime(r["join_date"], "%Y-%m-%d")
        except ValueError:
            continue
        years = today.year - join.year
        if years >= 1 and join.month == today.month and join.day == today.day:
            result.append({**r, "years": years})
    return result


def send_birthday_message(client: WebClient, person: dict) -> bool:
    """Slack 채널에 생일 축하 메시지를 전송합니다."""
    text = BIRTHDAY_MESSAGE.format(name=person["name"])
    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=text,
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": text}}],
            unfurl_links=False,
        )
        print(f"[성공] {person['name']}님 생일 메시지 전송 완료 → {SLACK_CHANNEL}")
        return True
    except SlackApiError as e:
        print(f"[오류] 생일 메시지 전송 실패 ({person['name']}): {e.response['error']}")
        return False


def send_anniversary_message(client: WebClient, person: dict) -> bool:
    """Slack 채널에 입사 기념일 메시지를 전송합니다."""
    text = ANNIVERSARY_MESSAGE.format(name=person["name"], years=person["years"])
    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=text,
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": text}}],
            unfurl_links=False,
        )
        print(f"[성공] {person['name']}님 {person['years']}주년 메시지 전송 완료 → {SLACK_CHANNEL}")
        return True
    except SlackApiError as e:
        print(f"[오류] 기념일 메시지 전송 실패 ({person['name']}): {e.response['error']}")
        return False


def run():
    if not SLACK_BOT_TOKEN:
        print("[오류] SLACK_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 확인 시작...")

    records = get_sheet_data()
    print(f"총 직원 수: {len(records)}명")

    client = WebClient(token=SLACK_BOT_TOKEN)

    # 생일 확인
    birthdays = find_birthdays_today(records)
    if birthdays:
        print(f"오늘 생일: {len(birthdays)}명")
        for person in birthdays:
            send_birthday_message(client, person)
    else:
        print("오늘 생일인 직원이 없습니다.")

    # 입사 기념일 확인
    anniversaries = find_anniversaries_today(records)
    if anniversaries:
        print(f"오늘 입사 기념일: {len(anniversaries)}명")
        for person in anniversaries:
            send_anniversary_message(client, person)
    else:
        print("오늘 입사 기념일인 직원이 없습니다.")


if __name__ == "__main__":
    run()
