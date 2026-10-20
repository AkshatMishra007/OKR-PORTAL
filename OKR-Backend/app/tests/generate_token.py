from app.core.security import create_access_token

token = create_access_token({"sub": "USER_UUID_HERE", "email": "test@test.com"})

print(token)
