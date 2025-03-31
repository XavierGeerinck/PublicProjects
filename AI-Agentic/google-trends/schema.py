from typing import List
from pydantic import BaseModel, Field
from enum import Enum


class TrendCategory(str, Enum):
    OTHER = "other"
    CARS_AND_VEHICLES = "cars and vehicles"
    BEAUTY_AND_MODE = "beauty and mode"
    ENTERTAINMENT = "entertainment"
    FOOD_AND_DRINK = "food and drink"
    HEALTH = "health"
    HOBBY = "hobby"
    PETS_AND_ANIMALS = "pets and animals"
    CLIMATE = "climate"
    POLITIC = "politic"
    TRAVEL_AND_TRANSPORTATION = "travel and transportation"
    SHOPPING = "shopping"
    GAMES = "games"
    SPORT = "sport"
    TECHNOLOGY = "technology"
    JOBS_AND_EDUCATION = "jobs and education"
    SCIENCE = "science"
    GOVERNMENT = "government"
    BUSINESS_AND_FINANCE = "business and finance"


class Trend(BaseModel):
    name: str = Field(description="The trend")
    name_similar: str = Field(description="The other trend information similar to this one, comma separated")
    time_start: str = Field(description="The start date of the trend in the format YYYY-MM-DD HH:mm")
    time_end: str = Field(description="The end date of the trend (if available, will appear as 11h ago)")
    is_active: bool = Field(description="If the trend is active or not, defined through Lasted x hours or Active")
    volume: str = Field(description="The search volume")
    categories: List[TrendCategory] = Field(description="The categories of the trend")
    created_at: str = Field(description="The date the trend was created")

class Trends(BaseModel):
    trends: List[Trend]
