"""카카오 초기 토큰 발급 스크립트 — 최초 1회만 실행."""
import requests
import webbrowser

REST_API_KEY = input("REST API 키를 입력하세요: ").strip()
REDIRECT_URI = "http://localhost"

# 1. 인증 URL 열기
auth_url = (
    f"https://kauth.kakao.com/oauth/authorize"
    f"?response_type=code"
    f"&client_id={REST_API_KEY}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=talk_message"
)
print(f"\n브라우저가 열립니다. 카카오 로그인 후 리다이렉트된 URL을 복사하세요.")
webbrowser.open(auth_url)

# 2. 리다이렉트 URL에서 code 추출
redirect_url = input("\n리다이렉트된 전체 URL을 붙여넣기하세요: ").strip()
# URL 예: http://localhost/?code=ABCDEF123456
code = redirect_url.split("code=")[1].split("&")[0]
print(f"인증 코드: {code}")

# 3. 토큰 발급
response = requests.post(
    "https://kauth.kakao.com/oauth/token",
    data={
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    },
)
response.raise_for_status()
tokens = response.json()

print("\n=== GitHub Secrets에 저장할 값 ===")
print(f"KAKAO_REST_API_KEY   = {REST_API_KEY}")
print(f"KAKAO_REFRESH_TOKEN  = {tokens['refresh_token']}")
print("\n※ access_token은 GitHub Secrets에 저장하지 않아도 됩니다.")
print("※ 위 두 값을 GitHub 저장소 Settings → Secrets and variables → Actions에 추가하세요.")
