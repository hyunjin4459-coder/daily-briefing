import requests

_API = "https://api.telegram.org/bot{token}/sendMessage"
_MAX = 4000  # Telegram 한 메시지 최대 4096자, 여유 두고 4000


def send_message(token: str, chat_id: str, text: str) -> None:
    """텔레그램 봇으로 메시지 전송. 4000자 초과 시 자동 분할."""
    chunks = [text[i:i + _MAX] for i in range(0, len(text), _MAX)]
    for chunk in chunks:
        resp = requests.post(
            _API.format(token=token),
            json={"chat_id": chat_id, "text": chunk},
            timeout=10,
        )
        resp.raise_for_status()
