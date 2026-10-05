"""
PART 1
Using the GitHub REST API documentation (https://docs.github.com/en/rest), find the answers to these questions:

What endpoint do you use to search repositories? GET /search/repositories
What query parameters can you use to sort the results by stars? sort=stars&order=desc
What is the rate limit for unauthenticated search requests? 10 requests per minute
What Accept header does GitHub recommend? application/vnd.github.v3+json
"""

import requests

url = "https://api.github.com/search/repositories"

params = {"q": "org:google", "sort": "stars", "order": "desc", "per_page": 3}

headers = {"Accept": "application/vnd.github+json"}

response = requests.get(url, params=params, headers=headers)

if response.status_code == 200:
    data = response.json()

    for repo in data["items"]:
        print(f"Name: {repo['name']}")
        print(f"Description: {repo['description']}")
        print(f"Stars: {repo['stargazers_count']}")
        print(f"Language: {repo['language']}")
        print()

    print("Rate limit remaining:", response.headers.get("X-RateLimit-Remaining"))

else:
    print("Request failed:", response.status_code)
