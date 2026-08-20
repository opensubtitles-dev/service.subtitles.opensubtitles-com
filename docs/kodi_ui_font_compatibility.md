# Kodi UI Font, Glyph & Formatting Compatibility Reference

This document records the verified rendering compatibility for subtitle list items in Kodi skins (Estuary, default TTF fonts like Roboto / Arial).

---

## 1. ✅ Verified & Fully Supported

### A. Kodi Text Formatting Tags
* **Colors**:
  * Named colors: `[COLOR green]...[/COLOR]`, `[COLOR cyan]...[/COLOR]`, `[COLOR orange]...[/COLOR]`, `[COLOR yellow]...[/COLOR]`, `[COLOR gold]...[/COLOR]`, `[COLOR red]...[/COLOR]`, `[COLOR lightblue]...[/COLOR]`, `[COLOR grey]...[/COLOR]`, `[COLOR white]...[/COLOR]`.
  * Hex ARGB codes: `[COLOR FF00FFCC]...[/COLOR]`, `[COLOR FFFFD700]...[/COLOR]`.
* **Typography**:
  * Bold: `[B]Text[/B]`
  * Italic: `[I]Text[/I]`

### B. International Character Sets & Diacritics
* **Czech & Slovak**: `ľ`, `š`, `č`, `ť`, `ž`, `ý`, `á`, `í`, `é`, `ô`, `ä`, `ň`, `ď`, `ĺ`, `ŕ`.
* **Cyrillic (Russian, Ukrainian, Bulgarian)**: `Русский перевод`, `Субтитры`, `Проверено`.
* **Western European**: German (`äöüß`), French (`éèêàç`), Spanish (`ñáíóú`), Polish (`ąęćłńóśźż`).

### C. Standard Unicode BMP Glyphs
* **Stars & Ratings**: `★` (U+2605 Black Star), `☆` (U+2606 White Star).
* **Bullets & Separators**: `•` (U+2022 Bullet), `│` (U+2502 Pipe / Divider), `»` (U+00BB Angle quote).
* **Brackets**: `[...]`, `(...)`, `{...}`.

---

## 1b. 🔬 Glyph Test Matrix (measured in Kodi, `test_flag_interceptor` mock mode)

Observed on-screen in the subtitle selection dialog (Estuary skin, default Kodi fonts).
"Tofu" = rendered as an empty rectangle. Verified against the mock rows produced by
`_inject_test_flag_subtitles()` in `resources/lib/subtitle_downloader.py`.

### ✅ Renders (58 confirmed)

