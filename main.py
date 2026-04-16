"""
차량사고 뉴스 텔레그램 알림 봇
- GitHub Actions용
- 같은 사건 그룹핑 + 일괄 메시지
"""

import json
from pathlib import Path
from datetime import datetime

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    SEARCH_KEYWORDS,
    HIGH_PRIORITY_KEYWORDS,
)
from news_fetcher import fetch_all_news
from telegram_bot import send_news_alerts
from llm_news_filter import filter_news_groups

SENT_FILE = Path(__file__).parent / "sent_news.json"


def load_sent_ids() -> set:
    if SENT_FILE.exists():
        try:
            with open(SENT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('ids', []))
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return set()


def save_sent_ids(ids: set):
    ids_list = list(ids)[-500:]
    with open(SENT_FILE, 'w', encoding='utf-8') as f:
        json.dump({'ids': ids_list, 'updated': datetime.now().isoformat()}, f)


def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] 차량사고 뉴스 검색")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERROR] 토큰/챗ID 없음! GitHub Secrets 확인")
        return

    sent_ids = load_sent_ids()
    news_groups = fetch_all_news(SEARCH_KEYWORDS, HIGH_PRIORITY_KEYWORDS)

    total_articles = sum(g.total_count for g in news_groups)
    new_groups = [g for g in news_groups if g.representative.news_id not in sent_ids]

    print(f"수집: {total_articles}개 기사 → {len(news_groups)}개 사건 / 신규: {len(new_groups)}개 사건")

    # Debug: print titles for diagnosis
    for g in new_groups:
        print(f"  [신규] {g.representative.title}")

    # LLM relevance filter
    if new_groups:
        pre_filter = len(new_groups)
        new_groups = filter_news_groups(new_groups)
        print(f"LLM 필터: {len(new_groups)}/{pre_filter}건 관련 사고")

    if new_groups:
        sent_ids = send_news_alerts(
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
            new_groups,
            sent_ids
        )
        save_sent_ids(sent_ids)

    print("완료")


if __name__ == "__main__":
    main()
