import pytest
from resources.lib.matcher import parse_release_tokens, calculate_match_score, rank_subtitles, sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("Gladiator.II.2024.2160p.mkv") == "Gladiator.II.2024.2160p"
    assert sanitize_filename("/path/to/Dune.Part.Two.2024.mp4") == "Dune.Part.Two.2024"
    assert sanitize_filename("") == ""


def test_parse_release_tokens():
    tokens = parse_release_tokens("Movie Title 2024 2160p UHD BluRay x265 Atmos-FLUX.mkv")
    assert tokens["release_group"] == "flux"
    assert tokens["resolution"] == "2160p"
    assert tokens["source"] == "bluray"
    assert tokens["is_bluray"] is True
    assert tokens["video_codec"] == "x265"
    assert tokens["audio_codec"] == "atmos"

    web_tokens = parse_release_tokens("TV Show S01E01 1080p NF WEB-DL DDP5.1 x264-NTb.mkv")
    assert web_tokens["release_group"] == "ntb"
    assert web_tokens["resolution"] == "1080p"
    assert web_tokens["source"] == "web"
    assert web_tokens["is_web"] is True
    assert web_tokens["streaming_service"] == "nf"
    assert web_tokens["video_codec"] == "x264"
    assert web_tokens["audio_codec"] == "ddp"

    cam_tokens = parse_release_tokens("Sample Movie 2024 HDCAM x264.avi")
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
    video_file = "Dune Part Two 2024 2160p UHD BluRay x265-Framestor.mkv"
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
    assert ranked[0]["_match_score"] > ranked[1]["_match_score"]
    assert ranked[1]["id"] == "web"
    assert ranked[2]["id"] == "cam"