| Glyph | Codepoint | Name | Block | Good for |
| :--- | :--- | :--- | :--- | :--- |
| `√` | U+221A | Square Root | Mathematical Operators | tick / verified |
| `★` | U+2605 | Black Star | Misc Symbols | rating, top pick |
| `☆` | U+2606 | White Star | Misc Symbols | empty rating |
| `●` | U+25CF | Black Circle | Geometric Shapes | filled marker |
| `○` | U+25CB | White Circle | Geometric Shapes | empty marker |
| `■` | U+25A0 | Black Square | Geometric Shapes | badge / block |
| `▪` | U+25AA | Black Small Square | Geometric Shapes | compact bullet |
| `▫` | U+25AB | White Small Square | Geometric Shapes | compact bullet |
| `▬` | U+25AC | Black Rectangle | Geometric Shapes | bar segment |
| `▲` | U+25B2 | Black Up Triangle | Geometric Shapes | high / better |
| `▼` | U+25BC | Black Down Triangle | Geometric Shapes | low / worse |
| `►` | U+25BA | Black Right Pointer | Geometric Shapes | play / next |
| `◄` | U+25C4 | Black Left Pointer | Geometric Shapes | previous |
| `◘` | U+25D8 | Inverse Bullet | Geometric Shapes | strong marker |
| `◙` | U+25D9 | Inverse White Circle | Geometric Shapes | strong marker |
| `•` | U+2022 | Bullet | General Punctuation | list bullet |
| `←` | U+2190 | Leftwards Arrow | Arrows | direction |
| `↑` | U+2191 | Upwards Arrow | Arrows | increase |
| `→` | U+2192 | Rightwards Arrow | Arrows | maps to / then |
| `↓` | U+2193 | Downwards Arrow | Arrows | decrease |
| `↔` | U+2194 | Left Right Arrow | Arrows | sync offset |
| `│` | U+2502 | Box Drawing Vertical | Box Drawing | field separator |
| `─` | U+2500 | Box Drawing Horizontal | Box Drawing | rule |
| `═` | U+2550 | Double Horizontal | Box Drawing | rule |
| `║` | U+2551 | Double Vertical | Box Drawing | strong separator |
| `‖` | U+2016 | Double Vertical Line | General Punctuation | separator |
| `¦` | U+00A6 | Broken Bar | Latin-1 Supplement | light separator |
| `░` | U+2591 | Light Shade | Block Elements | meter, empty |
| `▒` | U+2592 | Medium Shade | Block Elements | meter, partial |
| `▓` | U+2593 | Dark Shade | Block Elements | meter, high |
| `█` | U+2588 | Full Block | Block Elements | meter, full |
| `▌` | U+258C | Left Half Block | Block Elements | meter, half |
| `»` | U+00BB | Right Angle Quote | Latin-1 Supplement | continues / next |
| `‹` | U+2039 | Single Left Angle Quote | General Punctuation | small pointer |
| `›` | U+203A | Single Right Angle Quote | General Punctuation | small pointer |
| `…` | U+2026 | Horizontal Ellipsis | General Punctuation | truncation |
| `°` | U+00B0 | Degree Sign | Latin-1 Supplement | units |
| `†` | U+2020 | Dagger | General Punctuation | footnote mark |
| `‡` | U+2021 | Double Dagger | General Punctuation | footnote mark |
| `‰` | U+2030 | Per Mille | General Punctuation | ratio |
| `¶` | U+00B6 | Pilcrow | Latin-1 Supplement | paragraph mark |
| `§` | U+00A7 | Section Sign | Latin-1 Supplement | section mark |
| `¤` | U+00A4 | Currency Sign | Latin-1 Supplement | generic marker |
| `∞` | U+221E | Infinity | Mathematical Operators | unlimited quota |
| `≈` | U+2248 | Almost Equal | Mathematical Operators | approximate match |
| `≠` | U+2260 | Not Equal | Mathematical Operators | mismatch |
| `±` | U+00B1 | Plus-Minus | Latin-1 Supplement | tolerance |
| `×` | U+00D7 | Multiplication Sign | Latin-1 Supplement | cross / no |
| `÷` | U+00F7 | Division Sign | Latin-1 Supplement | ratio |
| `¬` | U+00AC | Not Sign | Latin-1 Supplement | negation |
| `′` | U+2032 | Prime | General Punctuation | minutes |
| `″` | U+2033 | Double Prime | General Punctuation | seconds |
| `™` | U+2122 | Trade Mark | Letterlike Symbols | branding |
| `©` | U+00A9 | Copyright | Latin-1 Supplement | branding |
| `€` | U+20AC | Euro Sign | Currency Symbols | price |
| `£` | U+00A3 | Pound Sign | Latin-1 Supplement | price |
| `¥` | U+00A5 | Yen Sign | Latin-1 Supplement | price |
| `¢` | U+00A2 | Cent Sign | Latin-1 Supplement | price |

### ❌ Tofu (18 confirmed broken)

