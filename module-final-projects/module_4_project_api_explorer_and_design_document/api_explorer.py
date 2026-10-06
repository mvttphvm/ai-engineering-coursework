import requests


def make_request(method, url, params=None, data=None):
    try:
        response = requests.request(method, url, params=params, json=data, timeout=10)

        print("\nMethod:", method)
        print("URI:", response.url)
        print("Status:", response.status_code, response.reason)
        print("Content-Type:", response.headers.get("Content-Type"))

        response.raise_for_status()

        return response

    except requests.exceptions.Timeout:
        print("\nRequest timed out:", url)
        return None

    except requests.exceptions.RequestException as error:
        print("Request failed:", error)
        return None


# ---------------- PokeAPI ----------------

# 1. A collection endpoint returns multiple resources
pokemon = make_request("GET", "https://pokeapi.co/api/v2/pokemon")

if pokemon:
    data = pokemon.json()
    print("Total Pokemon:", data["count"])
    print("First Pokemon:", data["results"][0]["name"])


# 2. A specific resource can be requested by its name
pikachu = make_request("GET", "https://pokeapi.co/api/v2/pokemon/pikachu")

if pikachu:
    data = pikachu.json()
    print("Name:", data["name"])
    print("Height:", data["height"])
    print("Weight:", data["weight"])


# 3. GET a collection of Pokemon types
types = make_request("GET", "https://pokeapi.co/api/v2/type")

if types:
    data = types.json()
    print("Number of types:", data["count"])
    print(f"First type: {data['results'][0]['name']}\n")


# ---------------- Open-Meteo ----------------

# 4. Query parameters specify the location and weather data
temperature = make_request(
    "GET",
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 33.7, "longitude": -117.9, "current": "temperature_2m"},
)

if temperature:
    data = temperature.json()
    print("Temperature:", data["current"]["temperature_2m"])


# 5. GET current wind speed for another location
wind = make_request(
    "GET",
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 34.05, "longitude": -118.24, "current": "wind_speed_10m"},
)

if wind:
    data = wind.json()
    print("Wind Speed:", data["current"]["wind_speed_10m"])


# 6. GET current humidity
humidity = make_request(
    "GET",
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 40.71, "longitude": -74.01, "current": "relative_humidity_2m"},
)

if humidity:
    data = humidity.json()
    print("Humidity:", data["current"]["relative_humidity_2m"])


# ---------------- JSONPlaceholder ----------------

# 7. This is a nested resource because the posts belong to user 1
posts = make_request("GET", "https://jsonplaceholder.typicode.com/users/1/posts")

if posts:
    data = posts.json()
    print("User 1 post count:", len(data))
    print("First post title:", data[0]["title"])


# 8. POST sends data to create a new resource
new_post = {"title": "My API Post", "body": "Learning REST APIs", "userId": 1}

post = make_request("POST", "https://jsonplaceholder.typicode.com/posts", data=new_post)

if post:
    data = post.json()

    # Status 201 means a resource was successfully created
    print("Created post ID:", data["id"])
    print("Created post title:", data["title"])


# 9. DELETE is used to remove a resource
deleted_post = make_request("DELETE", "https://jsonplaceholder.typicode.com/posts/1")

if deleted_post:
    print("Post 1 deleted successfully")


# ---------------- Error Handling Test ----------------

# 10. This Pokemon does not exist, so the API should return a 404
bad_request = make_request(
    "GET", "https://pokeapi.co/api/v2/pokemon/not-a-real-pokemon-123"
)

if bad_request is None:
    print("The error was handled and the program did not crash.")
