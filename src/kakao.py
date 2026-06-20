import json
import requests


def refresh_access_token(rest_api_key: str, refresh_token: str) -> str:
    """refresh_token으로 새 access_token을 발급받는다."""
    response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": rest_api_key,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def send_message(access_token: str, text: str) -> None:
    """카카오 나에게 보내기 API로 메시지를 전송한다."""
    template = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": "", "mobile_web_url": ""},
    }
    response = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=10,
    )
    response.raise_for_status()
