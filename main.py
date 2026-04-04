import asyncio
import pandas as pd
from playwright.async_api import async_playwright, Playwright
import json
from analyzer import TechAnalyzer

async def main():
    df = pd.read_parquet("part-00000-66e0628d-2c7f-425a-8f5b-738bcd6bf198-c000.snappy.parquet")
    domains = df["root_domain"].unique().tolist()
    analyzer = TechAnalyzer(domains)
    async with async_playwright() as p:
        await analyzer.start_browser(p)
        semaphore = asyncio.Semaphore(5)
        await asyncio.gather(*(analyzer.run_page(semaphore, domains[i], i + 1) for i in range(len(domains))))
        await analyzer.close_browser()

if __name__ == "__main__":
    asyncio.run(main())