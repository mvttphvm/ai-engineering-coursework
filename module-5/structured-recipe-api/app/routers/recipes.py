from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# Defines the information required to create a recipe
class RecipeCreate(BaseModel):
    title: str
    cuisine: str
    servings: int
    ingredients: list[str]


# In-memory storage
recipes: list[dict] = [
    {
        "id": 1,
        "title": "Pasta Carbonara",
        "cuisine": "Italian",
        "servings": 2,
        "ingredients": ["pasta", "eggs", "cheese"],
    },
    {
        "id": 2,
        "title": "Tacos al Pastor",
        "cuisine": "Mexican",
        "servings": 4,
        "ingredients": ["pork", "tortillas", "pineapple"],
    },
]

# Counter for new recipe IDs
_next_id = 3


# GET /recipes — List all recipes
@router.get("")
def list_recipes():
    return recipes


# GET /recipes/{recipe_id} — Get one recipe
@router.get("/{recipe_id}")
def get_recipe(recipe_id: int):
    for recipe in recipes:
        if recipe["id"] == recipe_id:
            return recipe

    raise HTTPException(status_code=404, detail="Recipe not found")


# POST /recipes — Create a new recipe
@router.post("", status_code=201)
def create_recipe(recipe: RecipeCreate):
    global _next_id

    new_recipe = {"id": _next_id, **recipe.model_dump()}

    recipes.append(new_recipe)
    _next_id += 1

    return new_recipe
