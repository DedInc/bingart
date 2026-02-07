# bingart

bingart is an unofficial async API wrapper for Bing Image & Video Creator. It allows you to programmatically generate AI-powered images and videos using Bing's creation tools with support for multiple models and aspect ratios.

> **Warning:** The `_U` auth cookie should be changed every 2-4 weeks for proper functionality.

## Description

This module uses web scraping and engineering techniques to interface with Bing's internal image and video creation APIs. It is not an official API client.

### Key Features

- **Fully asynchronous** — built on `curl_cffi` `AsyncSession` and `asyncio`
- **Generate images** with multiple AI models (DALL-E, GPT-4O, MAI1)
- **Generate videos** from text prompts
- **Custom aspect ratios** (Square, Landscape, Portrait)
- **Get image URLs** — up to 4 generated images per request
- **Flexible authentication** via cookies or auto-fetched from browsers
- **Enhanced prompts** — get AI-improved versions of your prompts
- **Async context manager** support (`async with`)
- **Custom exceptions** for common error handling

## Installation

```bash
pip install bingart
```

## Usage

### Basic Setup

Import and instantiate the `BingArt` class with a valid `_U` cookie value:

```python
import asyncio
from bingart import BingArt

async def main():
    bing_art = BingArt(auth_cookie_U='your_cookie_value_here')
    try:
        result = await bing_art.generate('sunset over mountains')
        print(result)
    finally:
        await bing_art.close()

asyncio.run(main())
```

### Using Async Context Manager (Recommended)

```python
import asyncio
from bingart import BingArt

async def main():
    async with BingArt(auth_cookie_U='your_cookie_value_here') as bing_art:
        result = await bing_art.generate('sunset over mountains')
        print(result)

asyncio.run(main())
```

### Auto Cookie Detection

Let bingart automatically fetch cookies from your installed browsers:

```python
from bingart import BingArt

# Auto-fetch cookies from Chrome, Edge, Firefox, Brave, Opera, Vivaldi, or Chromium
bing_art = BingArt(auto=True)
```

Supported browsers for auto-detection:
- Chrome
- Edge
- Firefox
- Brave
- Opera
- Vivaldi
- Chromium

### Advanced Usage with Models and Aspect Ratios

```python
import asyncio
from bingart import BingArt, Model, Aspect

async def main():
    async with BingArt(auth_cookie_U='your_cookie_value') as bing_art:
        # Generate with GPT-4O model in portrait aspect
        result = await bing_art.generate(
            'a futuristic cityscape',
            model=Model.GPT4O,
            aspect=Aspect.PORTRAIT
        )
        print(result)

        # Generate with MAI1 model in landscape aspect
        result = await bing_art.generate(
            'serene mountain landscape',
            model=Model.MAI1,
            aspect=Aspect.LANDSCAPE
        )
        print(result)

        # Generate with DALL-E (default) in square aspect
        result = await bing_art.generate(
            'abstract art composition',
            model=Model.DALLE,
            aspect=Aspect.SQUARE
        )
        print(result)

asyncio.run(main())
```

### Available Models

```python
from bingart import Model

Model.DALLE    # DALL-E 3 (default)
Model.GPT4O    # GPT-4O image generation
Model.MAI1     # MAI1 model
```

### Available Aspect Ratios

```python
from bingart import Aspect

Aspect.SQUARE      # 1:1 (default)
Aspect.LANDSCAPE   # 7:4 (wide)
Aspect.PORTRAIT    # 4:7 (tall)
```

### Video Generation

```python
import asyncio
from bingart import BingArt

async def main():
    async with BingArt(auth_cookie_U='your_cookie_value') as bing_art:
        result = await bing_art.generate(
            'a dancing robot in a futuristic city',
            content_type='video'
        )
        print(result)

asyncio.run(main())
```

## Output Format

### Image Generation Response

```json
{
  "images": [
    {"url": "https://th.bing.com/th/id/OIG.xxx?pid=ImgGn"},
    {"url": "https://th.bing.com/th/id/OIG.yyy?pid=ImgGn"},
    {"url": "https://th.bing.com/th/id/OIG.zzz?pid=ImgGn"},
    {"url": "https://th.bing.com/th/id/OIG.www?pid=ImgGn"}
  ],
  "prompt": "enhanced version of your original prompt",
  "model": "GPT4O",
  "aspect": "PORTRAIT"
}
```

### Video Generation Response

```json
{
  "video": {
    "video_url": "https://..."
  },
  "prompt": "your original prompt"
}
```

## Exception Handling

```python
import asyncio
from bingart import BingArt, AuthCookieError, PromptRejectedError

async def main():
    try:
        async with BingArt(auth_cookie_U='your_cookie_value') as bing_art:
            result = await bing_art.generate('your prompt here')
            print(result)
    except AuthCookieError:
        print("Invalid authentication cookie or session expired")
    except PromptRejectedError:
        print("Prompt was rejected due to content policy violation")

asyncio.run(main())
```

### Available Exceptions

- `AuthCookieError`: Raised when authentication cookie is invalid or expired
- `PromptRejectedError`: Raised when prompt violates content policy or is rejected as unethical

## Getting Your Cookie

1. Open your browser and go to [Bing Image Creator](https://www.bing.com/images/create)
2. Log in with your Microsoft account
3. Open Developer Tools (F12)
4. Go to Application/Storage → Cookies → `https://www.bing.com`
5. Find the `_U` cookie and copy its value

## Complete Example

```python
import asyncio
from bingart import BingArt, Model, Aspect, AuthCookieError, PromptRejectedError

async def main():
    try:
        async with BingArt(auto=True) as bing_art:
            # Generate multiple images with different settings
            prompts = [
                {
                    "query": "cyberpunk cityscape at night",
                    "model": Model.GPT4O,
                    "aspect": Aspect.LANDSCAPE
                },
                {
                    "query": "portrait of a mystical wizard",
                    "model": Model.DALLE,
                    "aspect": Aspect.PORTRAIT
                },
                {
                    "query": "abstract geometric patterns",
                    "model": Model.MAI1,
                    "aspect": Aspect.SQUARE
                }
            ]

            for config in prompts:
                print(f"\nGenerating: {config['query']}")
                result = await bing_art.generate(
                    config['query'],
                    model=config['model'],
                    aspect=config['aspect']
                )

                print(f"Model: {result['model']}")
                print(f"Aspect: {result['aspect']}")
                print(f"Enhanced prompt: {result['prompt']}")
                print(f"Generated {len(result['images'])} images")

                for idx, img in enumerate(result['images'], 1):
                    print(f"  Image {idx}: {img['url']}")

            # Generate a video
            print("\nGenerating video...")
            video_result = await bing_art.generate(
                'a cat playing piano',
                content_type='video'
            )
            print(f"Video URL: {video_result['video']['video_url']}")

    except AuthCookieError as e:
        print(f"Authentication error: {e}")
    except PromptRejectedError as e:
        print(f"Prompt rejected: {e}")

asyncio.run(main())
```

## Requirements

- Python >= 3.6
- curl_cffi
- rookiepy

## Contributing

Pull requests are welcome! Please open an issue to discuss major changes before submitting.

## License

MIT License - see LICENSE file for details

## Disclaimer

This is an unofficial API wrapper and is not affiliated with Microsoft or Bing. Use responsibly and in accordance with Bing's terms of service.
