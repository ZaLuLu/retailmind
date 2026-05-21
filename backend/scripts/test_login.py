import requests

try:
    # 1. Login
    res = requests.post("http://localhost:8000/api/v1/auth/login", json={
        "email": "rahul@retailmind.com",
        "password": "password123"
    })
    data = res.json()
    token = data["access_token"]
    
    # 2. Get /users/me
    headers = {"Authorization": f"Bearer {token}"}
    res_me = requests.get("http://localhost:8000/api/v1/users/me", headers=headers)
    print("Users/me Status code:", res_me.status_code)
    print("Users/me Response:", res_me.text)
except Exception as e:
    print("Error:", e)
