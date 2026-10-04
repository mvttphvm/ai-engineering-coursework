import requests

# ============================================================
# PART 1: Inspect headers from 3 endpoints
# ============================================================

endpoints = [
    ("https://jsonplaceholder.typicode.com/posts/1", "JSONPlaceholder /posts/1"),
    ("https://jsonplaceholder.typicode.com/users/1", "JSONPlaceholder /users/1"),
    ("https://httpbin.org/get", "httpbin /get"),
]

print("PART 1: Response header inspection\n")

for url, label in endpoints:
    print(f"Endpoint: {label}")

    response = requests.get(url, timeout=10)

    print(f"Status: {response.status_code}")
    print(f"Total response headers: {len(response.headers)}")

    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
    print(f"Content-Length: {response.headers.get('Content-Length', 'Not specified')}")

    # Check for caching headers
    caching_headers = ["Cache-Control", "ETag", "Last-Modified"]
    found_cache_headers = []

    for header in caching_headers:
        if header in response.headers:
            found_cache_headers.append(
                f"{header}: {response.headers[header]}"
            )

    if found_cache_headers:
        print("Caching headers present:")
        for header in found_cache_headers:
            print(f"  {header}")
    else:
        print("Caching headers: None")

    # Check for rate-limiting headers
    rate_limit_headers = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining"
    ]

    found_rate_headers = []

    for header in rate_limit_headers:
        if header in response.headers:
            found_rate_headers.append(
                f"{header}: {response.headers[header]}"
            )

    if found_rate_headers:
        print("Rate-limiting headers:")
        for header in found_rate_headers:
            print(f"  {header}")
    else:
        print("Rate-limiting headers: None")

    print()


# ============================================================
# PART 2: POST to httpbin.org with a custom header
# ============================================================

print("\nPART 2: POST to httpbin.org with custom header\n")

data = {
    "message": "Hello!",
    "exercise": "Header Inspector"
}

custom_headers = {
    "X-Student-Name": "Matt"
}

response = requests.post(
    "https://httpbin.org/post",
    json=data,
    headers=custom_headers,
    timeout=10
)

print(f"Status: {response.status_code}")

result = response.json()

print("\nJSON body received by httpbin:")
print(result["json"])

print("\nCustom header received by httpbin:")
print(f"X-Student-Name: {result['headers']['X-Student-Name']}")

print("\nFull response:")
print(result)