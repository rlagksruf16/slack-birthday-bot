#!/bin/bash
# 매일 오전 9시에 생일 알림을 실행하는 cron 작업을 등록합니다.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"
LOG_FILE="$SCRIPT_DIR/birthday_notifier.log"

# 실행할 cron 명령어 (매일 오전 9시)
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_DIR/birthday_notifier.py >> $LOG_FILE 2>&1"

# 기존 crontab에 추가 (중복 방지)
(crontab -l 2>/dev/null | grep -v "birthday_notifier"; echo "$CRON_JOB") | crontab -

echo "✅ cron 등록 완료!"
echo "   실행 시간: 매일 오전 9:00"
echo "   로그 파일: $LOG_FILE"
echo ""
echo "현재 crontab 확인:"
crontab -l | grep birthday_notifier
