"""One malformed API entry must not cost the user every other subtitle.

`rank_subtitles()` itself is non-lossy - it reorders, never filters. The risk is an
*exception*: before v1.0.16 a single unexpected field type (e.g. a non-string `release`,
which raises TypeError inside the release-token parser) propagated out of
`SubtitleDownloader.list_subtitles()`. That lost every result AND skipped the closing
`endOfDirectory()`, leaving Kodi's subtitle dialog hanging with nothing in it.

The existing matcher tests all assert ordering, so none of them noticed.
"""
import pytest

from resources.lib.matcher import rank_subtitles

VIDEO = "Show.S01E01.1080p.WEB.h264-GRP.mkv"


def _sub(sub_id, **overrides):
    attributes = {
        "language": "en",
        "release": "Show.S01E01.1080p.WEB.h264-GRP",
        "ratings": 8.0,
        "download_count": 10,
        "from_trusted": True,
        "hearing_impaired": False,
        "moviehash_match": False,
        "files": [{"file_id": sub_id}],
        "feature_details": {"title": "Show", "movie_name": "Show"},
    }
    attributes.update(overrides)
    return {"id": str(sub_id), "attributes": attributes}


MALFORMED = [
    pytest.param({"release": 12345}, id="release-is-a-number"),
    pytest.param({"release": None}, id="release-is-None"),
    pytest.param({"language": None}, id="language-is-None"),
    pytest.param({"ratings": None}, id="ratings-is-None"),
    pytest.param({"download_count": None}, id="download_count-is-None"),
]


def test_rank_subtitles_returns_every_subtitle():
    """Ranking reorders; it must never drop, cap or dedupe results."""
    subs = [_sub(i, language=lang) for i, lang in enumerate(["en", "fr", "en", "de", "fr"])]
    ranked = rank_subtitles(subs, VIDEO, preferred_languages=["fr", "en"])
    assert len(ranked) == len(subs)
    assert {id(s) for s in ranked} == {id(s) for s in subs}


def test_single_poor_scoring_subtitle_is_still_returned():
    """A lone bad match is still the only thing the user has - show it."""
    sub = _sub(1, release="Something.Completely.Different.CAM.xvid")
    assert rank_subtitles([sub], VIDEO, preferred_languages=["en"]) == [sub]


@pytest.mark.parametrize("bad_attributes", MALFORMED)
def test_one_malformed_entry_does_not_lose_the_others(bad_attributes):
    """Whether scoring copes or raises, the caller must still get the good entries."""
    good_a, good_b = _sub(1), _sub(2)
    bad = _sub(99, **bad_attributes)

    try:
        ranked = rank_subtitles([good_a, bad, good_b], VIDEO, preferred_languages=["en"])
    except Exception as e:
        # list_subtitles() catches this and falls back to the unranked order, so nothing is
        # lost in production - but the scorer should tolerate it outright rather than
        # relying on that safety net.
        pytest.fail(
            f"rank_subtitles() raised {e!r} on a malformed entry. list_subtitles() now "
            f"catches it, but harden the scorer instead of depending on the fallback."
        )

    assert good_a in ranked and good_b in ranked, "a malformed entry took good results with it"
    assert len(ranked) == 3, "entries must be reordered, never dropped"
