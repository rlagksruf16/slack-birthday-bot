"""
샘플 직원 스프레드시트(employees.xlsx)를 생성하는 스크립트입니다.
처음 설정할 때 한 번 실행하여 템플릿을 만드세요.
"""

import pandas as pd
from datetime import date

sample_data = {
    "이름": ["김철수", "이영희", "박민준", "최수진", "홍길동"],
    "부서": ["개발팀", "마케팅팀", "디자인팀", "인사팀", "영업팀"],
    "생일": [
        date(1990, 5, 20),   # 오늘 날짜로 테스트해 보세요
        date(1992, 3, 15),
        date(1988, 7, 4),
        date(1995, 11, 22),
        date(1985, 1, 8),
    ],
    "이메일": [
        "chulsoo@company.com",
        "younghee@company.com",
        "minjun@company.com",
        "sujin@company.com",
        "gildong@company.com",
    ],
}

df = pd.DataFrame(sample_data)
df.to_excel("employees.xlsx", index=False)
print("employees.xlsx 생성 완료!")
print(df.to_string(index=False))
