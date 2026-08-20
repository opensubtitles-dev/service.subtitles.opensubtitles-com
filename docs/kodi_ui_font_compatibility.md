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
  * `🤖`, `⚙️`, `🔒`, `🎬`, `🔥`, `👂`, `⭐`
  * *Reason*: Kodi's default fonts (e.g., Arial, Roboto) are standard TTF fonts without multi-color emoji glyphs. They render as blank spaces or empty rectangles.
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
