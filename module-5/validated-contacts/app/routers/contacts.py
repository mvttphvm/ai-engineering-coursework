from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactCategory,
)
from typing import Optional
from datetime import datetime

router = APIRouter()

# In-memory storage
contacts: list[dict] = []
_next_id = 1


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate):
    global _next_id

    new_contact = contact.model_dump()
    new_contact["id"] = _next_id
    new_contact["created_at"] = datetime.now().isoformat()

    contacts.append(new_contact)
    _next_id += 1

    return new_contact


@router.get("/", response_model=list[ContactResponse])
def list_contacts(category: Optional[ContactCategory] = Query(None)):
    if category is not None:
        return [contact for contact in contacts if contact["category"] == category]

    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int):
    for contact in contacts:
        if contact["id"] == contact_id:
            return contact

    raise HTTPException(status_code=404, detail="Contact not found")


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, contact_data: ContactUpdate):
    for contact in contacts:
        if contact["id"] == contact_id:
            update_data = contact_data.model_dump(exclude_unset=True)

            # Validate the complete contact after applying changes
            updated_contact = {**contact, **update_data}
            validated_contact = ContactResponse.model_validate(updated_contact)

            contact.update(validated_contact.model_dump())
            return contact

    raise HTTPException(status_code=404, detail="Contact not found")
