import re
import time
from urllib.parse import urlencode
from enum import Enum
from curl_cffi import requests
import rookiepy


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


class BingArt:
    def __init__(self, auth_cookie_U=None, auto=False):
        self.session = requests.Session(impersonate="chrome")
        self.base_url = "https://www.bing.com/images/create"

        if auto:
            self.auth_cookie_U = self.get_auth_cookie()
        else:
            self.auth_cookie_U = auth_cookie_U

        self.IG = None
        self.Salt = None
        self.EventID = None

        self._prepare_headers()
        self._fetch_g_config()

    def scan_cookies(self, cookies):
        for cookie in cookies:
            if cookie["domain"] == ".bing.com" and cookie["name"] == "_U":
                return cookie["value"]
        return None

    def get_auth_cookie(self):
        known_browsers = [
            "chrome",
            "edge",
            "firefox",
            "brave",
            "opera",
            "vivaldi",
            "chromium",
        ]
        for browser_name in known_browsers:
            try:
                browser_func = getattr(rookiepy, browser_name)
                cookies = browser_func()
                auth_cookie_U = self.scan_cookies(cookies)
                if auth_cookie_U:
                    return auth_cookie_U
            except Exception:
                continue
        raise AuthCookieError("Failed to fetch authentication cookies automatically.")

    def _prepare_headers(self):
        base_headers = {
            "authority": "www.bing.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.bing.com",
            "referer": "https://www.bing.com/images/create",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        }
        self.session.headers.update(base_headers)
        if self.auth_cookie_U:
            self.session.cookies.set("_U", self.auth_cookie_U, domain=".bing.com")

    def _fetch_g_config(self):
        response = self.session.get(self.base_url)
        self._parse_g_config(response.text)
        self._update_cookies()

    def _parse_g_config(self, html):
        ig_match = re.search(r'IG:"([^"]+)"', html)
        if ig_match:
            self.IG = ig_match.group(1)

        salt_match = re.search(r'Salt:"([^"]+)"', html)
        if salt_match:
            self.Salt = salt_match.group(1)

        event_id_match = re.search(r'EventID:"([^"]+)"', html)
        if event_id_match:
            self.EventID = event_id_match.group(1)

    def _update_cookies(self):
        hv = int(time.time())
        srchhpgusr = f"SRCHLANG=ru&HV={hv}&HVE={self.Salt or ''}&IG={self.IG or ''}"
        self.session.cookies.set("SRCHHPGUSR", srchhpgusr, domain=".bing.com")

    def _fetch_images(self, encoded_query, ID, model=Model.DALLE):
        while True:
            url = f"{self.base_url}/async/results/{ID}?{encoded_query}&IG={self.IG}&IID=images.as"
            response = self.session.get(url)
            if "text/css" in response.text:
                mdl_value = model.value if isinstance(model, Model) else model

                if mdl_value == Model.GPT4O.value:
                    if "imgri-inner-container strm" in response.text:
                        time.sleep(5)
                        continue

                    src_urls = re.findall(
                        r'src="(https://th\.bing\.com/th/id/OIG[^"]+)"', response.text
                    )
                    images = []
                    for src_url in src_urls:
                        base_url = src_url.split("?")[0] if "?" in src_url else src_url
                        clean_url = base_url + "?pid=ImgGn"
                        images.append({"url": clean_url})
                    if images:
                        enhanced_prompt = None
                        selcap_match = re.search(
                            r'data-selcap="([^"]+)"', response.text
                        )
                        if selcap_match:
                            enhanced_prompt = selcap_match.group(1)
                        else:
                            alt_match = re.search(
                                r'<img[^>]*class="image-row-img[^"]*"[^>]*alt="([^"]+)"',
                                response.text,
                            )
                            if alt_match:
                                enhanced_prompt = alt_match.group(1)
                        return {"images": images, "enhanced_prompt": enhanced_prompt}

                    time.sleep(5)
                    continue

                src_urls = re.findall(r'src="([^"]+)"', response.text)
                images = []
                for src_url in src_urls:
                    if "?" in src_url:
                        clean_url = src_url.split("?")[0] + "?pid=ImgGn"
                        images.append({"url": clean_url})
                if images:
                    enhanced_prompt = None
                    selcap_match = re.search(r'data-selcap="([^"]+)"', response.text)
                    if selcap_match:
                        enhanced_prompt = selcap_match.group(1)
                    else:
                        alt_match = re.search(
                            r'<img[^>]*class="image-row-img[^"]*"[^>]*alt="([^"]+)"',
                            response.text,
                        )
                        if alt_match:
                            enhanced_prompt = alt_match.group(1)
                    return {"images": images, "enhanced_prompt": enhanced_prompt}
            time.sleep(5)

    def _fetch_video(self, encoded_query, ID):
        while True:
            url = f"{self.base_url}/async/results/{ID}?{encoded_query}&IG={self.IG}&ctype=video&sm=1&girftp=1"
            response = self.session.get(url)

            try:
                if "errorMessage" in response.text and "Pending" in response.text:
                    time.sleep(5)
                    continue

                if "showContent" in response.text:
                    try:
                        data = response.json()
                        if data.get("showContent"):
                            return {"video_url": data["showContent"]}
                    except Exception:
                        pass

                video_url_match = re.search(r'ourl="([^"]+)"', response.text)
                if video_url_match:
                    return {"video_url": video_url_match.group(1)}

            except Exception:
                pass

            time.sleep(5)

    def _handle_creation_error(self, response):
        if (
            'data-clarity-tag="BlockedByContentPolicy"' in response.text
            or "girer_center block_icon" in response.text
        ):
            raise PromptRejectedError("Prompt rejected for content policy.")
        raise AuthCookieError("Auth failed or generic error.")

    def generate(
        self, query, model=Model.DALLE, aspect=Aspect.SQUARE, content_type="image"
    ):
        mdl_value = model.value if isinstance(model, Model) else model
        ar_value = aspect.value if isinstance(aspect, Aspect) else aspect

        params = {
            "q": query,
            "FORM": "GENCRE",
        }
        if self.IG:
            params["IG"] = self.IG

        if content_type == "video":
            self.session.headers["referer"] = f"{self.base_url}?ctype=video"
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
            self.session.headers["referer"] = self.base_url
            model_body_map = {0: "dalle", 1: "gpt4o", 4: "maiimage1"}
            aspect_body_map = {1: "1:1", 2: "7:4", 3: "4:7"}

            body_model = model_body_map.get(mdl_value, "dalle")
            body_aspect = aspect_body_map.get(ar_value, "1:1")

            rt_value = "3" if mdl_value == 0 else "4"

            params.update({"rt": rt_value, "mdl": str(mdl_value), "ar": str(ar_value)})
            payload = {"q": query, "model": body_model, "aspectRatio": body_aspect}

        response = self.session.post(
            self.base_url, params=params, data=payload, allow_redirects=False
        )

        try:
            redirect_url = response.headers.get("Location", "") or response.text
            if redirect_url.startswith("/"):
                redirect_url = f"https://www.bing.com{redirect_url}"

            id_match = re.search(r'id=([^&"]+)', redirect_url)
            if not id_match:
                self._handle_creation_error(response)

            ID = id_match.group(1)

            if response.headers.get("Location"):
                self.session.get(redirect_url)

        except Exception:
            self._handle_creation_error(response)

        encoded_query = urlencode({"q": query})

        if content_type == "video":
            result = self._fetch_video(encoded_query, ID)
            return {"video": result, "prompt": query}
        else:
            result = self._fetch_images(encoded_query, ID, model)
            enhanced_prompt = result.get("enhanced_prompt")
            final_prompt = enhanced_prompt if enhanced_prompt else query
            return {
                "images": result["images"],
                "prompt": final_prompt,
                "model": model.name if isinstance(model, Model) else model,
                "aspect": aspect.name if isinstance(aspect, Aspect) else aspect,
            }

    def close(self):
        self.session.close()