| Glyph | Codepoint | Name | Block | Use instead |
| :--- | :--- | :--- | :--- | :--- |
| `▶` | U+25B6 | Black Right Triangle | Geometric Shapes | use `►` U+25BA |
| `◆` | U+25C6 | Black Diamond | Geometric Shapes | use `■` U+25A0 |
| `✓` | U+2713 | Check Mark | Dingbats | use `√` U+221A |
| `✔` | U+2714 | Heavy Check Mark | Dingbats | use `√` U+221A |
| `✗` | U+2717 | Ballot X | Dingbats | use `×` U+00D7 |
| `✘` | U+2718 | Heavy Ballot X | Dingbats | use `×` U+00D7 |
| `✕` | U+2715 | Multiplication X | Dingbats | use `×` U+00D7 |
| `✖` | U+2716 | Heavy Multiplication X | Dingbats | use `×` U+00D7 |
| `✦` | U+2726 | Black Four Pointed Star | Dingbats | use `★` U+2605 |
| `✪` | U+272A | Circled White Star | Dingbats | use `★` U+2605 |
| `❖` | U+2756 | Black Diamond Minus X | Dingbats | use `■` U+25A0 |
| `☑` | U+2611 | Ballot Box With Check | Misc Symbols | use `√` U+221A |
| `☒` | U+2612 | Ballot Box With X | Misc Symbols | use `×` U+00D7 |
| `⚠` | U+26A0 | Warning Sign | Misc Symbols | use `[COLOR yellow]` text |
| `⚡` | U+26A1 | High Voltage | Misc Symbols | use `↯`-free text |
| `⇒` | U+21D2 | Rightwards Double Arrow | Arrows | use `→` U+2192 |
| `┃` | U+2503 | Heavy Vertical | Box Drawing | use `║` U+2551 |
| `┆` | U+2506 | Dotted Vertical | Box Drawing | use `│` U+2502 |

Emoji (U+1F000+ and `⭐` U+2B50) are worse than tofu: they break the `[COLOR]` markup
around them, so the tag itself leaks into the label as literal text. Never put one in
an on-screen string - `xbmc.log()` only.

### ❓ Not yet measured (16 in the current TRY rows)

| Glyph | Codepoint | Name | Block |
| :--- | :--- | :--- | :--- |
| `①` | U+2460 | Circled Digit One | Enclosed Alphanumerics |
| `②` | U+2461 | Circled Digit Two | Enclosed Alphanumerics |
| `ⓘ` | U+24D8 | Circled Latin Small I | Enclosed Alphanumerics |
| `Ⓐ` | U+24B6 | Circled Latin Capital A | Enclosed Alphanumerics |
| `⑴` | U+2474 | Parenthesized Digit One | Enclosed Alphanumerics |
| `–` | U+2013 | En Dash | General Punctuation |
| `—` | U+2014 | Em Dash | General Punctuation |
| `‾` | U+203E | Overline | General Punctuation |
| `«` | U+00AB | Left Angle Quote | Latin-1 Supplement |
| `„` | U+201E | Double Low Quote | General Punctuation |
| `¹` | U+00B9 | Superscript One | Latin-1 Supplement |
| `²` | U+00B2 | Superscript Two | Latin-1 Supplement |
| `³` | U+00B3 | Superscript Three | Latin-1 Supplement |
| `½` | U+00BD | One Half | Latin-1 Supplement |
| `¼` | U+00BC | One Quarter | Latin-1 Supplement |
| `¾` | U+00BE | Three Quarters | Latin-1 Supplement |

### How to run a test round
1. Enable **Test flag interceptor** in the add-on settings (debug section).
2. Trigger any subtitle search — the list is replaced by the glyph harness, 24 rows.
3. Each row reads `GLYPH nn TIER  <glyph> <codepoint> …`, so a blank rectangle sits directly next to the codepoint that failed. Note the codepoints, not the row numbers.
4. Rows are grouped and never re-ranked: **OK** rows on top (known-good baseline — if these break, the font itself changed), **TRY** rows next (untested candidates), **FAIL** rows last (already known bad, kept so a new font can be re-checked), then **FLAGS** / **CHARSET** rows exercising badges, native icons, and non-ASCII titles.
5. Move confirmed results into the matrix above, and move the glyph between tiers in `GLYPH_TEST_ROWS` (`resources/lib/subtitle_downloader.py`).

`tests/test_glyph_harness.py` asserts every printed codepoint actually matches its glyph — without that, a tofu box gets blamed on the wrong character.

### Re-testing under a different font or skin
Fonts are a Kodi-level setting; the add-on cannot change them, so results are per-skin/per-font and every round must record which one was used.
* **Font**: Settings → Interface → Skin → *Fonts* (Estuary ships `Default` (Roboto) and `Arial based`). The Arial set covers a different symbol range — worth a full round.
* **Skin**: Settings → Interface → Skin. A skin bundling its own TTF changes the result set entirely.
* Baseline for everything recorded above: **Estuary, `Default` fonts**.

