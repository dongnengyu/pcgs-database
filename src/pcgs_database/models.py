"""Pydantic models for request/response validation"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Request model for scraping a coin by certificate number"""

    cert_number: str = Field(..., min_length=1, description="PCGS certificate number")


class ScrapeResponse(BaseModel):
    """Response model for scrape operation"""

    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class CoinBase(BaseModel):
    """Base coin model with common fields"""

    cert_number: str
    pcgs_number: Optional[str] = None
    grade: Optional[str] = None
    date_mintmark: Optional[str] = None
    denomination: Optional[str] = None
    price_guide_value: Optional[str] = None
    population: Optional[str] = None
    pop_higher: Optional[str] = None
    mintage: Optional[str] = None
    region: Optional[str] = None
    holder_type: Optional[str] = None
    security: Optional[str] = None


class CoinCreate(CoinBase):
    """Model for creating a new coin record"""

    image_url: Optional[str] = None
    local_image_path: Optional[str] = None
    raw_data: Optional[str] = None


class CoinResponse(CoinBase):
    """Response model for coin data"""

    id: int
    image_url: Optional[str] = None
    local_image_path: Optional[str] = None
    raw_data: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CoinListResponse(BaseModel):
    """Response model for coin list"""

    coins: list[dict]
    total: int


class DeleteResponse(BaseModel):
    """Response model for delete operation"""

    success: bool
    message: str
