import requests

BASE_URL = "https://jsonplaceholder.typicode.com"


def report(method, url, **kwargs):
    """Make a request and return a formatted report."""

    response = requests.request(method, url, **kwargs)

    status = response.status_code

    if 200 <= status < 300:
        category = "2xx — Success"
    elif 400 <= status < 500:
        category = "4xx — Client Error"
    elif 500 <= status < 600:
        category = "5xx — Server Error"
    else:
        category = "Other"

    descriptions = {
        200: "OK — request succeeded, resource returned",
        201: "Created — resource successfully created",
        204: "No Content — request succeeded with no response body",
        400: "Bad Request — server could not understand the request",
        401: "Unauthorized — authentication is required",
        404: "Not Found — resource could not be found",
        500: "Internal Server Error — server encountered an error",
    }

    description = descriptions.get(
        status, "Request completed with an unexpected status code"
    )

    return {
        "method": method.upper(),
        "url": url,
        "status": status,
        "category": category,
        "description": description,
    }


def print_report(r):
    """Print a formatted report dict."""

    print(f"{r['method']} {r['url']}")
    print(f"Status: {r['status']} ({r['category']})")
    print(f"Description: {r['description']}")


print("Status Code Detective\n")


# 1. Successful GET (200)
print("1. Successful GET /posts/1")

r = report("GET", f"{BASE_URL}/posts/1")
print_report(r)


# 2. Nonexistent resource (404)
print("\n2. GET /posts/99999 (nonexistent)")

r = report("GET", f"{BASE_URL}/posts/99999")
print_report(r)


# 3. POST with valid data (201)
print("\n3. POST /posts with valid data")

r = report(
    "POST",
    f"{BASE_URL}/posts",
    json={"title": "New Post", "body": "This is a new post.", "userId": 1},
)
print_report(r)


# 4. DELETE
print("\n4. DELETE /posts/1")

r = report("DELETE", f"{BASE_URL}/posts/1")
print_report(r)


# 5. Invalid endpoint (404)
print("\n5. GET /invalidendpoint")

r = report("GET", f"{BASE_URL}/invalidendpoint")
print_report(r)


# 6. Nested resource (200)
print("\n6. GET /users/1/todos")

r = report("GET", f"{BASE_URL}/users/1/todos")
print_report(r)
