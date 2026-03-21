#!/usr/bin/env python3
"""Seed the database with sample data."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.db import init_db_sync
from src.services.data_importer import seed_sample_data


async def main():
    print("Initializing database...")
    init_db_sync()
    print("Seeding sample data...")
    count = await seed_sample_data()
    print(f"Done! Seeded {count} words.")


if __name__ == "__main__":
    asyncio.run(main())
