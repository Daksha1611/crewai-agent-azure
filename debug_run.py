# debug_run.py
import asyncio
from src.agents.crew import run_financial_crew

async def main():
    result = await run_financial_crew("TSLA")
    print(result)

asyncio.run(main())