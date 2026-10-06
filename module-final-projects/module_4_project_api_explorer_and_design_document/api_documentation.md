# API Documentation

## PokeAPI

Base URL: https://pokeapi.co/api/v2/

Authentication: None

### Endpoints Tested

1. GET /pokemon

Description: Gets a collection of Pokemon.

Example response shape:
count, next, previous, results

2. GET /pokemon/pikachu

Description: Gets information about Pikachu.

Example response shape:
id, name, height, weight, abilities, types

3. GET /type

Description: Gets a collection of Pokemon types.

Example response shape:
count, next, previous, results

Rate Limits:
I did not run into any rate limit errors while testing.

Something that surprised me:
The /pokemon endpoint gives the total number of Pokemon, but the results only contain part of the collection at a time.

## Open-Meteo

Base URL: https://api.open-meteo.com/v1/

Authentication: None

### Requests Tested

1. GET /forecast?latitude=33.7&longitude=-117.9&current=temperature_2m

Description: Gets the current temperature for the provided location.

Example response shape:
latitude, longitude, timezone, current

2. GET /forecast?latitude=34.05&longitude=-118.24&current=wind_speed_10m

Description: Gets the current wind speed for the provided location.

Example response shape:
latitude, longitude, timezone, current

3. GET /forecast?latitude=40.71&longitude=-74.01&current=relative_humidity_2m

Description: Gets the current relative humidity for the provided location.

Example response shape:
latitude, longitude, timezone, current

Rate Limits:
I did not run into any rate limit errors while testing.

Something that surprised me:
The same /forecast endpoint can return different weather information depending on the query parameters.

## JSONPlaceholder

Base URL: https://jsonplaceholder.typicode.com/

Authentication: None

### Endpoints Tested

1. GET /users/1/posts

Description: Gets the posts that belong to user 1. This is a nested resource.

Example response shape:
A list of posts containing userId, id, title, and body.

2. POST /posts

Description: Creates a new test post.

Example response shape:
userId, title, body, id

3. DELETE /posts/1

Description: Deletes post 1.

Example response shape:
An empty JSON object.

Rate Limits:
I did not run into any rate limit errors while testing.

Something that surprised me:
JSONPlaceholder responds like the POST and DELETE actually changed the data, but the changes are only simulated and are not permanently saved.
