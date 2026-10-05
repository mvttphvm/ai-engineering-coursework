import requests


# EXPERIMENT 1: Unauthenticated request to a PROTECTED endpoint
print("1. GET /user (protected — requires auth)")

response = requests.get("https://api.github.com/user")

print("Status code:", response.status_code)
print("Error message:", response.json()["message"])


# EXPERIMENT 2: Unauthenticated request to a PUBLIC endpoint
print("\n2. GET /users/octocat (public — no auth needed)")

response = requests.get("https://api.github.com/users/octocat")
data = response.json()

print("Status code:", response.status_code)
print("Login:", data["login"])
print("Name:", data["name"])
print("Public repos:", data["public_repos"])

print("Rate limit:", response.headers.get("X-RateLimit-Limit"))
print("Rate remaining:", response.headers.get("X-RateLimit-Remaining"))


# AUTH HEADER FACTORY
def create_auth_headers(api_key: str, auth_type: str) -> dict:
    if auth_type == "bearer":
        return {"Authorization": f"Bearer {api_key}"}

    elif auth_type == "api-key":
        return {"X-API-Key": api_key}

    else:
        raise ValueError("Unknown auth type")


# TEST AUTH HEADER FACTORY
print("\n3. Auth header factory demo")

print(create_auth_headers("abc123", "bearer"))
print(create_auth_headers("abc123", "api-key"))

try:
    print(create_auth_headers("abc123", "invalid"))
except ValueError as error:
    print("Error:", error)
