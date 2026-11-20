# Torah in Motion library search demo

A static Vercel-ready demo matching the layout and filter interactions of https://akelman.github.io/tim/example_library_search/. The expanded public sample has **2,000 records: 1,400 classes and 600 articles**, covering April 2019–November 2026. It includes 178 speakers, 174 topics, and 137 programs/series. See dataset-report.json for coverage and missing fields.

## Deploy
Import this repository into Vercel. Choose **Other** as framework, leave Build Command empty, and use the repository root (`.`) as Output Directory. No dependencies or environment variables are required.

## Algolia connection
Use **Algolia settings** to enter your Application ID, a search-only API key restricted to `torah-demo-records`, and that index name. Settings are saved in the current browser. To configure all visitors, put those public search credentials in `config.js` and redeploy. Never add Admin or write keys. Static JavaScript does not automatically read Vercel environment variables.

For a new index, upload `records.json`. Recommended ranking and searchable attributes are in `algolia-settings.json`; synonyms are in `algolia-synonyms.json`. **Upload the new records.json to include all 2,000 records in live search.** Existing objectIDs are preserved for all 264 original records. An older upload still works but only searches its own smaller dataset; the UI reports the index count. Deploy the matching app and data together so partition metadata stays in sync.

## How filtering works
Algolia searches the text query. The prototype retrieves all available matching records, enriches known media links/series from the bundled sample, then applies speaker, topic, format, and date filters before grouping and pagination. It reads the existing `date` values in YYYY-MM-DD form, not numeric timestamps. This also works if the Algolia index has no `attributesForFaceting` configured. Speaker/topic dropdown options come from the live record fields. Local sample mode uses the same filter rules.

Responses are cached in memory for up to 60 seconds per connection and text query, so selecting/clearing filters does not repeat the same network search. The expanded export assigns every record a numeric search_partition with at most 500 items. If a search exceeds Algolia's pagination limit, the app retrieves disjoint partitions, verifies completeness, and merges relevance results before filtering/grouping. This works without facet setup. Unknown or incomplete partitions produce an explicit index/data mismatch message rather than silently dropping records. For a substantially larger production library, use server-side filtering and group-oriented indexing.

## UX
- Search as you type; short words (1–4 letters) require precise prefix matching. Longer words retain typo tolerance.
- Searchable multi-select speaker/topic dropdowns; removable selection chips; mouse and keyboard selection.
- Date range inclusive of both boundaries, individual clears, Clear all, and invalid range feedback.
- Article/audio/video format toggles, OR within groups and AND between groups.
- One expandable result per series; numeric part order, then dates for unnumbered talks. Guest speakers in one program remain together.
- Only parts matching the current query/filters are shown; the UI labels this explicitly.
- Standalone content stays separate. Pagination operates on groups, not individual talks.
- Direct Read article, Listen, and Watch video actions wherever source links are available.

## Data
Public listing and detail pages were collected November 18, 2026 at a shared maximum of about three requests per second, with two workers. All 2,000 pages parsed successfully. Topics, speakers, series, and media URLs are taken from the detail pages. There are 1,398 audio links, 1,399 video links, and 805 PDF/source-sheet links. All records have dates and topics; 16 pages do not publish a speaker name, which remains empty. Article descriptions are bounded excerpts, not full articles or recording transcripts. Class pages do not publish description text; none is invented. Dates have day precision. The dataset is selected, not the full archive; series may be incomplete, and known numbered-part gaps are listed in dataset-report.json. Media links were extracted from source pages, not comprehensively checked for playback. Bundled classes can recover media and series information by stable objectID or URL when an older index upload lacks those fields.

Layout and styles are adapted from the supplied reference. External font stylesheets have local fallbacks.

## Verification
Run `node --test tests/search.test.cjs` for search/filter regressions, including complete retrieval of 2,000 hits across four partitions, grouping, and same-title programs with different IDs. Run `python3 tests/test_tools.py` for importer and validator checks, `python3 scripts/validate-data.py` for dataset quality, and `node --check app.js` for syntax.

Browser verification against the actual live Algolia index covered selecting Marc Shapiro by mouse and keyboard, speaker plus November 1–16 dates, Chanukah topic selection, a November 13-only range, removing a selected topic, clearing all filters, and expanding the filtered series. Results were checked, not just input changes. No credentials are committed or written into test files.

## Local preview
Run `python3 -m http.server 8765` in this directory and open http://localhost:8765. Direct file opening does not reliably load JSON.

## Import and refresh helpers
For a dashboard import, use **Upload a File** on `torah-demo-records` and select `records.json`. Keep the provided objectIDs. Recommended search settings are in `algolia-settings.json`.

Alternatively, run `python3 scripts/upload-algolia.py --dry-run` to validate the import, then `python3 scripts/upload-algolia.py` to apply settings and upload records. It prompts locally for an index-restricted key with addObject, editSettings, and search permissions; no private key belongs in chat, Git, or frontend config. It batches updates, waits for indexing, reports the final count, and never clears or deletes index records. An actual write import has not been run by the builder because only a search-only key is available.

`scripts/collect-public.py` reproduces the public crawl (requires beautifulsoup4). It uses a resumable `.crawl-cache/` folder ignored by Git, preserves IDs already present in records.json, and writes a candidate expanded-records.json into that cache. Validate before replacing the bundled dataset. Remove the cache only when a fully fresh crawl is desired. No media files are downloaded.

## Sentence and phrase search
The frontend removes conservative conversational scaffolding (for example, “Can you find classes about …”), while preserving negations and all words inside double quotes. It passes the cleaned terms to Algolia with exact-phrase syntax enabled and without optional-word relaxation. Curly quotation marks are accepted. Unquoted multiword queries still require all remaining keywords; no meanings or concepts are invented. Filler-only text is not turned into an empty query that browses everything.

Titles, speakers, topics, and adjacent query words receive more weight than passing mentions in descriptions. Exact typo matches remain ahead of fuzzy matches, so short-name precision is preserved. Quoted phrases must occur contiguously in the same searchable field; those phrases are also checked on returned records. Local mode uses the same cleanup and phrase rules. These are keyword relevance improvements, not semantic AI search or transcript search. No data re-upload or privileged Algolia setting change is required to use them after deploying the app.
