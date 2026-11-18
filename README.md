# Torah in Motion library search demo

A static Vercel-ready demo matching the layout and filter interactions of https://akelman.github.io/tim/example_library_search/. Uses 264 public records: 120 classes and 144 articles.

## Deploy on Vercel
Import this repository. Select **Other** as the framework, leave Build Command empty, and use the repository root (`.`) as Output Directory. No install command or environment variables are required.

## Update the Algolia index
**Re-upload the updated `records.json` to `torah-demo-records`.** Existing objectIDs are preserved so matching records can be replaced. The updated records include numeric `date_timestamp` fields (UTC seconds) required for date filters, and verified `audio_url` / `video_url` fields for direct media actions. An old upload still supports basic search. Direct media links for the 120 bundled classes are also supplied by matching objectID or class URL, even if the Algolia upload lacks media fields. Date filtering still requires updated records. New classes outside the bundled sample must include audio_url/video_url in Algolia.

Set these index settings in Algolia (JSON equivalent: `algolia-settings.json`):
- Searchable attributes, in order: `title`, `speakers`, `topics`, `series`, `description`.
- Attributes for faceting: `content_type`, `formats`, `searchable(speakers)`, `searchable(topics)`.
- Custom ranking: descending `date_timestamp`, as a tie breaker after relevance.
- Add synonym groups from `algolia-synonyms.json`.

Use **Algolia settings** to enter the Application ID, a search-only API key restricted to `torah-demo-records`, and the index name. Settings are saved only in the current browser. To connect every visitor, set those public search credentials in `config.js` and redeploy. Never add an Admin or write key to frontend files. Vercel environment variables do not automatically populate static JavaScript.

## Behavior
- Search as you type, with a submit fallback.
- Searchable speaker/topic dropdowns with multiple selections and removable chips.
- OR within each filter group, AND between groups.
- Inclusive start/end dates, individual date clear buttons, and range validation.
- Article/audio/video toggle filters, Clear all, and Hide/Show filters.
- Responsive result cards with Read article, Listen, and Watch video actions where source links exist.
- Pagination at 20 results per page, empty results, and connection error feedback.
- Local mode searches bundled records; connected mode queries Algolia and obtains speaker/topic options from its facets (up to 1,000 values per facet).

## Data and limits
Public listings were sampled November 18, 2026. Recording contents are not transcribed. Article descriptions are excerpts. Class topics are populated where verified in the reference dataset, and otherwise omitted. No classification is inferred. Direct media links reflect the public source; a source can contain mismatched filenames or broken links. Dates show day precision because recording time ranges were not collected. All media opens externally.

The layout and styling are adapted from the user-supplied reference page. Its externally hosted font stylesheets have local font fallbacks.

Local browser checks covered speaker suggestions/selection, combined date and speaker filters, clearing filters, and collapse/expand. JavaScript syntax is checked. Live Algolia behavior needs verification with your uploaded index and credentials; none are available in the repository.

## Preview locally
Run `python3 -m http.server 8765` in this directory, then open http://localhost:8765. Serve over HTTP; opening HTML directly from disk does not load JSON reliably.

## Format filtering compatibility
Format labels are normalized and augmented from verified audio/video links. In Algolia mode, format filtering is applied after media enrichment to all retrievable query matches, before result counts and pagination. This avoids losing matches with incomplete format metadata in an older upload. It may require extra search requests. If Algolia's retrieval limit prevents a complete set, the demo asks for a narrower query rather than showing incomplete results. Multiple formats use OR, consistent with the reference.

## Series grouping
Records with a nonempty `series` field become one expandable result per series, including series with only one matching talk. Parts sort by numeric part number (1, 2, 10); unnumbered talks follow in chronological order. Standalone records stay separate. Series names, not speaker names, identify groups so guest speakers in the same program remain together.

Grouping happens before pagination in both local and Algolia modes. Expanded lists contain only talks matching current search and filters, clearly labeled when filtering; a single matching talk still appears under its series. Open/closed state persists during filtering and pagination in the current page session. Algolia matches are collected before grouping, so the demo asks for a narrower query if its index retrieval limit would produce incomplete groups. No index changes or re-upload is required for the bundled records; for other records, populate `series` to enable grouping.

## Typo tolerance
Search requests explicitly allow no typo corrections for words of 1–4 characters, one typo for words of 5–7 characters, and up to two for words of 8 or more characters. Prefix matching remains available. This keeps `marc` from matching Marriage/Machzor while allowing misspellings in longer terms. The policy is applied per query word, so a longer word in a mixed query still gets typo tolerance. The same defaults are included in algolia-settings.json for future index setup; the deployed frontend applies them immediately without an index settings change.
