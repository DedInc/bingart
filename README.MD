# bingart

bingart is an unofficial API wrapper for Bing Image & Video Creator. It allows you to programmatically generate AI-powered images and videos using Bing's creation tools with support for multiple models and aspect ratios.

> **Warning:** The `_U` auth cookie should be changed every 2-4 weeks for proper functionality.

## Description 

This module uses web scraping and engineering techniques to interface with Bing's internal image and video creation APIs. It is not an official API client. 

### Key Features

- **Generate images** with multiple AI models (DALL-E, GPT-4O, MAI1)
- **Generate videos** from text prompts
- **Custom aspect ratios** (Square, Landscape, Portrait)
- **Get image URLs** - up to 4 generated images per request
- **Flexible authentication** via cookies or auto-fetched from browsers
- **Enhanced prompts** - get AI-improved versions of your prompts
- **Custom exceptions** for common error handling

## Installation

```bash
pip install bingart
```

## Usage

### Basic Setup

Import and instantiate the `BingArt` class with a valid `_U` cookie value:

```python
from bingart import BingArt

# Initialize with authentication cookie
bing_art = BingArt(auth_cookie_U='your_cookie_value_here')

try:
    # Generate images
    result = bing_art.generate('sunset over mountains')
    print(result)
finally:
    bing_art.close()
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
from bingart import BingArt, Model, Aspect

bing_art = BingArt(auth_cookie_U='your_cookie_value')

# Generate with GPT-4O model in portrait aspect
result = bing_art.generate(
    'a futuristic cityscape',
    model=Model.GPT4O,
    aspect=Aspect.PORTRAIT
)
print(result)

# Generate with MAI1 model in landscape aspect
result = bing_art.generate(
    'serene mountain landscape',
    model=Model.MAI1,
    aspect=Aspect.LANDSCAPE
)
print(result)

# Generate with DALL-E (default) in square aspect
result = bing_art.generate(
    'abstract art composition',
    model=Model.DALLE,
    aspect=Aspect.SQUARE
)
print(result)

bing_art.close()
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
from bingart import BingArt

bing_art = BingArt(auth_cookie_U='your_cookie_value')

# Generate a video
result = bing_art.generate(
    'a dancing robot in a futuristic city',
    content_type='video'
)
print(result)

bing_art.close()
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
from bingart import BingArt, AuthCookieError, PromptRejectedError

try:
    bing_art = BingArt(auth_cookie_U='your_cookie_value')
    result = bing_art.generate('your prompt here')
    print(result)
except AuthCookieError:
    print("Invalid authentication cookie or session expired")
except PromptRejectedError:
    print("Prompt was rejected due to content policy violation")
finally:
    bing_art.close()
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
from bingart import BingArt, Model, Aspect, AuthCookieError, PromptRejectedError

def main():
    try:
        # Initialize with auto cookie detection
        bing_art = BingArt(auto=True)
        
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
            result = bing_art.generate(
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
        video_result = bing_art.generate(
            'a cat playing piano',
            content_type='video'
        )
        print(f"Video URL: {video_result['video']['video_url']}")
        
    except AuthCookieError as e:
        print(f"Authentication error: {e}")
    except PromptRejectedError as e:
        print(f"Prompt rejected: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        bing_art.close()

if __name__ == "__main__":
    main()
```

## Session Management

Always close the session when you're done:

```python
# Using try-finally
bing_art = BingArt(auth_cookie_U='...')
try:
    result = bing_art.generate('your prompt')
finally:
    bing_art.close()

# Or using context manager pattern (if you implement __enter__/__exit__)
# This is recommended for future versions
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