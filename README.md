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
