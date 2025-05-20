import asyncio

from xhs.core import XiaoHongShuCrawler


async def main():
    crawler = XiaoHongShuCrawler()
    await crawler.start()


if __name__ == "__main__":
    asyncio.run(main())
