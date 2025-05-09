from dataclasses import dataclass
from typing import List, Dict, Optional
import re

def sanitize_input(v: str) -> str:
    # Remove any potentially dangerous characters
    # Only allow letters, numbers, spaces, and basic punctuation
    v = re.sub(r'[^a-zA-Z0-9\s\-_.,]', '', v)
    # Remove extra whitespace
    v = ' '.join(v.split())
    if not v:
        raise ValueError("Input cannot be empty after sanitization")
    if len(v) > 50:
        raise ValueError("Input must be 50 characters or less")
    return v

@dataclass
class Item:
    name: str
    is_divisible: bool = False

    def __post_init__(self):
        self.name = sanitize_input(self.name)

@dataclass
class Person:
    name: str

    def __post_init__(self):
        self.name = sanitize_input(self.name)

@dataclass
class Valuation:
    person: str
    item: str
    value: float

    def __post_init__(self):
        self.person = sanitize_input(self.person)
        self.item = sanitize_input(self.item)
        if not 0 <= self.value <= 100:
            raise ValueError("Value must be between 0 and 100")

@dataclass
class FairDivisionRequest:
    items: List[Item]
    people: List[Person]
    valuations: List[Valuation]

    def __post_init__(self):
        if not 1 <= len(self.items) <= 50:
            raise ValueError("Must have between 1 and 50 items")
        if not 1 <= len(self.people) <= 50:
            raise ValueError("Must have between 1 and 50 people")
        if not self.valuations:
            raise ValueError("Must have at least one valuation")

        # Create sets of valid item and person names
        valid_items = {item.name for item in self.items}
        valid_people = {person.name for person in self.people}

        # Check that all valuations reference valid items and people
        for valuation in self.valuations:
            if valuation.item not in valid_items:
                raise ValueError(f"Invalid item name: {valuation.item}")
            if valuation.person not in valid_people:
                raise ValueError(f"Invalid person name: {valuation.person}")

        # Check that each person has a valuation for each item
        for person in valid_people:
            for item in valid_items:
                if not any(v.person == person and v.item == item for v in self.valuations):
                    raise ValueError(f"Missing valuation for {person} and {item}")

@dataclass
class FairDivisionResponse:
    success: bool
    message: str
    result: Optional[Dict] = None
    error: Optional[str] = None 