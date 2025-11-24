from bs4 import BeautifulSoup
import requests
import json
from utils import convert_album_to_song_url, get_cover
from utils import safe_action_url, find_section, append_urls_from_section


def room_scrape(link="https://music.apple.com/us/room/6748797380"):
    """
    Scrape a shared Apple Music room and extract song URLs.

    Parameters
    ----------
    link : str, optional
        URL of the Apple Music room page. Defaults to an example room link.

    Returns
    -------
    list[str]
        List of converted song URLs extracted from the room.

    Notes
    -----
    This function parses the `serialized-server-data` script tag within
    the Apple Music room HTML, locates the 'copper-track-swoosh' section,
    and extracts track URLs.
    """
    result = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        rspn = requests.get(link, headers=headers, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    items_tag = soup.find("script", {"id": "serialized-server-data"})
    if not items_tag:
        return result

    try:
        data = json.loads(items_tag.text)
        sections = data[0]["data"]["sections"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    items = []
    for section in sections:
        if "copper-track-swoosh" in section.get("id", ""):
            items = section.get("items", [])
            break

    for item in items:
        try:
            action_url = (
                item["playAction"]["actionMetrics"]
                ["data"][0]["fields"]["actionUrl"]
            )
            song_url = convert_album_to_song_url(action_url)
            if song_url:
                result.append(song_url)
        except (KeyError, IndexError, TypeError):
            continue

    return result


def playlist_scrape(
    link=(
        "https://music.apple.com/us/playlist"
        "/new-music-daily/pl.2b0e6e332fdf4b7a91164da3162127b5"
    ),
):
    """
    Scrape an Apple Music playlist and extract all track URLs.

    Parameters
    ----------
    link : str, optional
        URL of the Apple Music playlist. Defaults to New Music Daily.

    Returns
    -------
    list[str]
        List of converted song URLs from the playlist.

    Notes
    -----
    Uses the 'track-list' section from Apple Music's internal serialized
    server data to extract song action URLs.
    """
    result = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        rspn = requests.get(link, headers=headers, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    items_tag = soup.find("script", {"id": "serialized-server-data"})
    if not items_tag:
        return result

    try:
        data = json.loads(items_tag.text)
        sections = data[0]["data"]["sections"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    items = []
    for section in sections:
        if "track-list" in section.get("id", ""):
            items = section.get("items", [])
            break

    for item in items:
        try:
            action_url = (
                item["playAction"]["actionMetrics"]
                ["data"][0]["fields"]["actionUrl"]
            )
            song_url = convert_album_to_song_url(action_url)
            if song_url:
                result.append(song_url)
        except (KeyError, IndexError, TypeError):
            continue

    return result


def search(keyword="sasha sloan"):
    """
    Search Apple Music for artists, songs, albums, playlists and videos.

    Parameters
    ----------
    keyword : str, optional
        Search query to send to Apple Music. Defaults to "sasha sloan".

    Returns
    -------
    dict
        Structured JSON-like dictionary containing search results:
        - artists
        - albums
        - songs
        - playlists
        - videos

    Notes
    -----
    Scrapes `serialized-server-data` to access Apple Music's internal search structure.
    """
    result = {"artists": [], "albums": [], "songs": [], "playlists": [], "videos": []}
    link = f"https://music.apple.com/us/search?term={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        rspn = requests.get(link, headers=headers, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    tag = soup.find("script", {"id": "serialized-server-data"})
    if not tag:
        return result

    try:
        data = json.loads(tag.text)
        sections = data[0]["data"]["sections"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    artists = {"items": []}
    albums = {"items": []}
    songs_block = {"items": []}
    playlists = {"items": []}
    videos = {"items": []}

    for sec in sections:
        sec_id = sec.get("id", "")
        if "artist" in sec_id:
            artists = sec
        elif "album" in sec_id:
            albums = sec
        elif "song" in sec_id:
            songs_block = sec
        elif "playlist" in sec_id:
            playlists = sec
        elif "music_video" in sec_id:
            videos = sec

    # Artists
    for item in artists.get("items", []):
        try:
            url = item["contentDescriptor"]["url"]
            title = item.get("title", "")
            artwork_dict = item.get("artwork", {}).get("dictionary", {})
            img = get_cover(
                artwork_dict.get("url", ""),
                artwork_dict.get("width", 0),
                artwork_dict.get("height", 0),
            )
            result["artists"].append({"title": title, "url": url, "image": img})
        except (KeyError, TypeError):
            continue

    # Albums
    for item in albums.get("items", []):
        try:
            url = item["contentDescriptor"]["url"]
            title = item["titleLinks"][0]["title"]
            artist = item["subtitleLinks"][0]["title"]
            artwork_dict = item.get("artwork", {}).get("dictionary", {})
            img = get_cover(
                artwork_dict.get("url", ""),
                artwork_dict.get("width", 0),
                artwork_dict.get("height", 0),
            )
            result["albums"].append(
                {
                    "title": title,
                    "artist": artist,
                    "url": url,
                    "image": img
                }
            )
        except (KeyError, TypeError, IndexError):
            continue

    # Songs
    for item in songs_block.get("items", []):
        try:
            url = item["contentDescriptor"]["url"]
            title = item.get("title", "")
            artist = item["subtitleLinks"][0]["title"]
            artwork_dict = item.get("artwork", {}).get("dictionary", {})
            img = get_cover(
                artwork_dict.get("url", ""),
                artwork_dict.get("width", 0),
                artwork_dict.get("height", 0),
            )
            result["songs"].append(
                {
                    "title": title,
                    "artist": artist,
                    "url": url,
                    "image": img
                }
            )
        except (KeyError, TypeError, IndexError):
            continue

    # Playlists
    for item in playlists.get("items", []):
        try:
            url = item["contentDescriptor"]["url"]
            title = item["titleLinks"][0]["title"]
            artist = item["subtitleLinks"][0]["title"]
            artwork_dict = item.get("artwork", {}).get("dictionary", {})
            img = get_cover(
                artwork_dict.get("url", ""),
                artwork_dict.get("width", 0),
                artwork_dict.get("height", 0),
            )
            result["playlists"].append(
                {
                    "title": title,
                    "artist": artist,
                    "url": url,
                    "image": img
                }
            )
        except (KeyError, TypeError, IndexError):
            continue

    # Videos
    for item in videos.get("items", []):
        try:
            url = item["contentDescriptor"]["url"]
            title = item["titleLinks"][0]["title"]
            artist = item["subtitleLinks"][0]["title"]
            artwork_dict = item.get("artwork", {}).get("dictionary", {})
            img = get_cover(
                artwork_dict.get("url", ""),
                artwork_dict.get("width", 0),
                artwork_dict.get("height", 0),
            )
            result["videos"].append(
                {
                    "title": title,
                    "artist": artist,
                    "url": url,
                    "image": img
                }
            )
        except (KeyError, TypeError, IndexError):
            continue

    return result


def song_scrape(url="https://music.apple.com/us/song/california/1821538031"):
    """
    Scrape a single Apple Music song page and extract metadata.

    Parameters
    ----------
    url : str, optional
        URL of the Apple Music song. Defaults to sample link.

    Returns
    -------
    dict
        Dictionary containing:
        - title
        - image (full resolution)
        - kind (song type)
        - album info (title + URL)
        - artist info (title + URL)
        - preview-url
        - list of more songs

    Notes
    -----
    Uses the `schema:song` JSON-LD tag to extract preview URL.
    """
    result = {
        "title": "",
        "image": "",
        "kind": "",
        "album": {"title": "", "url": ""},
        "artist": {"title": "", "url": ""},
        "more": [],
        "preview-url": "",
    }

    try:
        rspn = requests.get(url, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    tag = soup.find("script", {"id": "serialized-server-data"})
    if not tag:
        return result

    try:
        data = json.loads(tag.text)
        sections = data[0]["data"]["sections"]
        details = sections[0]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    try:
        item = details["items"][0]
        artwork_dict = item.get("artwork", {}).get("dictionary", {})
    except (KeyError, IndexError, TypeError):
        return result

    result["title"] = item.get("title", "")

    result["image"] = get_cover(
        artwork_dict.get("url", ""),
        artwork_dict.get("width", 0),
        artwork_dict.get("height", 0),
    )

    result["kind"] = details.get("presentation", {}).get("kind", "")
    result["album"]["title"] = item.get("album", "")

    try:
        result["album"]["url"] = (
            item["albumLinks"][0]["segue"]["actionMetrics"]
            ["data"][0]["fields"]["actionUrl"]
        )
    except (KeyError, IndexError, TypeError):
        pass

    result["artist"]["title"] = item.get("artists", "")

    try:
        result["artist"]["url"] = (
            item["artistLinks"][0]["segue"]["actionMetrics"]
            ["data"][0]["fields"]["actionUrl"]
        )
    except (KeyError, IndexError, TypeError):
        pass

    try:
        json_tag = soup.find(
            "script",
            {
                "id": "schema:song",
                "type": "application/ld+json"
            }
        )
        schema_data = json.loads(json_tag.string)
        result["preview-url"] = schema_data["audio"]["audio"]["contentUrl"]
    except (AttributeError, KeyError, TypeError, json.JSONDecodeError):
        result["preview-url"] = ""

    try:
        more_items = sections[-1]["items"]
        for m in more_items:
            url = safe_action_url(m)
            if url:
                result["more"].append(url)
    except (KeyError, IndexError, TypeError):
        pass

    return result


def album_scrape(url="https://music.apple.com/us/album/1965/1817707266?i=1817707585"):
    """
    Scrape an Apple Music album page
    and extract metadata, songs, related albums, videos, etc.

    Parameters
    ----------
    url : str, optional
        URL of the Apple Music album. Defaults to example album.

    Returns
    -------
    dict
        Dictionary containing:
        - title
        - image
        - caption/description
        - artist info
        - song URLs
        - album info text
        - more songs (same artist)
        - similar (recommended) albums
        - videos related to the album

    Notes
    -----
    Extracts multiple sections such as:
    - album-detail
    - track-list
    - similar albums
    - more by artist
    - album videos
    """
    result = {
        "title": "",
        "image": "",
        "caption": "",
        "artist": {"title": "", "url": ""},
        "songs": [],
        "info": "",
        "more": [],
        "similar": [],
        "videos": [],
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        rspn = requests.get(url, headers=headers, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    tag = soup.find("script", {"id": "serialized-server-data"})
    if not tag:
        return result

    try:
        data = json.loads(tag.text)
        sections = data[0]["data"]["sections"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    album_detail_index = None
    track_list_index = None
    video_index = None
    more_index = None
    similar_index = None
    track_list_section_index = None

    for idx, sec in enumerate(sections):
        sec_id = sec.get("id", "")
        if "album-detail" in sec_id:
            album_detail_index = idx
        elif "track-list " in sec_id:
            track_list_index = idx
        elif "video" in sec_id:
            video_index = idx
        elif "more" in sec_id:
            more_index = idx
        elif "you-might-also-like" in sec_id:
            similar_index = idx
        elif "track-list-section" in sec_id:
            track_list_section_index = idx

    # TITLE
    try:
        item = sections[album_detail_index]["items"][0]
        result["title"] = item.get("title", "")
    except Exception:
        pass

    # IMAGE
    try:
        artwork = item.get("artwork", {}).get("dictionary", {})
        result["image"] = get_cover(
            artwork.get("url", ""),
            artwork.get("width", 0),
            artwork.get("height", 0),
        )
    except Exception:
        pass

    # CAPTION
    try:
        result["caption"] = item.get(
            "modalPresentationDescriptor",
            {}
        ).get("paragraphText", "")
    except Exception:
        pass

    # ARTIST
    try:
        sl = item.get("subtitleLinks", [])[0]
        result["artist"]["title"] = sl.get("title", "")
        result["artist"]["url"] = (
            sl["segue"]["actionMetrics"]
            ["data"][0]["fields"]["actionUrl"]
        )
    except Exception:
        pass

    # SONG LIST
    try:
        track_items = sections[track_list_index].get("items", [])
        for it in track_items:
            try:
                url = it["contentDescriptor"]["url"]
                song_url = convert_album_to_song_url(url)
                if song_url:
                    result["songs"].append(song_url)
            except Exception:
                continue
    except Exception:
        pass

    # INFO + MORE SONGS
    try:
        desc_item = sections[track_list_section_index]["items"][0]
        result["info"] = desc_item.get("description", "")

        more_items = sections[more_index].get("items", [])
        for m in more_items:
            url = safe_action_url(m)
            if url:
                result["more"].append(url)
    except Exception:
        pass

    # SIMILAR
    try:
        sim_items = sections[similar_index].get("items", [])
        for s in sim_items:
            url = safe_action_url(s)
            if url:
                result["similar"].append(url)
    except Exception:
        pass

    # VIDEOS
    try:
        vid_items = sections[video_index].get("items", [])
        for v in vid_items:
            try:
                url = v["contentDescriptor"]["url"]
                result["videos"].append(url)
            except Exception:
                continue
    except Exception:
        pass

    return result


def video_scrape(
    url=(
        "https://music.apple.com/us/music-video/"
        "gucci-mane-visualizer/1810547026"
    ),
):
    """
    Scrape Apple Music music-video page and extract metadata + video file URL.

    Parameters
    ----------
    url : str, optional
        URL of the Apple Music music-video. Defaults to example.

    Returns
    -------
    dict
        {
            title,
            image,
            artist: {title, url},
            video-url,
            more (same artist),
            similar (same genre)
        }

    Notes
    -----
    Uses JSON-LD block `schema:music-video` to extract the direct video content URL.
    """
    result = {
        "title": "",
        "image": "",
        "artist": {"title": "", "url": ""},
        "video-url": "",
        "more": [],
        "similar": [],
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        rspn = requests.get(url, headers=headers, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    tag = soup.find("script", {"id": "serialized-server-data"})
    if not tag:
        return result

    try:
        data = json.loads(tag.text)
        sections = data[0]["data"]["sections"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    music_video_header = None
    more = None
    similar = None

    for sec in sections:
        sec_id = sec.get("id", "")
        if "music-video-header" in sec_id:
            music_video_header = sec
        elif "more-by-artist" in sec_id:
            more = sec
        elif "more-in-genre" in sec_id:
            similar = sec

    # TITLE
    item = (music_video_header or {}).get("items", [{}])[0]
    result["title"] = item.get("title", "")

    # IMAGE
    try:
        artwork = item.get("artwork", {}).get("dictionary", {})
        result["image"] = get_cover(
            artwork.get("url", ""),
            artwork.get("width", 0),
            artwork.get("height", 0),
        )
    except Exception:
        pass

    # ARTIST
    try:
        sl = item.get("subtitleLinks", [])[0]
        result["artist"]["title"] = sl.get("title", "")
        result["artist"]["url"] = (
            sl["segue"]["actionMetrics"]
            ["data"][0]["fields"]["actionUrl"]
        )
    except Exception:
        pass

    # VIDEO URL
    try:
        json_tag = soup.find(
            "script",
            {
                "id": "schema:music-video",
                "type": "application/ld+json"
            }
        )
        schema_data = json.loads(json_tag.string)
        result["video-url"] = schema_data["video"]["contentUrl"]
    except (AttributeError, KeyError, TypeError, json.JSONDecodeError):
        pass

    # MORE BY ARTIST
    try:
        for m in more.get("items", []):
            url = safe_action_url(m)
            if url:
                result["more"].append(url)
    except Exception:
        pass

    # SIMILAR
    try:
        for s in similar.get("items", []):
            url = safe_action_url(s)
            if url:
                result["similar"].append(url)
    except Exception:
        pass

    return result


def artist_scrape(url="https://music.apple.com/us/artist/king-princess/1349968534"):
    """
    Scrape an Apple Music artist page and extract all available metadata.

    Parameters
    ----------
    url : str, optional
        Apple Music artist page URL. Defaults to King Princess sample link.

    Returns
    -------
    dict
        Dictionary containing:
        - title
        - image
        - latest release URL
        - list of top songs
        - all albums
        - singles & EPs
        - playlists
        - videos
        - similar artists
        - appears on
        - more-to-see (videos)
        - more-to-hear (songs)
        - about text
        - extra info (bio subtitle)

    Notes
    -----
    This is the most complex scraper and extracts ~12 different sections
    from the artist page.
    """
    result = {
        "title": "",
        "image": "",
        "latest": "",
        "top": [],
        "albums": [],
        "singles_and_EP": [],
        "playlists": [],
        "videos": [],
        "similar": [],
        "appears_on": [],
        "more_to_see": [],
        "more_to_hear": [],
        "about": "",
        "info": "",
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        rspn = requests.get(url, headers=headers, timeout=10)
        rspn.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(rspn.text, "html.parser")
    tag = soup.find("script", {"id": "serialized-server-data"})
    if not tag:
        return result

    try:
        data = json.loads(tag.text)
        sections = data[0]["data"]["sections"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return result

    artist_detail = find_section(sections, "artist-detail-header-section")
    latest_and_top = find_section(sections, "latest-release-and-top-songs")
    albums = find_section(sections, "full-albums")
    playlists = find_section(sections, "playlists")
    videos = find_section(sections, "music-videos")
    appears_on = find_section(sections, "appears-on")
    more_to_see = find_section(sections, "more-to-see")
    more_to_hear = find_section(sections, "more-to-hear")
    bio = find_section(sections, "artist-bio")
    similar = find_section(sections, "similar-artists")

    # HEADER
    try:
        item = artist_detail["items"][0]
        result["title"] = item.get("title", "")
        artwork = item.get("artwork", {}).get("dictionary", {})
        result["image"] = get_cover(
            artwork.get("url", ""),
            artwork.get("width", 0),
            artwork.get("height", 0),
        )
    except Exception:
        pass

    # LATEST
    try:
        result["latest"] = (
            latest_and_top["pinnedLeadingItem"]["item"]["segue"]
            ["actionMetrics"]["data"][0]["fields"]["actionUrl"]
        )
    except Exception:
        pass

    # TOP SONGS
    append_urls_from_section(latest_and_top, result["top"])

    # ALBUMS
    append_urls_from_section(albums, result["albums"])

    # PLAYLISTS
    append_urls_from_section(playlists, result["playlists"])

    # VIDEOS
    append_urls_from_section(videos, result["videos"])

    # SIMILAR
    append_urls_from_section(similar, result["similar"])

    # APPEARS ON
    append_urls_from_section(appears_on, result["appears_on"])

    # MORE TO SEE
    append_urls_from_section(more_to_see, result["more_to_see"])

    # MORE TO HEAR
    append_urls_from_section(more_to_hear, result["more_to_hear"])

    # ABOUT
    try:
        item = bio["items"][0]
        mpd = item.get("modalPresentationDescriptor", {})
        result["about"] = mpd.get("paragraphText", "")
        result["info"] = mpd.get("headerSubtitle", "")
    except Exception:
        pass

    return result


def test_all_functions():
    """
    Run integration-style tests for all scraper functions.

    This function executes each scraper with sample inputs to verify that:
      - The function runs without raising exceptions.
      - The returned structures contain expected keys.
      - Basic counts (number of items, presence of preview/video URLs, etc.)
        match minimal sanity expectations.

    Tests performed:
      1. room_scrape()       – prints number of room items.
      2. playlist_scrape()   – prints number of playlist items.
      3. search()            – searches for "night tapes" and prints result counts.
      4. song_scrape()       – scrapes a sample Apple Music song URL.
      5. album_scrape()      – scrapes a sample Apple Music album URL.
      6. video_scrape()      – scrapes a sample Apple Music video URL.
      7. artist_scrape()     – scrapes a sample Apple Music artist page.

    This is not a formal unit test suite, but a quick manual verification tool
    intended to confirm scraper functionality during development.

    Prints:
      - Counts of returned items.
      - Key fields such as title, preview-url existence, etc.
    """
    print("\n=== TEST: room_scrape ===")
    try:
        r = room_scrape()
        print("Room items:", len(r))
    except Exception as e:
        print("room_scrape ERROR:", e)

    print("\n=== TEST: playlist_scrape ===")
    try:
        p = playlist_scrape()
        print("Playlist items:", len(p))
    except Exception as e:
        print("playlist_scrape ERROR:", e)

    print("\n=== TEST: search ===")
    try:
        s = search("night tapes")
        print("Artists:", len(s.get("artists", [])))
        print("Albums:", len(s.get("albums", [])))
        print("Songs:", len(s.get("songs", [])))
        print("Playlists:", len(s.get("playlists", [])))
        print("Videos:", len(s.get("videos", [])))
    except Exception as e:
        print("search ERROR:", e)

    print("\n=== TEST: song_scrape ===")
    try:
        song = song_scrape("https://music.apple.com/us/song/california/1821538031")
        print("Song title:", song.get("title"))
        print("Preview URL exists:", bool(song.get("preview-url")))
    except Exception as e:
        print("song_scrape ERROR:", e)

    print("\n=== TEST: album_scrape ===")
    try:
        album = album_scrape(
            "https://music.apple.com/us/album/1965/1817707266?i=1817707585"
        )
        print("Album title:", album.get("title"))
        print("Songs:", len(album.get("songs", [])))
    except Exception as e:
        print("album_scrape ERROR:", e)

    print("\n=== TEST: video_scrape ===")
    try:
        video = video_scrape(
            "https://music.apple.com/us/music-video/gucci-mane-visualizer/1810547026"
        )
        print("Video title:", video.get("title"))
        print("Video URL exists:", bool(video.get("video-url")))
    except Exception as e:
        print("video_scrape ERROR:", e)

    print("\n=== TEST: artist_scrape ===")
    try:
        artist = artist_scrape(
            "https://music.apple.com/us/artist/king-princess/1349968534"
        )
        print("Artist title:", artist.get("title"))
        print("Top songs:", len(artist.get("top", [])))
        print("Albums:", len(artist.get("albums", [])))
        print("Videos:", len(artist.get("videos", [])))
    except Exception as e:
        print("artist_scrape ERROR:", e)

    print("\n=== ALL TESTS COMPLETED ===")
