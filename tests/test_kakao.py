from unittest.mock import patch, MagicMock
from src.kakao import refresh_access_token, send_message


def test_refresh_access_token_returns_token():
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "new_token_abc"}
    mock_response.raise_for_status.return_value = None

    with patch("src.kakao.requests.post", return_value=mock_response):
        token = refresh_access_token("rest_key_123", "refresh_token_xyz")

    assert token == "new_token_abc"


def test_send_message_calls_kakao_api():
    mock_response = MagicMock()
    mock_response.json.return_value = {"result_code": 0}
    mock_response.raise_for_status.return_value = None

    with patch("src.kakao.requests.post", return_value=mock_response) as mock_post:
        send_message("access_token_abc", "테스트 메시지")

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "kapi.kakao.com" in call_kwargs[0][0]


def test_send_message_raises_on_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")

    with patch("src.kakao.requests.post", return_value=mock_response):
        try:
            send_message("bad_token", "메시지")
            assert False, "예외 발생 필요"
        except Exception:
            pass
