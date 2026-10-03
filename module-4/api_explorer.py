"""
Before you start:
    Make sure your virtual environment is active:
        source .venv/bin/activate   # Mac/Linux
        .venv\\Scripts\\activate     # Windows
    And requests is installed:
        pip install -r requirements.txt
"""

import requests
# Make sure you've activated your virtual environment and installed requirements.txt

BASE_URL = "https://jsonplaceholder.typicode.com"

# ============================================================
# TASK 1: GET all users
# ============================================================
print("TASK 1: All Users")
print("-" * 40)

response = requests.get(BASE_URL + "/users")

print("Status Code:", response.status_code)
users = response.json()
print("Total Users:", len(users))

for user in users:
    print(user["name"], "-", user["email"])


# ============================================================
# TASK 2: GET posts by user #3
# ============================================================

print("\nTASK 2: Posts by User #3")
print("-" * 40)

response = requests.get(BASE_URL + "/posts", params={"userId": 3})

posts = response.json()

print("Status Code:", response.status_code)
print("Posts found:", len(posts))

for post in posts[:3]:
    print(post["title"])


# ============================================================
# TASK 3: GET comments on post #1
# ============================================================

print("\nTASK 3: Comments on Post #1")
print("-" * 40)

response = requests.get(BASE_URL + "/posts/1/comments")

comments = response.json()

print("Status Code:", response.status_code)
print("Comments found:", len(comments))

for comment in comments[:2]:
    print(comment["email"], "-", comment["body"][:60])


# ============================================================
# TASK 4: POST a new post
# ============================================================

print("\nTASK 4: Create a New Post (POST)")
print("-" * 40)

new_post = {
    "title": "My First API Post",
    "body": "This post was created using a POST request.",
    "userId": 1,
}

response = requests.post(BASE_URL + "/posts", json=new_post)

created_post = response.json()

print("Status Code:", response.status_code)
print("Created ID:", created_post["id"])
print("Title:", created_post["title"])
