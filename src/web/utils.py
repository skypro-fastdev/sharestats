from fastapi.requests import Request
from fastapi.responses import Response


def add_no_cache_headers(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_orientation(request: Request) -> str:
    if "/vk/" in request.url.path:
        return "vk_post"
    if "/h/" in request.url.path:
        return "horizontal"
    return "vertical"


def is_social_bot(request: Request) -> bool:
    user_agent = request.headers.get("User-Agent", "").lower()
    referer = request.headers.get("Referer", "")

    bots = ("telegrambot", "instagram", "facebookexternalhit", "linkedinbot", "vkshare")  # 'twitterbot'
    social_referers = ("instagram.com", "facebook.com", "t.co", "t.me", "linkedin.com")  # 'twitter.com', 'vk.com'

    is_bot = any(bot in user_agent for bot in bots)
    is_social_referer = any(social in referer for social in social_referers)
    is_facebook_preview = request.headers.get("X-Purpose") == "preview"

    return is_bot or is_social_referer or is_facebook_preview
