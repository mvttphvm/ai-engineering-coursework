
# Design Critic: Evaluate API URIs — Your Response

**Exercise:** Design Critic
**Module:** 4 — REST API Fundamentals
**Lesson:** 2
**Estimated time:** 25 minutes

## Objective

Evaluate 8 URIs against REST conventions, then design your own API for a recipe manager.

## REST URI Rules (from the lesson)

1. Use nouns, not verbs — HTTP methods express the action
2. Use plural nouns for collections: `/users`, not `/user`
3. Resource IDs go in the path: `/users/5`, not `?id=5`
4. Query params are for filtering: `/products?category=electronics`
5. Nest at most 2-3 levels: `/users/5/orders` ✓, `/a/b/c/d/e/f` ✗

---

## Part 1 — Evaluate These URIs

For each URI: say Good or Bad, explain what's wrong (if bad), and write the corrected version.

| URI                                              | Method | Good or Bad? | Issue (if bad)                                                        | Corrected Version  |
| ------------------------------------------------ | ------ | ------------ | --------------------------------------------------------------------- | ------------------ |
| `/getAllUsers`                                 | GET    | Bad          | verb not noun,<br />doesn't need All,<br />Users supposed to be users | /users             |
| `/users`                                       | POST   | Good         | n/a                                                                   | n/a                |
| `/user/5`                                      | GET    | BAD          | user supposed to be plural                                            | /users/5           |
| `/removeProduct?id=12`                         | DELETE | BAD          | no verbs, lowercase & plural needed, /12 is cleaner                  | /product/12        |
| `/products?category=electronics&sort=price`    | GET    | Good         | n/a                                                                   | n/a                |
| `/updateUser/5`                                | PUT    | Bad          | no verb, needs plural and lowercase                                   | /users/5           |
| `/users/5/orders`                              | GET    | Good         | n/a                                                                   | n/a                |
| `/users/5/orders/10/items/3/reviews/1/replies` | GET    | Bad          | too much nesting                                                      | /reviews/1/replies |

---

## Part 2 — Design a Recipe Manager API

Design a REST API for a recipe manager app. Include resources for at least: recipes, ingredients, categories.

**Endpoints table (minimum 8 endpoints):**

| Method | URI                                        | Description                                            |
| ------ | ------------------------------------------ | ------------------------------------------------------ |
| GET    | /categories/1                              | gets a category of food                                |
| POST   | /recipes                                   | adds a new recipe                                      |
| PUT    | /recipes/17                                | updates the recipe                                     |
| DELETE | /recipes/5/ingredients/6                   | removes ingredient 6                                   |
| GET    | /recipes?toppings=chocolate&group=desserts | finds recipes with chocolate toppings and are desserts |
| GET    | /ingredients?sugarFree=true                | gets ingredients that are sugarFree                    |
| PATCH  | /categories/5                              | changes catgeory 5                                     |
| DELETE | /categories/5/recipe?group=pastas          | deletes pasta recipes                                  |

**Design notes:** _(Explain any interesting decisions — why you nested some resources, how you handle filtering, etc.)_

> I used nested resources when one resource belongs to another, such as /recipes/5/ingredients/6, because the ingredient is being accessed within a specific recipe. I used query parameters for filtering, such as ?toppings=chocolate&group=desserts and ?sugarFree=true, because they narrow down a collection without changing the main resource path. I used specific IDs like /recipes/17 and /categories/5 when working with one specific resource.