### Rules distilled from the matrix
1. **Dingbats (U+2700–U+27BF) are entirely unavailable.** Every glyph tested from that block was tofu — no check marks, no crosses, no fancy stars.
2. **Misc Symbols (U+2600–U+26FF) are available only for `★` and `☆`.** Ballot boxes, warning, and lightning all fail.
3. **Latin-1 Supplement, General Punctuation, Mathematical Operators, Arrows, Box Drawing, Block Elements and Geometric Shapes are broadly safe** — every glyph tested from those blocks rendered, except the four gaps in rule 4.
4. **Four one-off gaps to route around**: `▶` U+25B6 → use `►` U+25BA · `◆` U+25C6 → use `■` U+25A0 · `⇒` U+21D2 → use `→` U+2192 · `┃` U+2503 / `┆` U+2506 → use `║` U+2551 / `│` U+2502. In each case a near-identical neighbour works, so nothing is actually lost.
5. **Latin diacritics and Cyrillic are fully safe**, including `ľščťžýáíéôäňĎĹŔ`, `Größe` and `Проверено Ґї€Њ` — confirmed inline in release titles.
6. **Emoji are not merely missing — they corrupt the line.** The `[COLOR]` tag around an emoji leaks into the label as literal text, so the whole badge is lost, not just the icon.
7. **Anything outside the ✅ table must be re-tested before shipping**, and re-tested again if the target skin or font changes.

### Recommended vocabulary (confirmed glyphs, mapped to meaning)

| Meaning | Glyph | Why this one |
| :--- | :--- | :--- |
| Verified / OK / trusted | `√` U+221A in `[COLOR green]` | The only check-like mark that renders — all real check marks are Dingbats and fail. |
| Rating, top pick | `★` U+2605 / `☆` U+2606 | The two Misc Symbols that survive; `☆` gives an empty-state counterpart. |
| Better / worse, higher / lower | `▲` U+25B2 / `▼` U+25BC | Reads as direction without color, so it still works for color-blind users. |
| Direction, mapping, offset | `→` U+2192, `↔` U+2194 | Full Arrows block renders (except `⇒`); `↔` suits sync-offset labels. |
| Play / next / previous | `►` U+25BA, `»` U+00BB, `◄` U+25C4 | Pointer shapes render; the triangle `▶` does not. |
| Not matching / negative | `×` U+00D7 | The Latin-1 multiplication sign stands in for every failed Dingbat cross. |
| Progress or score meter | `█ ▓ ▒ ░` U+2588/2593/2592/2591 | Full Block Elements range renders — a five-cell bar is viable in a label. |
| Field separator | `│` U+2502, `║` U+2551, `•` U+2022 | Light, heavy, and inline variants all confirmed. |
| Approximate / unlimited | `≈` U+2248, `∞` U+221E | Useful for fuzzy match scores and unlimited VIP quota. |

---

## 1c. 🚫 Why the add-on cannot show its own images in this dialog

Worth knowing before anyone proposes replacing badges with icons: **the subtitle selection
dialog gives the add-on no image slot it can point at its own PNG files.** The skin, not the
add-on, decides what is drawn, and Estuary's `xml/DialogSubtitles.xml` builds every texture
path itself:

```xml
<texture>$INFO[ListItem.Thumb,windows/subtitles/flags/,.png]</texture>
<texture fallback="flags/starrating/rating0.png">$INFO[ListItem.ActualIcon,flags/starrating/rating,.png]</texture>
```

The value the add-on sets is only the *middle* of a path the skin prefixes and suffixes, and
it resolves inside the skin's own texture bundle (`Textures.xbt`) — so `setArt({"thumb": ...})`
can only name a language flag the skin already ships, and `setArt({"icon": ...})` can only pick
`rating0`–`rating5`. An absolute path to a file in `resources/media/` produces a broken texture,
not a picture.

