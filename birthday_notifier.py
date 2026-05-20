"""
직원 생일 Slack 알림 봇
- 매일 실행되어 오늘 생일인 직원을 찾아 Slack 채널에 메시지를 전송합니다.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#general")
SPREADSHEET_PATH = os.getenv("SPREADSHEET_PATH", "employees.xlsx")

BIRTHDAY_MESSAGES = [
    "🎂 오늘은 *{name}*님의 생일입니다! 🎉\n모두 함께 축하해 주세요~ 🎁🎊",
    "🎈 *{name}*님, 생일 축하드립니다! 🥳\n행복한 하루 되세요! 🌟",
    "🎉 Happy Birthday! *{name}*님의 특별한 날을 축하합니다! 🎂✨",
]

import random

def load_employees(path: str) -> pd.DataFrame:
    """스프레드시트에서 직원 데이터를 불러옵니다."""
    p = Path(path)
    if not p.exists():
        print(f"[오류] 파일을 찾을 수 없습니다: {path}")
        sys.exit(1)

    if p.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif p.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        print(f"[오류] 지원하지 않는 파일 형식입니다: {p.suffix}")
        sys.exit(1)

    # 필수 컬럼 확인
    required = {"이름", "생일"}
    missing = required - set(df.columns)
    if missing:
        print(f"[오류] 스프레드시트에 다음 컬럼이 없습니다: {missing}")
        print(f"현재 컬럼: {list(df.columns)}")
        sys.exit(1)

    return df


def find_birthdays_today(df: pd.DataFrame) -> list[dict]:
    """오늘 생일인 직원 목록을 반환합니다."""
    today = datetime.now()
    today_month = today.month
    today_day = today.day

    birthdays_today = []

    for _, row in df.iterrows():
        raw = row["생일"]
        if pd.isna(raw):
            continue

        # 날짜 파싱 (다양한 형식 지원)
        try:
            if isinstance(raw, (datetime,)):
                bday = raw
            else:
                bday = pd.to_datetime(str(raw), dayfirst=False)
        except Exception:
            print(f"[경고] 날짜 파싱 실패 (이름: {row['이름']}, 값: {raw})")
            continue

        if bday.month == today_month and bday.day == today_day:
            birthdays_today.append({
                "name": str(row["이름"]).strip(),
                "department": str(row.get("부서", "")).strip() if "부서" in row.index else "",
                "birthday": bday,
            })

    return birthdays_today


def send_slack_message(client: WebClient, person: dict) -> bool:
    """Slack 채널에 생일 축하 메시지를 전송합니다."""
    name = person["name"]
    department = person["department"]

    template = random.choice(BIRTHDAY_MESSAGES)
    text = template.format(name=name)

    if department:
        text += f"\n> 소속: {department}"

    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=text,
            unfurl_links=False,
        )
        print(f"[성공] {name}님 생일 메시지 전송 완료 → {SLACK_CHANNEL}")
        return True
    except SlackApiError as e:
        print(f"[오류] Slack 메시지 전송 실패 ({name}): {e.response['error']}")
        return False


def run():
    if not SLACK_BOT_TOKEN:
        print("[오류] SLACK_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 생일 확인 시작...")

    df = load_employees(SPREADSHEET_PATH)
    birthdays = find_birthdays_today(df)

    if not birthdays:
        print("오늘 생일인 직원이 없습니다.")
        return

    client = WebClient(token=SLACK_BOT_TOKEN)

    print(f"오늘 생일: {len(birthdays)}명")
    for person in birthdays:
        send_slack_message(client, person)


if __name__ == "__main__":
    run()
