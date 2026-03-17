import json
import logging
import uuid
from datetime import datetime, timezone

import azure.functions as func

from src.cosmos_client import save_meal_log
from src.date_utils import resolve_meal_date
from src.openai_client import extract_food_data, generate_aoi_reply

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="analyze-meal", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def analyze_meal(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body."}, ensure_ascii=False),
            status_code=400,
            mimetype="application/json",
        )

    user_id = body.get("userId")
    session_id = body.get("sessionId")
    message = body.get("message")
    mood = body.get("mood")
    eaten_at = body.get("eatenAt")
    photo_blob_path = body.get("photoBlobPath")
    photo_url_for_model = body.get("photoUrlForModel")

    if not user_id or not session_id or not message:
        return func.HttpResponse(
            json.dumps(
                {"error": "userId, sessionId, message are required."},
                ensure_ascii=False,
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        assistant_reply = generate_aoi_reply(
            message=message,
            mood=mood,
            eaten_at=eaten_at,
        )
        food_data = extract_food_data(
            message=message,
            mood=mood,
            eaten_at=eaten_at,
            photo_url_for_model=photo_url_for_model,
        )

        now_iso = datetime.now(timezone.utc).astimezone().isoformat()
        meal_date = resolve_meal_date(food_data.get("meal_date_hint"), eaten_at)

        document = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "sessionId": session_id,
            "recordType": "meal_log",
            "schemaVersion": "1.0.0",
            "recordedAt": now_iso,
            "updatedAt": now_iso,
            "mealDate": meal_date,
            "mealDateHint": food_data.get("meal_date_hint"),
            "mealType": food_data.get("meal_type"),
            "eatenAt": eaten_at,
            "timezone": "Asia/Tokyo",
            "input": {
                "userMessage": message,
                "mood": mood,
                "photoProvided": bool(photo_blob_path),
            },
            "photo": {
                "blobPath": photo_blob_path,
                "contentType": None,
            },
            "foods": food_data.get("foods", []),
            "context": {
                "location": food_data.get("location"),
                "eatingCompanions": food_data.get("eating_companions"),
            },
            "debq": {
                "emotionRaw": food_data.get("emotion_raw"),
                "triggerRaw": food_data.get("trigger_raw"),
                "signals": food_data.get("debq_signals"),
            },
            "extraction": {
                "confidence": food_data.get("extraction_confidence"),
                "dietitianMemo": food_data.get("dietitian_memo"),
                "modelName": "gpt-4.1",
                "deploymentName": body.get("extractDeployment") or "configured-via-env",
                "promptVersion": "extract-v1",
            },
            "assistant": {
                "persona": "aoi",
                "reply": assistant_reply,
            },
            "flags": {
                "manualCorrected": False,
                "dateCorrectedLater": False,
                "isDeleted": False,
            },
        }

        save_meal_log(document)

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "assistantReply": assistant_reply,
                    "foodData": food_data,
                    "savedId": document["id"],
                },
                ensure_ascii=False,
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as exc:
        logging.exception("analyze-meal failed")
        return func.HttpResponse(
            json.dumps(
                {"error": "Internal Server Error", "detail": str(exc)},
                ensure_ascii=False,
            ),
            status_code=500,
            mimetype="application/json",
        )