That leaves exactly four visual slots, all skin-drawn:

| Slot | How it is set | What it can show |
| :--- | :--- | :--- |
| Language flag | `setArt({"thumb": get_flag(lang)})` | one of the skin's flag images |
| Rating stars | `setArt({"icon": "0".."5"})` | the skin's 0–5 star images |
| SYNC icon | `setProperty("sync", "true")` | fixed skin icon |
| CC / SDH icon | `setProperty("hearing_imp", "true")` | fixed skin icon |

Everything else has to be text in `label2`, which is why the glyph matrix above matters. Other
skins compose these paths differently, so even this much is skin-dependent — another reason
badges stay textual.

---

## 2. 🖼️ Native Kodi Dialog Icons (Do NOT Duplicate in Text)

Kodi skins render native icons in dedicated columns for subtitle items. Avoid adding redundant text badges for these:

| Feature | Add-on Property / Art | Kodi UI Representation | Rule |
| :--- | :--- | :--- | :--- |
| **MovieHash Exact Match** | `list_item.setProperty("sync", "true")` | Native **SYNC** Icon | 🚫 Do NOT add `(Hash)` text tag |
| **Hearing Impaired / SDH** | `list_item.setProperty("hearing_imp", "true")` | Native **Ear / CC** Icon | 🚫 Do NOT add `[SDH]` text badge |
| **Subtitle Rating** | `list_item.setArt({"icon": "5"})` | Native **Star Column** (0–5 stars) | Rendered in star rating column |
| **Language Flag** | `list_item.setArt({"thumb": "flags/en.png"})` | Native **Flag Thumbnail** | Rendered in language flag column |

---

## 3. ❌ Unsupported / Broken (Do NOT Use)

* ❌ **Extended Emoji Planes (SMP Unicode U+1F000+)**:
  * `🤖`, `⚙️`, `🔒`, `🎬`, `🔥`, `👂`, `⭐`, `👍`, `👎`
  * *Reason*: Kodi's default fonts (e.g., Arial, Roboto) are standard TTF fonts without multi-color emoji glyphs. They render as blank spaces or empty rectangles.
  * *Scope*: applies to **every** on-screen string — list item labels, `Dialog.yesno()` button labels, `Dialog.ok()` bodies, notifications. Emoji in `xbmc.log()` output is fine (log file is plain UTF-8) and is the only place they are allowed.
* ❌ **Dingbats block (U+2700–U+27BF), entire block**: `✓ ✔ ✗ ✘ ✕ ✖ ✦ ✪ ❖` — see the test matrix in §1b.
* ❌ **Misc Symbols beyond `★`/`☆`**: `☑ ☒ ⚠ ⚡`.
* ❌ **Two Geometric Shapes gaps**: `▶` (U+25B6) and `◆` (U+25C6).
* ❌ **Complex Right-To-Left (RTL) Scripts (Arabic / Hebrew)**:
  * *Reason*: Kodi skins lack bi-directional shaping engines for list item titles, rendering characters reversed or detached.
* ❌ **Obsolete `[HD]` Flag**:
  * *Reason*: Redundant visual clutter since >99% of modern releases are HD/4K.

---

## 4. 🏷️ Final Recommended Badge Schema (Appended at END of Line)

```text
[Release Title] [Trusted] [AI] [Machine] [Forced] (+MatchScore)
```

### Examples:
* **Hash Match (with trusted uploader)**:
  ```text
  Example.Movie.2024.1080p.BluRay.x264-FLUX [COLOR green][Trusted][/COLOR]
  ```
  *(SYNC icon displayed by Kodi natively)*

* **AI-Translated Smart Match (+95 score)**:
  ```text
  Example.Movie.2024.1080p.BluRay.x264-FLUX [COLOR cyan][AI][/COLOR] [COLOR yellow](+95)[/COLOR]
  ```

* **Machine-Translated Forced Subtitle (+70 score)**:
  ```text
  Example.Movie.2024.720p.HDTV.x264 [COLOR orange][Machine][/COLOR] [COLOR yellow][Forced][/COLOR] [COLOR yellow](+70)[/COLOR]
  ```
