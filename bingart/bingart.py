import re
import time
import asyncio
from enum import Enum
from urllib.parse import urlencode

import rookiepy
from curl_cffi.requests import AsyncSession

BASE_URL = "https://www.bing.com/images/create"
BING_ORIGIN = "https://www.bing.com"
IMAGE_HOST = "https://th.bing.com"

POLL_INTERVAL = 5
POLL_INTERVAL_GPT4O = 3

BROWSERS = ["chrome", "edge", "firefox", "brave", "opera", "vivaldi", "chromium"]

REJECTION_MARKERS = [
    "girer_center block_icon",
    'data-clarity-tag="BlockedByContentPolicy"',
    'dq-err="',
]

AUTH_MARKER = 'id="id_a" style="display:none"'
GPT4O_STREAMING_MARKER = "imgri-inner-container strm"

MODEL_BODY_MAP = {0: "dalle", 1: "gpt4o", 4: "maiimage1"}
ASPECT_BODY_MAP = {1: "1:1", 2: "7:4", 3: "4:7"}

RE_IG = re.compile(r'IG:"([^"]+)"')
RE_SALT = re.compile(r'Salt:"([^"]+)"')
RE_ID = re.compile(r'id=([^&"]+)')
RE_SELCAP = re.compile(r'data-selcap="([^"]+)"')
RE_ALT = re.compile(r'<img[^>]*class="image-row-img[^"]*"[^>]*alt="([^"]+)"')
RE_SRC_FULL_OIG = re.compile(r'src="(https://th\.bing\.com/th/id/OIG[^"]+)"')
RE_SRC_REL_OIG = re.compile(r'src="(/th/id/OIG[^"]+)"')
RE_SRC_ANY = re.compile(r'src="([^"]+)"')
RE_VIDEO_URL = re.compile(r'ourl="([^"]+)"')


class Model(Enum):
    DALLE = 0
    GPT4O = 1
    MAI1 = 4


class Aspect(Enum):
    SQUARE = 1
    LANDSCAPE = 2
    PORTRAIT = 3


class AuthCookieError(Exception):
    pass


class PromptRejectedError(Exception):
    pass


def _check_prompt_rejected(html):
    if any(marker in html for marker in REJECTION_MARKERS):
        raise PromptRejectedError("Prompt rejected for content policy.")


def _to_full_url(url):
    if url.startswith("/"):
        return f"{IMAGE_HOST}{url}"
    return url


def _clean_image_url(src_url):
    full = _to_full_url(src_url)
    base = full.split("?")[0] if "?" in full else full
    return base + "?pid=ImgGn"


def _extract_enhanced_prompt(html):
    match = RE_SELCAP.search(html) or RE_ALT.search(html)
    return match.group(1) if match else None


def _extract_image_urls(html, model_value):
    if model_value == Model.GPT4O.value:
        src_urls = RE_SRC_FULL_OIG.findall(html) or RE_SRC_REL_OIG.findall(html)
    else:
        src_urls = RE_SRC_ANY.findall(html)

    images = []
    for src_url in src_urls:
        full = _to_full_url(src_url)
        if "?" in full or "/th/id/" in full:
            images.append({"url": _clean_image_url(src_url)})
    return images


