"""
IMPORTANT: JSONPlaceholder is a sandbox API. POST/PATCH/DELETE return realistic
responses but don't actually save data. This is normal and expected — it lets
you practice the full lifecycle without needing a real backend.
"""

import requests

BASE_URL = "https://jsonplaceholder.typicode.com/todos"


# Helper to print each step clearly
def log_step(step, method, path, status, note=""):
    print(f"  Step {step}: [{method}] {path}")
    print(f"           Status: {status}  {note}")


print("Full CRUD Lifecycle on /todos\n")
print("Step 1: CREATE")
new_post = {"title": "Complete Module 4", "completed": False, "userId": 1}

response = requests.post("https://jsonplaceholder.typicode.com/todos", json=new_post)

print(f"POST /todos")
print(f"Status: {response.status_code}")  # 201 = Created
created = response.json()
print(f"Created todo with ID: {created['id']}")
print(f"Title: {created['title']}")
print()


print("\nStep 2: READ")
id = created["id"]
response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{id}")
print(f"GET /todos/{id}")
print(f"Status: {response.status_code}")
post = response.json()
print(f"Title: {post['title'][:50]}")
print()


print("\nStep 3: UPDATE (PATCH)")
partial_update = {"completed": True}

response = requests.patch(
    f"https://jsonplaceholder.typicode.com/todos/{id}", json=partial_update
)

print(f"PATCH /todos/{id}")
print(f"Status: {response.status_code}")
result = response.json()
print(f"Updated completed: {result['completed']}")
print(f"Title unchanged: {result['title'][:40]}")
print(f"ID unchanged: {result['id']}")
print()


print("\nStep 4: READ AGAIN (verify)")
response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{id}")
print(f"GET /todos/{id}")
print(f"Status: {response.status_code}")
post = response.json()
print(f"Title: {post['title'][:50]}")
print()


print("\nStep 5: DELETE")
response = requests.delete(f"https://jsonplaceholder.typicode.com/todos/{id}")

print(f"DELETE /todos/{id}")
print(f"Status: {response.status_code}")
print()


print("\nStep 6: VERIFY DELETION")
response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{id}")
print(f"GET /todos/{id}")
if response.status_code == 404:
    print("Todo not found (deleted).")
elif response.status_code == 200:
    print("Todo still exists (sandbox behavior).")
else:
    print(f"Status code: {response.status_code}")
    post = response.json()
    print(f"Title: {post['title'][:50]}")
    print()
