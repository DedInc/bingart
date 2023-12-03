# 🎨 bingart

bingart is an unofficial 🤫 API wrapper for Bing Image Creator (based on DALL-E 3). It allows you to programmatically generate 🖼️ AI-powered images using Bing's image creation tool.

> ⚠️ **Warning:** The `_U` auth cookie should be changed every 2-4 weeks for working.

## 💡 Description 

This module uses web scraping and engineering techniques to interface with Bing's internal image creation APIs. It is not an official API client. 

### 🔑 Key Features

- 🖼️ **Generate images** by providing a text prompt
- 📸 **Get image URLs** - up to 4 generated images  
- 🔐 **Authentication** via saved Bing cookies
- ⚠️ **Custom exceptions** for common issues

## 💻 Usage

Import and instantiate the `BingArt` class with a valid `_U` cookie value:

```python
from bingart import BingArt

bing = BingArt(auth_cookie='...')
```

Call `generate_images()` with your query text:

```python 
results = bing.generate_images("a cat painting in Picasso style")
```

The return value contains image URLs and original prompt: 

```json
{
  "images": [
    {"url": "https://..."}
  ],
  "prompt": "a cat painting in Picasso style"
}
```

## 🚨 Exceptions

- `AuthCookieError`: Invalid authentication cookie
- `PromptRejectedError`: Prompt rejected as unethical  

## 🤝 Contributing

Pull requests welcome! Please open an issue to discuss major changes.