from playwright.sync_api import BrowserContext

from tools import utils


class XiaoHongShuLogin:
    def __init__(
        self, login_type: str, browser_context: BrowserContext, cookie_str: str
    ):
        self.login_type = login_type
        self.browser_context = browser_context
        self.cookie_str = cookie_str

    async def begin(self):
        if self.login_type == "cookie":
            await self.login_by_cookies()
        else:
            raise ValueError("login type not supported")

    async def login_by_cookies(self):
        for key, value in utils.convert_str_cookie_to_dict(self.cookie_str).items():
            if key != "web_session":
                continue
            await self.browser_context.add_cookies(
                [
                    {
                        "name": key,
                        "value": value,
                        "domain": ".xiaohongshu.com",
                        "path": "/",
                    }
                ]
            )
