import urllib.parse
import requests
import json
from bs4 import BeautifulSoup


def get_cover(url, width, height, img_format="jpg", crop_option=""):
    """
    Generate a full Apple Music artwork URL\
    with proper width, height, format, and crop settings.

    Parameters
    ----------
    url : str
        The original Apple Music artwork template URL
        containing `{w}`, `{h}`, `{f}`, `{c}`.
    width : int or str
        Target width of the image.
    height : int or str
        Target height of the image.
    img_format : str, optional
        Image format (jpg, png, etc.). Defaults to "jpg".
    crop_option : str, optional
        Cropping mode used by Apple Music artwork URLs. Defaults to empty string.

    Returns
    -------
    str
        Fully formatted artwork URL.

    Notes
    -----
    Apple Music uses dynamic artwork URLs where dimensions and format are embedded
    in the URL as placeholders such as `{w}`, `{h}`, `{f}`, and `{c}`.
    """
    if not isinstance(url, str):
        return url

    try:
        new_url = (
            url.replace("{w}", str(width))
               .replace("{h}", str(height))
               .replace("{c}", crop_option)
               .replace("{f}", img_format)
        )
        return new_url
    except (TypeError, AttributeError):
        return url


def convert_album_to_song_url(album_url):
    """
    Convert an Apple Music album-track URL into a direct Apple Music song URL.

    Parameters
    ----------
    album_url : str
        Full Apple Music album URL that
        contains a track ID via the query parameter `?i=...`.

    Returns
    -------
    str or None
        Direct Apple Music song URL if `i` parameter exists.
        Otherwise, returns `None`.

    Examples
    --------
    Input:
        https://music.apple.com/us/album/song-name/12345?i=67890

    Output:
        https://music.apple.com/us/song/song-name/67890

    Notes
    -----
    Apple Music album pages embed individual song IDs through the query parameter `i`,
    which must be extracted and placed into a `/song/` URL.
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

    Parameters
    ----------
    url : str, optional
        Base artist page URL. Defaults to the sample King Princess artist link.

    Returns
    -------
    list[str]
        A list of Apple Music URLs for all singles & EPs for the artist.

    Notes
    -----
    - Apple Music loads singles under the `/see-all?section=singles` endpoint.
    - This function retrieves the serialized server data, parses the `items` section,
      and extracts the correct song/EP URLs.
    - Used internally by `artist_scrape()`.
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
            action_url = (
                item["segue"]["actionMetrics"]
                ["data"][0]["fields"]["actionUrl"]
            )
            result.append(action_url)
        except (KeyError, IndexError, TypeError):
            continue

    return result


def safe_action_url(item):
    """
    Safely extract an Apple Music "actionUrl" from a section item.

    This function attempts to extract a playable or navigational URL from
    Apple Music's internal JSON structure. It first looks for URLs provided
    via `segue -> actionMetrics`, which is the most common structure. If that
    fails, it falls back to the `contentDescriptor` URL when available.

    Parameters
    ----------
    item : dict
        A dictionary representing an Apple Music content item inside a section.

    Returns
    -------
    str or None
        The extracted URL if available, otherwise None.

    Notes
    -----
    This helper prevents repetitive try/except blocks throughout all scraper
    functions and gracefully handles missing keys, unexpected formats, or
    incomplete items.
    """
    try:
        # segue-based URLs (most items)
        return item["segue"]["actionMetrics"]["data"][0]["fields"]["actionUrl"]
    except Exception:
        pass

    try:
        # fallback: plain contentDescriptor
        return item["contentDescriptor"]["url"]
    except Exception:
        return None


def find_section(sections, key):
    """
    Locate a specific Apple Music section by matching a substring in its ID.

    This utility searches through the list of sections extracted from
    Apple Music's `serialized-server-data` and returns the first section
    whose "id" field contains the provided key substring.

    Parameters
    ----------
    sections : list[dict]
        List of section dictionaries parsed from Apple Music page data.
    key : str
        Substring to search for inside the section ID.

    Returns
    -------
    dict or None
        The matching section dictionary if found, otherwise None.

    Notes
    -----
    Apple Music uses structured section IDs such as:
        - "artist-detail-header-section"
        - "track-list"
        - "music-videos"
        - "similar-artists"
    This function simplifies section lookup and reduces repeated loops and
    conditional chains in scraper functions.
    """
    for sec in sections:
        if key in sec.get("id", ""):
            return sec
    return None


def append_urls_from_section(section, target_list):
    """
    Extract URLs from a section and append them to a target list.

    This helper iterates through all items inside a given Apple Music
    section, uses `safe_action_url()` to safely extract their URLs,
    and appends each valid URL to the provided list.

    Parameters
    ----------
    section : dict or None
        The section dictionary containing an "items" list. If None, the
        function does nothing.
    target_list : list
        The list to which valid extracted URLs will be appended.

    Returns
    -------
    None
        This function modifies target_list in-place.

    Notes
    -----
    Many Apple Music sections such as:
        - top songs
        - albums
        - playlists
        - videos
        - similar artists
    share the same internal structure. This helper removes code duplication
    and ensures unified URL extraction behavior.
    """
    if not section:
        return
    for it in section.get("items", []):
        url = safe_action_url(it)
        if url:
            target_list.append(url)