class BingArt:
    def __init__(self, auth_cookie_U=None, auto=False):
        self.session = AsyncSession(impersonate="chrome")
        self.auth_cookie_U = self._find_browser_cookie() if auto else auth_cookie_U
        self.IG = None
        self.Salt = None
        self._prepare_session()

    def _find_browser_cookie(self):
        for name in BROWSERS:
            try:
                for cookie in getattr(rookiepy, name)():
                    if cookie["domain"] == ".bing.com" and cookie["name"] == "_U":
                        return cookie["value"]
            except Exception:
                continue
        raise AuthCookieError("Failed to fetch authentication cookies automatically.")

    def _prepare_session(self):
        self.session.headers.update(
            {
                "authority": "www.bing.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "content-type": "application/x-www-form-urlencoded",
                "origin": BING_ORIGIN,
                "referer": BASE_URL,
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            }
        )
        if self.auth_cookie_U:
            self.session.cookies.set("_U", self.auth_cookie_U, domain=".bing.com")

    async def _fetch_config(self):
        response = await self.session.get(BASE_URL)
        if AUTH_MARKER not in response.text:
            raise AuthCookieError(
                "Authentication failed. Please check your auth cookie."
            )

        for attr, pattern in [("IG", RE_IG), ("Salt", RE_SALT)]:
            match = pattern.search(response.text)
            if match:
                setattr(self, attr, match.group(1))

        srchhpgusr = f"SRCHLANG=ru&HV={int(time.time())}&HVE={self.Salt or ''}&IG={self.IG or ''}"
        self.session.cookies.set("SRCHHPGUSR", srchhpgusr, domain=".bing.com")

    async def _poll_images(self, query, request_id, model):
        mdl_value = model.value if isinstance(model, Model) else model
        interval = (
            POLL_INTERVAL_GPT4O if mdl_value == Model.GPT4O.value else POLL_INTERVAL
        )
        encoded = urlencode({"q": query})

        while True:
            url = f"{BASE_URL}/async/results/{request_id}?{encoded}&IG={self.IG}&IID=images.as"
            response = await self.session.get(url)
            _check_prompt_rejected(response.text)

            if "text/css" not in response.text:
                await asyncio.sleep(interval)
                continue

            if (
                mdl_value == Model.GPT4O.value
                and GPT4O_STREAMING_MARKER in response.text
            ):
                await asyncio.sleep(interval)
                continue

            images = _extract_image_urls(response.text, mdl_value)
            if images:
                return {
                    "images": images,
                    "enhanced_prompt": _extract_enhanced_prompt(response.text),
                }

            await asyncio.sleep(interval)

    async def _poll_video(self, query, request_id):
        encoded = urlencode({"q": query})

        while True:
            url = f"{BASE_URL}/async/results/{request_id}?{encoded}&IG={self.IG}&ctype=video&sm=1&girftp=1"
            response = await self.session.get(url)
            _check_prompt_rejected(response.text)

            if "errorMessage" in response.text and "Pending" in response.text:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            if "showContent" in response.text:
                try:
                    data = response.json()
                    if data.get("showContent"):
                        return {"video_url": data["showContent"]}
                except Exception:
                    pass

            match = RE_VIDEO_URL.search(response.text)
            if match:
                return {"video_url": match.group(1)}

            await asyncio.sleep(POLL_INTERVAL)

    def _build_params_and_payload(self, query, mdl_value, ar_value, content_type):
        params = {"q": query, "FORM": "GENCRE"}
        if self.IG:
            params["IG"] = self.IG

        if content_type == "video":
            self.session.headers["referer"] = f"{BASE_URL}?ctype=video"
            params.update(
                {
                    "rt": "3",
                    "mdl": "0",
                    "ar": "1",
                    "ctype": "video",
                    "pt": "3",
                    "sm": "0",
                }
            )
            payload = {"q": query, "model": "dalle", "aspectRatio": "1:1"}
        else:
            self.session.headers["referer"] = BASE_URL
            rt_value = "3" if mdl_value == 0 else "4"
            params.update({"rt": rt_value, "mdl": str(mdl_value), "ar": str(ar_value)})
            payload = {
                "q": query,
                "model": MODEL_BODY_MAP.get(mdl_value, "dalle"),
                "aspectRatio": ASPECT_BODY_MAP.get(ar_value, "1:1"),
            }

        return params, payload

    async def _submit_creation(self, params, payload):
        response = await self.session.post(
            BASE_URL, params=params, data=payload, allow_redirects=False
        )
        _check_prompt_rejected(response.text)

        redirect_url = response.headers.get("Location", "") or response.text
        if redirect_url.startswith("/"):
            redirect_url = f"{BING_ORIGIN}{redirect_url}"

        id_match = RE_ID.search(redirect_url)
        if not id_match:
            raise AuthCookieError("Auth failed or generic error.")

        if response.headers.get("Location"):
            redirect_response = await self.session.get(redirect_url)
            _check_prompt_rejected(redirect_response.text)

        return id_match.group(1)

    async def generate(
        self, query, model=Model.DALLE, aspect=Aspect.SQUARE, content_type="image"
    ):
        if self.IG is None:
            await self._fetch_config()

        mdl_value = model.value if isinstance(model, Model) else model
        ar_value = aspect.value if isinstance(aspect, Aspect) else aspect

        params, payload = self._build_params_and_payload(
            query, mdl_value, ar_value, content_type
        )
        request_id = await self._submit_creation(params, payload)

        if content_type == "video":
            result = await self._poll_video(query, request_id)
            return {"video": result, "prompt": query}

        result = await self._poll_images(query, request_id, model)
        prompt = result.get("enhanced_prompt") or query
        return {
            "images": result["images"],
            "prompt": prompt,
            "model": model.name if isinstance(model, Model) else model,
            "aspect": aspect.name if isinstance(aspect, Aspect) else aspect,
        }

    async def close(self):
        await self.session.close()

    async def __aenter__(self):
        await self._fetch_config()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
