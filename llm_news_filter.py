# llm_news_filter.py
import os
import json
import logging
from typing import List

logger = logging.getLogger(__name__)

BATCH_SIZE = 15

_FILTER_PROMPT = """당신은 차량 돌진/충돌 사고 뉴스 분류기입니다.
차량방호 장비 제조사(볼라드, 차량차단기, 방호울타리 등)에게 유의미한 사고 뉴스를 선별합니다.

[RELEVANT 기준 — 아래 중 하나라도 해당하면 RELEVANT]
- 차량이 건물, 상가, 인도, 보행자, 시설물, 학교, 정류장 등에 돌진/충돌한 사고
- 급발진으로 인한 사고
- 음주/무면허/졸음 운전으로 인도/건물/보행자 충돌 사고
- 역주행으로 인한 충돌 사고
- 차량 돌진 사고에 대한 방지 대책/방호시설 관련 보도
- 보행자 보호 시설(볼라드, 방호울타리 등) 관련 보도

[IRRELEVANT 기준 — 아래에 해당하면 IRRELEVANT]
- 해외 사건 (미국, LA, 일본, 중국, 베트남, 대만, 호주, 하노이, 프리웨이 등)
- 연예인/스포츠선수의 음주운전 체포/재판 (사고 없이 단속만 된 경우)
- 보험사기, 운전자 바꿔치기
- 차량 간 단순 추돌 (건물/인도/보행자 피해 없음)
- 사고와 무관한 차량 구매/판매/리콜 뉴스

판단이 애매하면 RELEVANT로 분류하세요.

[기사 목록]
{articles}"""


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    from google import genai
    return genai.Client(api_key=api_key)


def filter_news_groups(groups, fallback_groups=None):
    """
    Filter news groups using Gemini LLM.
    Returns only RELEVANT groups.
    On failure, returns all groups (fail-open for recall).

    Args:
        groups: list of NewsGroup objects
        fallback_groups: if provided, return these on LLM failure
    """
    client = _get_gemini_client()
    if client is None:
        logger.warning("GEMINI_API_KEY not set, skipping LLM filter")
        return groups

    if not groups:
        return groups

    # Build article list for prompt
    articles = []
    for i, g in enumerate(groups, 1):
        title = g.representative.title.split(' - ')[0].strip()
        articles.append(f"{i}. {title}")

    prompt = _FILTER_PROMPT.format(articles="\n".join(articles))

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "decision": {"type": "string", "enum": ["RELEVANT", "IRRELEVANT"]},
                                },
                                "required": ["id", "decision"],
                            },
                        }
                    },
                },
            },
        )

        raw = json.loads(response.text)
        decisions = {}
        for item in raw.get("results", []):
            decisions[item["id"]] = item.get("decision", "RELEVANT")

        # Filter: keep only RELEVANT, default to RELEVANT if missing
        filtered = []
        for i, g in enumerate(groups, 1):
            decision = decisions.get(i, "RELEVANT")
            if decision == "RELEVANT":
                filtered.append(g)
            else:
                logger.info(f"[LLM REJECT] {g.representative.title}")

        logger.info(f"LLM filter: {len(filtered)}/{len(groups)} relevant")
        return filtered

    except Exception as e:
        logger.error(f"LLM filter failed: {e}")
        return groups  # Fail-open
