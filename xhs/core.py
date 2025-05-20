import json
from email.mime import base
from typing import Optional
from unittest import async_case

from playwright.async_api import BrowserContext, BrowserType, Page, async_playwright

from config import base_config
from tools import utils
from xhs.client import XiaoHongShuClient
from xhs.helper import get_search_id
from xhs.login import XiaoHongShuLogin


class XiaoHongShuCrawler:
    context_page: Page
    xhs_client: XiaoHongShuClient
    browser_context: BrowserContext

    def __init__(self) -> None:
        self.index_url = "https://www.xiaohongshu.com"
        self.user_agent = base_config.UA

    async def start(self) -> None:
        async with async_playwright() as playwright:
            # Launch a browser context.
            chromium = playwright.chromium
            self.browser_context = await self.launch_browser(chromium, self.user_agent)

            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)

            # Create a client to interact with the xiaohongshu website.
            self.xhs_client = await self.create_xhs_client()

            # if not await self.xhs_client.pong():
            login_obj = XiaoHongShuLogin(
                login_type=base_config.LOGIN_TYPE,
                browser_context=self.browser_context,
                cookie_str=base_config.COOKIES,
            )

            await login_obj.begin()
            await self.xhs_client.update_cookies(browser_context=self.browser_context)

            await self.search()

            print("Xhs Crawler finished ...")

    async def search(self) -> None:

        search_id = get_search_id()  # 相同关键词，获取更分页的时候不用更改
        notes_res = await self.xhs_client.get_note_by_keyword(
            keyword=base_config.KEYWORD,
            search_id=search_id,
        )
        print(json.dumps(notes_res, indent=2, ensure_ascii=False))

    async def create_xhs_client(self) -> XiaoHongShuClient:
        cookie_str, cookie_dict = utils.convert_cookies(
            await self.browser_context.cookies()
        )
        xhs_client_obj = XiaoHongShuClient(
            headers={
                "User-Agent": self.user_agent,
                "Cookie": cookie_str,
                "Origin": "https://www.xiaohongshu.com",
                "Referer": "https://www.xiaohongshu.com",
                "Content-Type": "application/json;charset=UTF-8",
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )

        return xhs_client_obj

    async def launch_browser(
        self, chromium: BrowserType, user_agent: Optional[str], headless: bool = True
    ):
        browser = await chromium.launch(headless=headless)
        browser_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=user_agent,
        )
        return browser_context

    async def close(self):
        await self.browser_context.close()
