import pytest
from resources.lib.matcher import parse_release_tokens, calculate_match_score, rank_subtitles, sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("Gladiator.II.2024.2160p.mkv") == "Gladiator.II.2024.2160p"
    assert sanitize_filename("/path/to/Dune.Part.Two.2024.mp4") == "Dune.Part.Two.2024"
    assert sanitize_filename("") == ""


def test_parse_release_tokens():
    tokens = parse_release_tokens("Gladiator.II.2024.2160p.UHD.BluRay.x265.TrueHD.Atmos.7.1-FLUX.mkv")
    assert tokens["release_group"] == "flux"
    assert tokens["resolution"] == "2160p"
    assert tokens["source"] == "bluray"
    assert tokens["is_bluray"] is True
    assert tokens["video_codec"] == "x265"
    assert tokens["audio_codec"] == "atmos"

    web_tokens = parse_release_tokens("Breaking.Bad.S05E14.1080p.NF.WEB-DL.DDP5.1.x264-NTb.mkv")
    assert web_tokens["release_group"] == "ntb"
    assert web_tokens["resolution"] == "1080p"
    assert web_tokens["source"] == "web"
    assert web_tokens["is_web"] is True
    assert web_tokens["streaming_service"] == "nf"
    assert web_tokens["video_codec"] == "x264"
    assert web_tokens["audio_codec"] == "ddp"

    cam_tokens = parse_release_tokens("Avatar.2.2022.HDCAM.x264-CINEV.avi")
    assert cam_tokens["is_cam"] is True
    assert cam_tokens["source"] == "cam"


def test_match_score_moviehash_priority():
    sub_hash = {
        "attributes": {
            "moviehash_match": True,
            "release": "Random.Release.Name",
            "ratings": 5.0,
            "download_count": 100
        }
    }
    sub_unmatched = {
        "attributes": {
            "moviehash_match": False,
            "release": "Random.Release.Name",
            "ratings": 10.0,
            "download_count": 50000
        }
    }

    score_hash = calculate_match_score(sub_hash, "My.Movie.2024.1080p.mkv")
    score_unmatched = calculate_match_score(sub_unmatched, "My.Movie.2024.1080p.mkv")

    assert score_hash > score_unmatched
    assert sub_hash["_is_sync"] is True


def test_rank_subtitles_orders_exact_release_first():
    video_file = "Dune.Part.Two.2024.2160p.UHD.BluRay.x265-Framestor.mkv"
    guessit_meta = {
        "title": "Dune Part Two",
        "year": 2024,
        "release_group": "Framestor",
        "source": "BluRay",
        "screen_size": "2160p",
        "video_codec": "x265"
    }

    sub_exact = {
        "id": "exact",
        "attributes": {
            "release": "Dune Part Two 2024 2160p UHD BluRay x265-Framestor",
            "ratings": 8.0,
            "download_count": 500,
            "from_trusted": True
        }
    }

    sub_web = {
        "id": "web",
        "attributes": {
            "release": "Dune Part Two 2024 1080p WEB-DL x264-EVO",
            "ratings": 9.0,
            "download_count": 50000,
            "from_trusted": True
        }
    }

    sub_cam = {
        "id": "cam",
        "attributes": {
            "release": "Dune Part Two 2024 CAMRip x264",
            "ratings": 4.0,
            "download_count": 80000
        }
    }

    subtitles = [sub_cam, sub_web, sub_exact]
    ranked = rank_subtitles(subtitles, video_file, guessit_meta, smart_ranking=True)

    # Exact BluRay Framestor match must rank FIRST despite having fewer downloads than older WEB/CAM subs
    assert ranked[0]["id"] == "exact"
    assert ranked[0]["_is_sync"] is True
    assert ranked[1]["id"] == "web"
    assert ranked[2]["id"] == "cam"


def test_edition_mismatch_penalty():
    video_file = "Kingdom.of.Heaven.2005.Extended.Director's.Cut.1080p.BluRay.x264.mkv"
    
    sub_extended = {
        "id": "ext",
        "attributes": {
            "release": "Kingdom.of.Heaven.2005.Extended.Directors.Cut.1080p.BluRay",
            "download_count": 1000
        }
    }
    
    sub_theatrical = {
        "id": "theat",
        "attributes": {
            "release": "Kingdom.of.Heaven.2005.Theatrical.Cut.1080p.BluRay",
            "download_count": 10000
        }
    }

    ranked = rank_subtitles([sub_theatrical, sub_extended], video_file, smart_ranking=True)
    assert ranked[0]["id"] == "ext"


def test_legacy_ranking_fallback_when_disabled():
    sub_low = {"id": "low", "attributes": {"download_count": 10}}
    sub_high = {"id": "high", "attributes": {"download_count": 1000}}

    ranked = rank_subtitles([sub_low, sub_high], "Some.Movie.2024.mkv", smart_ranking=False)
    assert ranked[0]["id"] == "high"
