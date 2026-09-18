"""
GrowthPilot AI — Seed Script
Usage: python -m scripts.seed
       OR: make seed (from backend/ directory)
"""
import asyncio
import logging
import os
import sys

# Ensure backend/src is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("━" * 50)
    logger.info("PAYTM GROWTHPILOT AI — Synthetic Data Seeder")
    logger.info("Sandbox · Synthetic Demo Data · SEED=42")
    logger.info("━" * 50)

    from src.core.database import create_all_tables
    logger.info("Creating database tables...")
    await create_all_tables()

    from data.generators.synthetic import SyntheticDataGenerator
    gen = SyntheticDataGenerator(seed=42)
    await gen.run()

    logger.info("━" * 50)
    logger.info("✅  Seed complete!")
    logger.info("   Hero merchant : Rajesh Tea & Snacks")
    logger.info("   Login email   : rajesh@teaandsnacks.com")
    logger.info("   Login password: demo1234")
    logger.info("   API docs      : http://localhost:8000/docs")
    logger.info("━" * 50)


if __name__ == "__main__":
    asyncio.run(main())
