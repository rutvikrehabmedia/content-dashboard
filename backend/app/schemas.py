from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

class ScrapedContentModel(MongoBaseModel):
    url: HttpUrl
    original_url: Optional[HttpUrl]
    process_id: str
    timestamp: datetime
    content: Optional[str]
    meta_data: Dict = Field(default_factory=dict)
    scraped_data: Dict = Field(default_factory=dict)

class SearchLogModel(MongoBaseModel):
    query: str
    urls: List[str] = Field(default_factory=list)
    whitelist: List[str] = Field(default_factory=list)
    blacklist: List[str] = Field(default_factory=list)
    scraped_data: Dict = Field(default_factory=dict)
    process_id: str
    timestamp: datetime

class WhitelistModel(MongoBaseModel):
    url: HttpUrl
    added_at: datetime

class BlacklistModel(MongoBaseModel):
    url: HttpUrl
    added_at: datetime 