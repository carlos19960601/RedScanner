import asyncio
import json
import time
from email.mime import base
from typing import Dict, Optional
from unittest import async_case

from playwright.async_api import BrowserContext, BrowserType, Page, async_playwright

from config import base_config
from tools import utils
from xhs.client import XiaoHongShuClient
from xhs.exception import DataFetchError
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

        semaphore = asyncio.Semaphore(base_config.MAX_CONCURRENCY_NUM)
        task_list = [
            self.get_note_detail_async_task(
                post_item.get("id"),
                xsec_source=post_item.get("xsec_source"),
                xsec_token=post_item.get("xsec_token"),
                semaphore=semaphore,
            )
            for post_item in notes_res.get("items", {})
            if post_item.get("model_type") not in ("rec_query", "hot_query")
        ]
        note_details = await asyncio.gather(*task_list)
        print(json.dumps(note_details, indent=2, ensure_ascii=False))

    async def get_note_detail_async_task(
        self,
        note_id: str,
        xsec_source: str,
        xsec_token: str,
        semaphore: asyncio.Semaphore,
    ) -> Optional[Dict]:
        note_detail_from_html, note_detail_from_api = None, None
        async with semaphore:
            try:
                # 尝试直接获取网页版笔记详情，携带cookie
                note_detail_from_html: Optional[Dict] = (
                    await self.xhs_client.get_note_by_id_from_html(
                        note_id,
                        xsec_source,
                        xsec_token,
                        enable_cookie=True,
                    )
                )
                time.sleep(1)
                if not note_detail_from_html:
                    # 如果网页版笔记详情获取失败，则尝试API获取
                    note_detail_from_api = await self.xhs_client.get_note_by_id(
                        note_id, xsec_source, xsec_token
                    )

                note_detail = note_detail_from_html or note_detail_from_api
                if note_detail:
                    return note_detail

            except DataFetchError as e:
                print(f"Get note detail error: {e}")
                return None

    async def get_note_by_id(
        self, note_id: str, xsec_source: str, xsec_token: str
    ) -> Dict:
        if xsec_source == "":
            xsec_source = "pc_search"

        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": 1},
            "xsec_source": xsec_source,
            "xsec_token": xsec_token,
        }
        uri = "/api/sns/web/v1/feed"
        res = await self.post(uri, data)
        if res and res.get("items"):
            res_dict: Dict = res["items"][0]["note_card"]
            return res_dict
        # 爬取频繁了可能会出现有的笔记能有结果有的没有
        utils.logger.error(f"get note id:{note_id} empty and res:{res}")
        return dict()

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
