from typing import Dict, List, Optional, Tuple

from playwright.async_api import Cookie


def convert_cookies(cookies: Optional[List[Cookie]]) -> Tuple[str, Dict]:
    if not cookies:
        return "", {}
    cookies_str = ";".join(
        [f"{cookie.get('name')}={cookie.get('value')}" for cookie in cookies]
    )
    cookie_dict = dict()
    for cookie in cookies:
        cookie_dict[cookie.get("name")] = cookie.get("value")
    return cookies_str, cookie_dict


def convert_str_cookie_to_dict(cookie_str: str) -> Dict:
    cookie_dict: Dict[str, str] = dict()
    if not cookie_str:
        return cookie_dict
    for cookie in cookie_str.split(";"):
        cookie = cookie.strip()
        if not cookie:
            continue
        cookie_list = cookie.split("=")
        if len(cookie_list) != 2:
            continue
        cookie_value = cookie_list[1]
        if isinstance(cookie_value, list):
            cookie_value = "".join(cookie_value)
        cookie_dict[cookie_list[0]] = cookie_value
    return cookie_dict
