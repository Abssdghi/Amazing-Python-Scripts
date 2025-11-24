import urllib.parse
import requests
import json
from bs4 import BeautifulSoup


def get_cover(url, width, height, format="jpg", crop_option=""):
    """
    Generate a full Apple Music artwork URL with proper width, height, format, and crop settings.
    """
    if not isinstance(url, str):
        return url

    try:
        new_url = (
            url.replace("{w}", str(width))
               .replace("{h}", str(height))
               .replace("{c}", crop_option)
               .replace("{f}", format)
        )
        return new_url
    except (TypeError, AttributeError):
        return url


def convert_album_to_song_url(album_url):
    """
    Convert an Apple Music album-track URL into a direct Apple Music song URL.
    """
    try:
        parsed = urllib.parse.urlparse(album_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        song_id = query_params.get("i", [None])[0]

        if not song_id:
            return None

        parts = parsed.path.split("/")
        if len(parts) < 4:
            return None

        country = parts[1]
        title = parts[3]

        return f"https://music.apple.com/{country}/song/{title}/{song_id}"

    except (IndexError, KeyError, TypeError, AttributeError, ValueError):
        return None


def get_all_singles(url="https://music.apple.com/us/artist/king-princess/1349968534"):
    """
    Fetch all singles & EP URLs from an Apple Music artist page.
    """
    result = []

    full_url = f"{url}/see-all?section=singles"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(full_url, headers=headers, timeout=10)
        res.raise_for_status()
    except requests.RequestException:
        return result

    soup = BeautifulSoup(res.text, "html.parser")
    script_tag = soup.find("script", {"id": "serialized-server-data"})
    if not script_tag:
        return result

    try:
        data = json.loads(script_tag.text)
        sections = data[0]["data"]["sections"]
        if not sections:
            return result

        items = sections[0].get("items", [])
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return result

    for item in items:
        try:
            action_url = item["segue"]["actionMetrics"]["data"][0]["fields"]["actionUrl"]
            result.append(action_url)
        except (KeyError, IndexError, TypeError):
            continue

    return result
