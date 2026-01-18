"""Coin-related API endpoints"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..database import delete_coin, get_all_coins, get_coin_by_cert, save_coin
from ..models import CoinListResponse, DeleteResponse, ScrapeRequest, ScrapeResponse
from ..scraper import fetch_pcgs_cert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["coins"])


@router.get("/coins", response_model=CoinListResponse)
async def list_coins() -> CoinListResponse:
    """Get all coins list"""
    coins = get_all_coins()
    return CoinListResponse(coins=coins, total=len(coins))


@router.get("/coins/{cert_number}")
async def get_coin(cert_number: str) -> dict:
    """Get single coin details by certificate number"""
    coin = get_coin_by_cert(cert_number)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_coin(
    request: ScrapeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ScrapeResponse:
    """Scrape and save coin data by certificate number"""
    cert_number = request.cert_number.strip()
    if not cert_number:
        raise HTTPException(status_code=400, detail="Certificate number cannot be empty")

    try:
        coin_data = fetch_pcgs_cert(cert_number)
        save_coin(coin_data)
        return ScrapeResponse(success=True, data=coin_data)
    except Exception as e:
        logger.error("Scrape failed for %s: %s", cert_number, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/coins/{cert_number}", response_model=DeleteResponse)
async def remove_coin(cert_number: str) -> DeleteResponse:
    """Delete coin data by certificate number"""
    if delete_coin(cert_number):
        return DeleteResponse(success=True, message="Deleted successfully")
    raise HTTPException(status_code=404, detail="Coin not found")
