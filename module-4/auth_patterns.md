# Auth Pattern Recognition

**Part 1 - Documentation Reading (no code)**

Visit the documentation pages for two real APIs and answer these questions for each:

* **OpenAI API** : [https://platform.openai.com/docs/api-reference/authentication](https://platform.openai.com/docs/api-reference/authentication)
* **GitHub REST API** : [https://docs.github.com/en/rest/authentication](https://docs.github.com/en/rest/authentication)

OpenAI API

1. What authentication method does it use? API key using Bearer authentication.
2. Where does the credential go (header, query parameter, or something else)? HTTP header.
3. What header name does it use? Example: Authorization: Bearer YOUR_API_KEY
4. What happens if you make a request without authentication? The request fails with an authentication error, 401 unauthorized usually.

GitHub REST API

1. What authentication method does it use? A personal access token, GitHub App token, or OAuth token.
2. Where does the credential go (header, query parameter, or something else)? HTTP header.
3. What header name does it use? Example: Authoerization: Bearer YOUR_TOKEN
4. What happens if you make a request without authentication? Some public endpoint will work, but with lower rate limits and no access to private/protected resources. Endpoints that require authentication return an authentication error.

**Part 2 - Code Implementation**

Create a script (`<span>auth_patterns.py</span>`) that demonstrates:

1. Making an *unauthenticated* request to [`<span>https://api.github.com/user</span>`](https://api.github.com/user) and printing the status code (you should get 401)
2. Making an *unauthenticated* request to [`<span>https://api.github.com/users/octocat</span>`](https://api.github.com/users/octocat) and printing the status code (this public endpoint should return 200)
3. A function called `<span>create_auth_headers()</span>` that takes an API key and an auth type ("bearer" or "api-key") and returns the correct headers dictionary

---

## GitHub REST API

|  |  |  |  |
| - | - | - | - |
