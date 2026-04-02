import asyncio
import pandas as pd
import json
from analyzer import TechAnalyzer

async def main():
    df = pd.read_parquet("part-00000-66e0628d-2c7f-425a-8f5b-738bcd6bf198-c000.snappy.parquet")
    domains = df["root_domain"].unique().tolist()

    analyzer = TechAnalyzer(domains)

if __name__ == "__main__":
    asyncio.run(main())