import requests
import re
import time
import rookiepy
from urllib.parse import urlencode

class AuthCookieError(Exception):
    pass

class PromptRejectedError(Exception):
    pass

class BingArt:
    def __init__(self, auth_cookie_U=None, auth_cookie_KievRPSSecAuth=None, auto=False):
        self.session = requests.Session()
        self.base_url = 'https://www.bing.com/images/create'

        if auto:
            self.auth_cookie_U, self.auth_cookie_KievRPSSecAuth = self.get_auth_cookies()
        else:
            self.auth_cookie_U = auth_cookie_U
            self.auth_cookie_KievRPSSecAuth = auth_cookie_KievRPSSecAuth

        self.headers = self._prepare_headers()

    def scan_cookies(self, cookies):
        auth_cookie_U = auth_cookie_KievRPSSecAuth = None
        for cookie in cookies:
            if cookie['domain'] == '.bing.com':
                if cookie['name'] == '_U':
                    auth_cookie_U = cookie['value']
                elif cookie['name'] == 'KievRPSSecAuth':
                    auth_cookie_KievRPSSecAuth = cookie['value']
        return auth_cookie_U, auth_cookie_KievRPSSecAuth

    def get_auth_cookies(self):
        known_browsers = [
            'arc', 'brave', 'chrome', 'chromium', 'edge', 'firefox',
            'librewolf', 'octo_browser', 'opera', 'opera_gx', 'vivaldi'
        ]

        for browser_name in known_browsers:
            try:
                browser_func = getattr(rookiepy, browser_name)
                cookies = browser_func()
                auth_cookie_U, auth_cookie_KievRPSSecAuth = self.scan_cookies(cookies)
                if auth_cookie_U:
                    return auth_cookie_U, auth_cookie_KievRPSSecAuth
            except Exception:
                continue

        raise AuthCookieError('Failed to fetch authentication cookies automatically.')

    def _prepare_headers(self, content_type='image'):
        cookie_str = ''
        if self.auth_cookie_U:
            cookie_str += f'_U={self.auth_cookie_U};'
        if self.auth_cookie_KievRPSSecAuth:
            cookie_str += f' KievRPSSecAuth={self.auth_cookie_KievRPSSecAuth};'

        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookie_str
        }

        if content_type == 'video':
            base_headers['Referer'] = f'{self.base_url}?ctype=video'
            base_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            base_headers['Referer'] = self.base_url

        return base_headers

    def _get_balance(self):
        response = self.session.get(self.base_url)
        try:
            coins = 15 - int(re.search(r'<div id="reward_c" data-tb="(\d+)"', response.text).group(1))
        except AttributeError:
            raise AuthCookieError('Auth cookie failed!')
        return coins

    def _fetch_images(self, encoded_query, ID, IG):
        images = []
        while True:
            response = self.session.get(f'{self.base_url}/async/results/{ID}?{encoded_query}&IG={IG}&IID=images.as'.replace('&nfy=1', ''))
            if 'text/css' in response.text:
                src_urls = re.findall(r'src="([^"]+)"', response.text)
                for src_url in src_urls:
                    if '?' in src_url:
                        clean_url = src_url.split('?')[0] + '?pid=ImgGn'
                        images.append({'url': clean_url})
                return images
            time.sleep(5)

    def _fetch_video(self, encoded_query, ID):
        while True:
            response = self.session.get(f'{self.base_url}/async/results/{ID}?{encoded_query}&ctype=video&sm=1&girftp=1')
            try:
                result = response.json()
                if result.get('errorMessage') == 'Pending':
                    time.sleep(5)
                    continue
                elif result.get('showContent'):
                    return {'video_url': result['showContent']}
                else:
                    return None
            except ValueError:
                video_url = re.search(r'ourl="([^"]+)"', response.text)
                if video_url:
                    return {'video_url': video_url.group(1)}
                else:
                    time.sleep(5)
                    continue
    
    def _handle_creation_error(self, response):
        if 'data-clarity-tag="BlockedByContentPolicy"' in response.text or 'girer_center block_icon' in response.text:
            raise PromptRejectedError('Error! Your prompt has been rejected for content policy reasons.')
        else:
            raise AuthCookieError('Auth cookie failed!')

    def generate(self, query, content_type='image'):
        encoded_query = urlencode({'q': query})
        
        if content_type == 'image':
            headers = self.headers
            coins = self._get_balance()
            rt = '4' if coins > 0 else '3'
            creation_url = f'{self.base_url}?{encoded_query}&rt={rt}&FORM=GENCRE'
        elif content_type == 'video':
            headers = self._prepare_headers(content_type='video')
            creation_url = f'{self.base_url}?{encoded_query}&rt=4&FORM=GENCRE&ctype=video&pt=4&sm=1'
        else:
            raise ValueError("content_type must be 'image' or 'video'")

        self.session.headers.update(headers)
        response = self.session.post(creation_url, data={'q': query})

        try:
            if content_type == 'image':
                ID = re.search(';id=([^"]+)"', response.text).group(1)
                IG = re.search('IG:"([^"]+)"', response.text).group(1)
            else:
                ID = re.search(r'id=([^&]+)', response.url).group(1)
                IG = None
        except AttributeError:
            self._handle_creation_error(response)

        if content_type == 'image':
            result = self._fetch_images(encoded_query, ID, IG)
            return {'images': result, 'prompt': query}
        else:
            result = self._fetch_video(encoded_query, ID)
            return {'video': result, 'prompt': query}

    def generate_images(self, query):
        return self.generate(query, content_type='image')

    def generate_video(self, query):
        return self.generate(query, content_type='video')

    def close_session(self):
        self.session.close()