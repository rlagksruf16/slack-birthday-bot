"""
직원 생일 Slack 알림 봇
- Google Sheets에서 직원 데이터를 읽어 오늘 생일인 직원에게 Slack 메시지를 전송합니다.
"""

import json
import os
import random
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

NAME_COL      = "영문이름"
BIRTHDAY_COL  = "생년월일"
HEADER_ROW    = 2   # 헤더가 2행에 있음

BIRTHDAY_MESSAGES = [
    "🎂 오늘은 *{name}*님의 생일입니다! 🎉\n모두 함께 축하해 주세요~ 🎁🎊",
    "🎈 *{name}*님, 생일 축하드립니다! 🥳\n행복한 하루 되세요! 🌟",
    "🎉 Happy Birthday! *{name}*님의 특별한 날을 축하합니다! 🎂✨",
]


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

    headers = all_values[HEADER_ROW - 1]   # 0-indexed → row 2 = index 1
    data_rows = all_values[HEADER_ROW:]     # 데이터는 3행부터

    # 필수 컬럼 인덱스 확인
    try:
        name_idx = headers.index(NAME_COL)
        bday_idx = headers.index(BIRTHDAY_COL)
    except ValueError as e:
        print(f"[오류] 컬럼을 찾을 수 없습니다: {e}")
        print(f"현재 헤더: {headers}")
        sys.exit(1)

    records = []
    for row in data_rows:
        if len(row) <= max(name_idx, bday_idx):
            continue
        name = row[name_idx].strip()
        birthday = row[bday_idx].strip()
        if name and birthday and name != NAME_COL:
            records.append({"name": name, "birthday": birthday})

    return records


def find_birthdays_today(records: list[dict]) -> list[dict]:
    """오늘 생일인 직원 목록을 반환합니다."""
    today = datetime.now()
    result = []

    for r in records:
        try:
            bday = datetime.strptime(r["birthday"], "%Y-%m-%d")
        except ValueError:
            print(f"[경고] 날짜 파싱 실패 (이름: {r['name']}, 값: {r['birthday']})")
            continue

        if bday.month == today.month and bday.day == today.day:
            result.append(r)

    return result


def send_slack_message(client: WebClient, person: dict) -> bool:
    """Slack 채널에 생일 축하 메시지를 전송합니다."""
    text = random.choice(BIRTHDAY_MESSAGES).format(name=person["name"])

    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=text, unfurl_links=False)
        print(f"[성공] {person['name']}님 생일 메시지 전송 완료 → {SLACK_CHANNEL}")
        return True
    except SlackApiError as e:
        print(f"[오류] Slack 메시지 전송 실패 ({person['name']}): {e.response['error']}")
        return False


def run():
    if not SLACK_BOT_TOKEN:
        print("[오류] SLACK_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 생일 확인 시작...")

    records = get_sheet_data()
    print(f"총 직원 수: {len(records)}명")

    birthdays = find_birthdays_today(records)

    if not birthdays:
        print("오늘 생일인 직원이 없습니다.")
        return

    client = WebClient(token=SLACK_BOT_TOKEN)
    print(f"오늘 생일: {len(birthdays)}명")
    for person in birthdays:
        send_slack_message(client, person)


if __name__ == "__main__":
    run()
