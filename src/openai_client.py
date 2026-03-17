import json
import os
from typing import Optional

from openai import OpenAI

from src.prompts import AOI_PERSONA_PROMPT, EXTRACTION_SYSTEM_PROMPT


def _base_url() -> str:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    return f"{endpoint}/openai/v1/"


def _client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        base_url=_base_url(),
    )


def _food_data_schema() -> dict:
    return {
        "name": "food_data_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foods": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "group": {
                                "type": "string",
                                "enum": ["主食", "肉類", "魚介", "野菜", "乳類", "油脂", "果物", "その他"],
                            },
                            "amount": {"type": "string"},
                        },
                        "required": ["name", "group", "amount"],
                    },
                },
                "meal_date_hint": {"type": ["string", "null"]},
                "meal_type": {
                    "type": "string",
                    "enum": ["朝食", "昼食", "間食", "夕食", "夜食"],
                },
                "location": {
                    "type": "string",
                    "enum": ["自宅", "外食", "職場", "不明"],
                },
                "eating_companions": {
                    "type": "string",
                    "enum": ["一人", "家族", "同僚", "友人", "不明"],
                },
                "emotion_raw": {"type": ["string", "null"]},
                "trigger_raw": {"type": ["string", "null"]},
                "debq_signals": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "emotional": {"type": "boolean"},
                        "external": {"type": "boolean"},
                        "restrained": {"type": "boolean"},
                    },
                    "required": ["emotional", "external", "restrained"],
                },
                "extraction_confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "dietitian_memo": {"type": "string"},
            },
            "required": [
                "foods",
                "meal_date_hint",
                "meal_type",
                "location",
                "eating_companions",
                "emotion_raw",
                "trigger_raw",
                "debq_signals",
                "extraction_confidence",
                "dietitian_memo",
            ],
        },
    }


def generate_aoi_reply(message: str, mood: Optional[str], eaten_at: Optional[str]) -> str:
    client = _client()
    deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": AOI_PERSONA_PROMPT},
            {
                "role": "user",
                "content": f"ユーザー発話: {message}\n気分: {mood or '不明'}\n食べた時刻: {eaten_at or '不明'}",
            },
        ],
        temperature=0.8,
        max_tokens=180,
    )
    return (response.choices[0].message.content or "").strip()


def extract_food_data(
    message: str,
    mood: Optional[str],
    eaten_at: Optional[str],
    photo_url_for_model: Optional[str] = None,
) -> dict:
    client = _client()
    deployment = os.environ["AZURE_OPENAI_EXTRACT_DEPLOYMENT"]

    user_content = [
        {
            "type": "text",
            "text": f"ユーザー発話: {message}\n気分: {mood or '不明'}\n食べた時刻: {eaten_at or '不明'}",
        }
    ]

    if photo_url_for_model:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": photo_url_for_model},
            }
        )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": _food_data_schema(),
        },
        temperature=0,
        max_tokens=500,
    )

    content = response.choices[0].message.content or "{}"
    return json.loads(content)
