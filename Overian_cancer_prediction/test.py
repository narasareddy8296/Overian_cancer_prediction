import requests

API_URL = "https://api.together.xyz/v1/chat/completions"
headers = {
    "Authorization": "Bearer tgp_v1_oq7VQfTL92PXJoxRvWILTSyH9AfyNMIq2VPq0HoUkgA",
    "Content-Type": "application/json"
}

data = {
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful medical assistant specializing in cancer awareness and prevention."
        },
        {
            "role": "user",
            "content": """
A 62-year-old postmenopausal woman has the following tumor markers:
- CA125: 312.7 U/mL
- HE4: 135.6 pmol/L
- CA19-9: 65.3 U/mL
- AFP: 202.1 ng/mL

She has a first-degree relative with ovarian cancer and is a smoker.

Explain her ovarian cancer risk level, likely causes, and provide personalized recommendations on lifestyle, diet, and medical follow-up.
"""
        }
    ],
    "temperature": 0.7,
    "max_tokens": 1024
}

response = requests.post(API_URL, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print(result["choices"][0]["message"]["content"])
else:
    print(f"❌ Error {response.status_code}:\n{response.text}")
