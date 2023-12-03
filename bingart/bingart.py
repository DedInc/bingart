import requests
import re
import time
from urllib.parse import urlencode

class AuthCookieError(Exception):
    pass

class PromptRejectedError(Exception):
    pass

class BingArt:
    def __init__(self, auth_cookie):
        self.auth_cookie = auth_cookie

    def generate_images(self, query):        
        encoded_query = urlencode({'q': query})

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1474.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': 'https://www.bing.com/images/create',
            'Accept-Language': 'en-US;q=0.6,en;q=0.5',
            'Cookie': f'_U={self.auth_cookie}'
        }

        data = {
            'q': query,
            'qs': 'ds'
        }

        with requests.Session() as session:
            session.headers.update(headers)

            r = session.get('https://www.bing.com/images/create')

            try:
                coins = int(r.text.split('bal" aria-label="')[1].split(' ')[0])
            except IndexError:
                raise AuthCookieError('Auth cookie failed!')

        url = f'https://www.bing.com/images/create?{encoded_query}&rt=' + '4' if coins > 0 else '3' + '&FORM=GENCRE'

        with requests.Session() as session:
            session.headers = headers
            r = session.post(url, data=data)

            try:
                ID = r.text.split(';id=')[1].split('"')[0]
            except IndexError:
                raise PromptRejectedError('Error! Your prompt has been rejected for ethical reasons.')

            IG = r.text.split('IG:"')[1].split('"')[0]

            while True:
                r = session.get(f'https://www.bing.com/images/create/async/results/{ID}?{encoded_query}&IG={IG}&IID=images.as'.replace('&amp;nfy=1', ''))                
                if 'text/css' in r.text:
                    break
                time.sleep(5)

            src_urls = re.findall(r'src="([^"]+)"', r.text)
            src_urls = [url for url in src_urls if '?' in url]

            for i, src_url in enumerate(src_urls):
                new_url = src_url.replace(src_url.split('?')[1], 'pid=ImgGn')
                src_urls[i] = new_url
            return {'images': [{'url': src_url} for src_url in src_urls], 'prompt': query}