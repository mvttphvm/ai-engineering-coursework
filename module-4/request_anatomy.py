import requests
import json

BASE_URL = "https://jsonplaceholder.typicode.com"


def print_separator(title):
    """Print a section separator."""
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print('=' * 55)


def display_anatomy(response, label):
    """Display the full anatomy of a request/response pair."""
    req = response.request

    print(f"\n=== REQUEST for {label} ===")
    print(f"Method: {req.method}")
    print(f"URL: {req.url}")
    print(f"Headers: {dict(req.headers)}")

    if req.body:
        print(f"Body: {json.dumps(json.loads(req.body), indent=2)}")
    else:
        print("Body: None")

    print(f"\n=== RESPONSE for {label} ===")
    print(f"Status: {response.status_code} ({response.reason})")
    print(f"Elapsed Time: {response.elapsed.total_seconds() * 1000:.2f} ms")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {response.headers.get('Content-Length')}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")


print_separator("REQUEST 1: GET /users/1")
response = requests.get(f"{BASE_URL}/users/1")
display_anatomy(response, "GET /users/1")


print_separator("REQUEST 2: POST /posts")
response = requests.post(
    f"{BASE_URL}/posts",
    json={"title": "Jump Jump", "body": "It's time to JUMP!", "userId": 1},
)
display_anatomy(response, "POST /posts")


print_separator("REQUEST 3: PATCH /posts/1")
response = requests.patch(
    f"{BASE_URL}/posts/1",
    json={"title": "Updated Title"}
)
display_anatomy(response, "PATCH /posts/1")