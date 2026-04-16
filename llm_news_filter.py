# llm_news_filter.py
import os
import json
import logging
from typing import List

logger = logging.getLogger(__name__)

BATCH_SIZE = 15

_FILTER_PROMPT = """당신은 차량 돌진 사고 뉴스 분류기입니다.
차량방호 장비 제조사(볼라드, 차량차단기 등)에게 유의미한 사고 뉴스만 선별합니다.

[판단 기준]
각 기사가 아래 3가지를 모두 만족하면 RELEVANT, 하나라도 불만족하면 IRRELEVANT:
1. 국내(한국) 사건인가? (해외 사건 제외 — LA, 미국, 일본, 중국, 베트남, 대만, 호주 등)
2. 차량이 건물, 상가, 인도, 보행자, 시설물, 학교 등에 물리적으로 돌진/충돌한 사고인가?
3. 실제 사고 보도인가? (아래는 모두 IRRELEVANT)
   - 재판/판결/구형/항소
   - 정책/제도/법안 발표
   - 연예인/스포츠선수 음주운전
   - 보험사기/운전자 바꿔치기
   - 단순 교통법규 위반 (무면허, 음주 단속)
   - 단순 차량 간 추돌 (건물/인도 돌진 아님)
   - 사고 후 도로 개선/시설 설치 등 후속 조치

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
