import asyncio
import json
from typing import Any, Dict, Union

import httpx
from playwright.async_api import BrowserContext, Page

from tools import utils
from xhs.exception import DataFetchError, IPBlockError
from xhs.field import SearchNoteType, SearchSortType
from xhs.helper import get_search_id, sign


class XiaoHongShuClient:
    def __init__(
        self,
        timeout=10,
        *,
        headers: Dict[str, str],
        playwright_page: Page,
        cookie_dict: Dict[str, str],
    ):
        self.timeout = timeout
        self.headers = headers
        self._host = "https://edith.xiaohongshu.com"
        self.playwright_page = playwright_page
        self.cookie_dict = cookie_dict

    async def get(self, uri: str):
        pass

    async def post(self, uri: str, data: Dict) -> Dict:
        """
        POST请求，对请求头签名
        Args:
            uri: 请求路由
            data: 请求体参数

        Returns:

        """
        headers = await self._pre_headers(uri, data)
        json_str = json.dumps(data)
        return await self.request(
            method="POST", url=f"{self._host}{uri}", data=json_str, headers=headers
        )

    async def request(self, method: str, url: str, **kwargs) -> Union[str, Any]:
        """
        封装httpx的公共请求方法，对请求响应做一些处理
        Args:
            method: 请求方法
            url: 请求的URL
            **kwargs: 其他请求参数，例如请求头、请求体等

        Returns:

        """
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, timeout=self.timeout, **kwargs)
        data: Dict = response.json()
        print(data)
        if data["success"]:
            return data.get("data", data.get("success", {}))
        elif data["code"] == self.IP_ERROR_CODE:
            raise IPBlockError(self.IP_ERROR_STR)
        else:
            raise DataFetchError(data.get("msg", None))

    async def pong(self) -> bool:
        """
        用于检查登录态是否失效了
        Returns:

        """
        """get a note to check if login state is ok"""
        ping_flag = False
        try:
            note_card: Dict = await self.get_note_by_keyword(keyword="小红书")
            print(note_card)
            if note_card.get("items"):
                ping_flag = True
        except Exception as e:
            print("Ping xhs failed: {e}, and try to login again...")
            ping_flag = False

        return ping_flag

    async def get_note_by_keyword(
        self,
        keyword: str,
        search_id: str = get_search_id(),
        page: int = 1,
        page_size: int = 20,
        sort: SearchSortType = SearchSortType.GENERAL,
        note_type: SearchNoteType = SearchNoteType.ALL,
    ) -> Dict:
        """
        根据关键词搜索笔记
        Args:
            keyword: 关键词参数
            page: 分页第几页
            page_size: 分页数据长度
            sort: 搜索结果排序指定
            note_type: 搜索的笔记类型

        Returns:

        """
        uri = "/api/sns/web/v1/search/notes"
        data = {
            "keyword": keyword,
            "search_id": search_id,
            "page": page,
            "page_size": page_size,
            "sort": sort.value,
            "note_type": note_type.value,
        }
        return await self.post(uri, data)

    async def _pre_headers(self, url: str, data=None) -> Dict:
        """
        请求头参数签名
        Args:
            url:
            data:

        Returns:

        """
        encrypt_params = await self.playwright_page.evaluate(
            "([url, data]) => window._webmsxyw(url,data)", [url, data]
        )
        local_storage = await self.playwright_page.evaluate("() => window.localStorage")

        signs = sign(
            a1=self.cookie_dict.get("a1", ""),
            b1=local_storage.get("b1", ""),
            x_s=encrypt_params.get("X-s", ""),
            x_t=str(encrypt_params.get("X-t", "")),
        )

        headers = {
            "X-S": signs["x-s"],
            "X-T": signs["x-t"],
            "x-S-Common": signs["x-s-common"],
            "X-B3-Traceid": signs["x-b3-traceid"],
        }
        self.headers.update(headers)

        return self.headers

    async def update_cookies(self, browser_context: BrowserContext):
        """
        API客户端提供的更新cookies方法，一般情况下登录成功后会调用此方法
        Args:
            browser_context: 浏览器上下文对象

        Returns:

        """

        cookie_str, cookie_dict = utils.convert_cookies(await browser_context.cookies())
        self.headers["Cookie"] = cookie_str
        self.cookie_dict = cookie_dict


if __name__ == "__main__":
    client = XiaoHongShuClient()
    asyncio.run(client.get_note_by_keyword(keyword="吹风机"))
