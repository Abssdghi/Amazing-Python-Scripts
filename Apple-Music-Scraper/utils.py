import urllib.parse
import requests, json
from bs4 import BeautifulSoup

def get_cover(url, width, height, format="jpg", crop_option=""):
    """
    Generate a full Apple Music artwork URL with proper width, height, format, and crop settings.

    Parameters
    ----------
    url : str
        The original Apple Music artwork template URL containing `{w}`, `{h}`, `{f}`, `{c}`.
    width : int or str
        Target width of the image.
    height : int or str
        Target height of the image.
    format : str, optional
        Image format (jpg, png, etc.). Defaults to `"jpg"`.
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
    new_url = url.replace("{w}", str(width))
    new_url = new_url.replace("{h}", str(height))
    new_url = new_url.replace("{c}", crop_option)
    new_url = new_url.replace("{f}", format)
    return new_url

def convert_album_to_song_url(album_url):
    """
    Convert an Apple Music album-track URL into a direct Apple Music song URL.

    Parameters
    ----------
    album_url : str
        Full Apple Music album URL that contains a track ID via the query parameter `?i=...`.

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
    parsed = urllib.parse.urlparse(album_url)
    query_params = urllib.parse.parse_qs(parsed.query)
    song_id = query_params.get('i', [None])[0]

    if not song_id:
        return None

    parts = parsed.path.split('/')
    country = parts[1]
    title = parts[3]

    return f"https://music.apple.com/{country}/song/{title}/{song_id}"

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
    url = url+"/see-all?section=singles"
    
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.find('script', {'id': 'serialized-server-data'})
    our_json = json.loads(items.text)
    
    sections = our_json[0]['data']['sections'][0]['items']
        
    for i in sections:
        result.append((i['segue']['actionMetrics']['data'][0]['fields']['actionUrl']))
    
    return result