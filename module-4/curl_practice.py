# Part 2 - Python API Client

import requests
import json


class APIClient:
    """A simple API client — similar to how you'd organize a Postman collection."""

    def __init__(self, base_url, headers=None):
        self.base_url = base_url.rstrip("/")
        self.default_headers = headers or {}

    def _request(self, method, path, **kwargs):
        """Make a request and return a formatted result."""
        url = f"{self.base_url}{path}"

        # Merge default headers with any request-specific headers
        headers = {**self.default_headers, **kwargs.pop("headers", {})}

        response = requests.request(method, url, headers=headers, **kwargs)

        return {
            "status": response.status_code,
            "reason": response.reason,
            "time_ms": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.text else None,
            "headers": dict(response.headers),
        }

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self._request("PUT", path, **kwargs)

    def patch(self, path, **kwargs):
        return self._request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)


class JSONPlaceholderClient(APIClient):
    def __init__(self):
        super().__init__("https://jsonplaceholder.typicode.com")

    def get_user(self, user_id):
        """Get a specific user's profile."""
        return self.get(f"/users/{user_id}")["data"]

    def get_user_posts(self, user_id):
        """Get all posts by a specific user."""
        return self.get("/posts", params={"userId": user_id})["data"]

    def create_post(self, user_id, title, body):
        """Create a new post for a user."""
        data = {"userId": user_id, "title": title, "body": body}

        return self.post("/posts", json=data)["data"]

    def search_posts(self, query):
        """Search posts by title (client-side filtering)."""
        posts = self.get("/posts")["data"]

        return [post for post in posts if query.lower() in post["title"].lower()]


# Test Script

client = JSONPlaceholderClient()

# 1. Get user 5's profile and print their name and city
user = client.get_user(5)
print("Name:", user["name"])
print("City:", user["address"]["city"])

# 2. Get user 5's posts and print the count
posts = client.get_user_posts(5)
print("User 5 post count:", len(posts))

# 3. Create a new post and print the returned ID
new_post = client.create_post(5, "My New Post", "This is my API testing assignment.")
print("New post ID:", new_post["id"])

# 4. Search for posts with "qui" in the title and print how many match
matches = client.search_posts("qui")
print("Posts with 'qui' in title:", len(matches))
