"""PCGS certificate information scraper using Playwright Async API"""

import logging
import os
import re
from typing import Optional

import httpx
from playwright.async_api import async_playwright

from .config import get_settings

logger = logging.getLogger(__name__)


async def download_image(url: str, save_path: str) -> bool:
    """
    Download image to local path.

    Args:
        url: Image URL
        save_path: Local path to save the image

    Returns:
        True if download was successful, False otherwise
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.pcgs.com/",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(response.content)
        return True
    except Exception as e:
        logger.error("Failed to download image %s: %s", url, e)
        return False


async def fetch_pcgs_cert(cert_number: str, download_images: bool = True) -> dict:
    """
    Fetch PCGS certificate information using Playwright Async API.

    Args:
        cert_number: PCGS certificate number
        download_images: Whether to download coin images

    Returns:
        Dictionary containing coin information
    """
    settings = get_settings()
    url = f"https://www.pcgs.com/cert/{cert_number}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # Navigate to page
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait for page to load
        await page.wait_for_timeout(3000)

        coin_data: dict = {
            "cert_number": cert_number,
            "url": url,
        }

        # Get page HTML
        html = await page.content()

        # Extract title
        title_elem = await page.query_selector("h1")
        if title_elem:
            coin_data["title"] = (await title_elem.inner_text()).strip()

        # Try to get grade information
        grade_selectors = [
            ".grade",
            ".coin-grade",
            "[class*='grade']",
            ".pcgs-grade",
            ".certification-grade",
        ]
        for selector in grade_selectors:
            elem = await page.query_selector(selector)
            if elem:
                text = (await elem.inner_text()).strip()
                if text and re.search(r"MS|PR|AU|XF|VF|EF|F|VG|G|AG|\d+", text):
                    coin_data["grade"] = text
                    break

        # Find specification areas
        spec_selectors = [
            ".coin-details",
            ".cert-details",
            ".specifications",
            ".coin-info",
            "[class*='detail']",
            "[class*='spec']",
        ]
        for selector in spec_selectors:
            elems = await page.query_selector_all(selector)
            for elem in elems:
                text = (await elem.inner_text()).strip()
                if text:
                    coin_data.setdefault("details", []).append(text)

        # Find table data
        rows = await page.query_selector_all("tr")
        for row in rows:
            cells = await row.query_selector_all("td, th")
            if len(cells) >= 2:
                key = (
                    (await cells[0].inner_text())
                    .strip()
                    .lower()
                    .replace(" ", "_")
                    .replace(":", "")
                )
                value = (await cells[1].inner_text()).strip()
                if key and value and len(key) < 50:
                    coin_data[key] = value

        # Find definition lists
        dts = await page.query_selector_all("dt")
        dds = await page.query_selector_all("dd")
        for dt, dd in zip(dts, dds):
            key = (
                (await dt.inner_text()).strip().lower().replace(" ", "_").replace(":", "")
            )
            value = (await dd.inner_text()).strip()
            if key and value:
                coin_data[key] = value

        # Find images - PCGS uses cloudfront.net for coin images
        images: list[str] = []

        # Method 1: Find img tags with cloudfront URLs
        img_elems = await page.query_selector_all("img")
        for img in img_elems:
            src = await img.get_attribute("src") or ""
            if src and "cloudfront.net/cert/" in src:
                # Prefer large images over small/thumbnail
                if "/small/" in src:
                    src = src.replace("/small/", "/large/")
                images.append(src)

        # Method 2: Search HTML for cloudfront URLs (backup)
        if not images:
            import re
            cloudfront_pattern = r'https://d1htnxwo4o0jhw\.cloudfront\.net/cert/\d+/large/[^\s"\']+'
            html_images = re.findall(cloudfront_pattern, html)
            images.extend(html_images)

        # Fallback: original method for older pages
        if not images:
            for img in img_elems:
                src = await img.get_attribute("src") or ""
                alt = await img.get_attribute("alt") or ""
                if src and (
                    "coin" in src.lower()
                    or "coin" in alt.lower()
                    or cert_number in src
                ):
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        src = "https://www.pcgs.com" + src
                    images.append(src)

        if images:
            coin_data["image_urls"] = list(set(images))  # Deduplicate

            # Download images
            if download_images:
                img_dir = str(settings.IMAGES_DIR)
                os.makedirs(img_dir, exist_ok=True)
                saved_images: list[str] = []
                for i, img_url in enumerate(coin_data["image_urls"]):
                    ext = os.path.splitext(img_url.split("?")[0])[-1] or ".jpg"
                    filename = f"{cert_number}_{i + 1}{ext}"
                    save_path = os.path.join(img_dir, filename)
                    if await download_image(img_url, save_path):
                        # Store relative path for serving
                        relative_path = f"data/images/{filename}"
                        saved_images.append(relative_path)
                        logger.info("Image saved: %s", save_path)
                coin_data["saved_images"] = saved_images

        # Save debug info
        coin_data["_html_length"] = len(html)

        await browser.close()

    return coin_data


async def main() -> None:
    """Main function for testing the scraper"""
    import json
    import asyncio

    logging.basicConfig(level=logging.INFO)

    cert_number = "40483953"

    logger.info("Fetching PCGS certificate: %s", cert_number)
    logger.info("-" * 50)

    try:
        data = await fetch_pcgs_cert(cert_number)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error("Fetch failed: %s", e)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