def test_edition_mismatch_penalty():
    video_file = "Kingdom of Heaven 2005 Extended Directors Cut 1080p BluRay x264.mkv"
    
    sub_extended = {
        "id": "ext",
        "attributes": {
            "release": "Kingdom of Heaven 2005 Extended Directors Cut 1080p BluRay",
            "download_count": 1000
        }
    }
    
    sub_theatrical = {
        "id": "theat",
        "attributes": {
            "release": "Kingdom of Heaven 2005 Theatrical Cut 1080p BluRay",
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


def test_legacy_ranking_with_preferred_languages_grouping():
    # Subtitles across English and Czech
    en_low = {"id": "en_low", "attributes": {"language": "en", "download_count": 10}}
    en_high = {"id": "en_high", "attributes": {"language": "en", "download_count": 500}}
    cs_low = {"id": "cs_low", "attributes": {"language": "cs", "download_count": 5}}
    cs_high = {"id": "cs_high", "attributes": {"language": "cs", "download_count": 300}}

    all_subs = [en_low, cs_high, en_high, cs_low]

    # When smart_ranking is False, should group Czech first (cs_high, cs_low), then English (en_high, en_low)
    ranked = rank_subtitles(all_subs, "Some.Movie.2024.mkv", smart_ranking=False, preferred_languages=["cs", "en"])
    assert [s["id"] for s in ranked] == ["cs_high", "cs_low", "en_high", "en_low"]


def test_get_match_display_tag():
    from resources.lib.matcher import get_match_display_tag

    # Exact moviehash match returns empty tag string since Kodi renders the native SYNC icon
    sub_hash = {"attributes": {"moviehash_match": True}}
    assert get_match_display_tag(sub_hash) == ""

    sub_high = {"_match_score": 6000.0, "attributes": {}}
    assert get_match_display_tag(sub_high) == "[COLOR yellow](+99)[/COLOR]"

    sub_med = {"_match_score": 1200.0, "attributes": {}}
    assert get_match_display_tag(sub_med) == "[COLOR yellow](+64)[/COLOR]"

    sub_low = {"_match_score": 50.0, "attributes": {}}
    assert get_match_display_tag(sub_low) == "[COLOR yellow](+5)[/COLOR]"

    sub_zero = {"_match_score": 0.0, "attributes": {}}
    assert get_match_display_tag(sub_zero) == ""


def test_multi_language_top_picks_and_grouping():
    video_file = "Movie 2024 1080p BluRay x264-FLUX.mkv"

    # Czech subtitles
    cs_top = {"id": "cs_top", "attributes": {"language": "cs", "release": "Movie 2024 1080p BluRay x264-FLUX"}}
    cs_mid = {"id": "cs_mid", "attributes": {"language": "cs", "release": "Movie 2024 1080p WEB-DL x264"}}
    cs_low = {"id": "cs_low", "attributes": {"language": "cs", "release": "Movie 2024 CAMRip x264"}}

    # English subtitles
    en_top = {"id": "en_top", "attributes": {"language": "en", "release": "Movie 2024 1080p BluRay x264-FLUX"}}
    en_mid = {"id": "en_mid", "attributes": {"language": "en", "release": "Movie 2024 1080p WEB-DL x264"}}
    en_low = {"id": "en_low", "attributes": {"language": "en", "release": "Movie 2024 CAMRip x264"}}

    all_subs = [en_low, cs_low, en_mid, cs_top, cs_mid, en_top]

    # User preferred languages: 1st Czech, 2nd English
    ranked = rank_subtitles(all_subs, video_file, smart_ranking=True, preferred_languages=["cs", "en"])

    # Expected order:
    # 1. cs_top (#1 match for Czech)
    # 2. en_top (#1 match for English)
    # 3. cs_mid (remaining Czech best)
    # 4. cs_low (remaining Czech worst)
    # 5. en_mid (remaining English best)
    # 6. en_low (remaining English worst)
    expected_ids = ["cs_top", "en_top", "cs_mid", "cs_low", "en_mid", "en_low"]
    actual_ids = [s["id"] for s in ranked]

    assert actual_ids == expected_ids


def _provenance_sub(sub_id, release, ai=False, machine=False):
    return {"id": sub_id, "attributes": {
        "language": "es", "release": release, "ratings": 0.0, "votes": 0,
        "download_count": 100, "from_trusted": False, "moviehash_match": False,
        "hearing_impaired": False, "ai_translated": ai, "machine_translated": machine,
        "foreign_parts_only": False, "files": [{"file_id": 1}],
        "feature_details": {"title": "Obsession", "movie_name": "Obsession"}}}


def test_human_translation_outranks_ai_with_better_filename_match():
    """Regression: exact-release AI subtitle topped the list over real translations."""
    video = "Obsession.2025.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264-BYNDR.mp4"
    ai_exact = _provenance_sub("ai", "Obsession.2025.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264", ai=True)
    human_close = _provenance_sub("human", "Obsession.2025.1080p.WEB-DL")

    ranked = rank_subtitles([ai_exact, human_close], video, preferred_languages=["es"])

    assert ranked[0]["id"] == "human", \
        f"human should win: human={human_close['_match_score']}, ai={ai_exact['_match_score']}"


def test_provenance_order_human_then_ai_then_machine_on_equal_releases():
    video = "Obsession.2025.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264-BYNDR.mp4"
    release = "Obsession.2025.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264"
    human = _provenance_sub("human", release)
    ai = _provenance_sub("ai", release, ai=True)
    machine = _provenance_sub("machine", release, machine=True)

    ranked = rank_subtitles([machine, ai, human], video, preferred_languages=["es"])

    assert [s["id"] for s in ranked] == ["human", "ai", "machine"]


def test_ai_penalty_does_not_resurrect_cam_desync_garbage():
    """AI for the right release must still beat a human CAM rip subtitle."""
    video = "Obsession.2025.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264-BYNDR.mp4"
    ai_exact = _provenance_sub("ai", "Obsession.2025.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264", ai=True)
    human_cam = _provenance_sub("human_cam", "Obsession.2025.CAM.XviD")

    ranked = rank_subtitles([human_cam, ai_exact], video, preferred_languages=["es"])

    assert ranked[0]["id"] == "ai"


def test_on_demand_detection_via_comment_marker():
    from resources.lib.matcher import is_on_demand_translation
    assert is_on_demand_translation({
        "comments": "This subtitle file will be created on demand in czech language as AI translation from polish language.",
        "files": [{"file_id": 11827675}]})


def test_on_demand_detection_via_synthetic_file_id():
    from resources.lib.matcher import is_on_demand_translation
    assert is_on_demand_translation({
        "comments": "", "files": [{"file_id": "1246448409911500000000000000000000"}]})


def test_real_uploaded_ai_subtitle_is_not_on_demand():
    from resources.lib.matcher import is_on_demand_translation
    assert not is_on_demand_translation({
        "comments": "retail subs compatible with WEB-DL", "ai_translated": True,
        "files": [{"file_id": 11827675}]})
    assert not is_on_demand_translation({"comments": "", "files": []})


def test_episode_subtitle_sinks_when_target_is_a_movie():
    """Live catalog mislink: TV episode subs attached to the 1971 movie feature."""
    video = "The.Andromeda.Strain.1971.mp4"
    episode_sub = _provenance_sub("episode", "Andromeda - [1x07] - The Ties That Blind")
    movie_sub = _provenance_sub("movie", "The Andromeda Strain 1971")

    ranked = rank_subtitles([episode_sub, movie_sub], video, preferred_languages=["es"])
    assert ranked[0]["id"] == "movie"


def test_episode_subtitle_not_penalized_when_target_is_an_episode():
    from resources.lib.matcher import calculate_match_score
    sub = _provenance_sub("ep", "Show.S04E01.1080p.WEB.H264-GROUP")
    score_for_episode = calculate_match_score(sub, "Show.S04E01.1080p.WEB.mkv")
    sub2 = _provenance_sub("ep2", "Show.S04E01.1080p.WEB.H264-GROUP")
    score_for_movie = calculate_match_score(sub2, "Some.Movie.2024.1080p.mkv")
    assert score_for_episode > score_for_movie


def test_rank_drops_non_object_entries_and_keeps_ranking():
    """A non-object entry in the result list must be dropped, not allowed to
    re-raise inside the score-failure handler and disable ranking for the
    whole page."""
    from resources.lib.matcher import rank_subtitles

    good = {"id": "1", "attributes": {"language": "en",
                                      "release": "Movie.2024.1080p.BluRay.x264-GRP",
                                      "files": [{"file_name": "Movie.2024.1080p.BluRay.x264-GRP.srt"}]}}
    ranked = rank_subtitles([None, "junk", 42, good],
                            video_filename="Movie.2024.1080p.BluRay.x264-GRP.mkv",
                            guessit_data=None, preferred_languages=["en"],
                            smart_ranking=True)
    assert ranked == [good] or (len(ranked) == 1 and ranked[0]["id"] == "1")
