def format_video_embed_url(url: str | None) -> str | None:
    """
    Helper to convert standard YouTube/Vimeo links to embeddable formats.
    This function ensures that video URLs provided by users are transformed
    into a format suitable for embedding in iframes, preventing issues like
    "refused to connect" errors due to X-Frame-Options policies.
    """
    if not url:
        return url
    # YouTube: convert watch?v= or youtu.be/ to /embed/
    if "youtube.com/watch?v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "youtu.be/" in url:
        video_id = url.split("/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    # Vimeo: convert vimeo.com/ID to player.vimeo.com/video/ID
    if "vimeo.com/" in url and "player.vimeo.com" not in url:
        video_id = url.split("/")[-1].split("?")[0]
        return f"https://player.vimeo.com/video/{video_id}"
    return url