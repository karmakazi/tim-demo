# Torah in Motion library search demo

A static Vercel-ready demo matching the layout and filter interactions of https://akelman.github.io/tim/example_library_search/. The public sample has 264 records: 120 classes and 144 articles.

## Deploy
Import this repository into Vercel. Choose **Other** as framework, leave Build Command empty, and use the repository root (`.`) as Output Directory. No dependencies or environment variables are required.

## Algolia connection
Use **Algolia settings** to enter your Application ID, a search-only API key restricted to `torah-demo-records`, and that index name. Settings are saved in the current browser. To configure all visitors, put those public search credentials in `config.js` and redeploy. Never add Admin or write keys. Static JavaScript does not automatically read Vercel environment variables.

For a new index, upload `records.json`. Recommended ranking and searchable attributes are in `algolia-settings.json`; synonyms are in `algolia-synonyms.json`. Existing uploads do not need to be replaced for the prototype's speaker, topic, date, format, or series controls to work.

## How filtering works
Algolia searches the text query. The prototype retrieves all available matching records, enriches known media links/series from the bundled sample, then applies speaker, topic, format, and date filters before grouping and pagination. It reads the existing `date` values in YYYY-MM-DD form, not numeric timestamps. This also works if the Algolia index has no `attributesForFaceting` configured. Speaker/topic dropdown options come from the live record fields. Local sample mode uses the same filter rules.

Responses are cached in memory for up to 60 seconds per connection and text query, so selecting/clearing filters does not repeat the same network search. If Algolia's retrieval limit prevents collecting all matches, the UI asks for a narrower search rather than returning incomplete groups. For a substantially larger production index, move filtering/grouping server-side with properly configured index attributes.

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
Public listings were sampled November 18, 2026. Descriptions are excerpts, not transcripts. Class topics are populated where verified in the reference dataset; otherwise omitted. Dates have day precision. Media URLs reflect the public source. The 120 sampled classes can recover direct media links by stable objectID or class URL when an older Algolia upload lacks those fields. New classes outside that sample need their own media fields.

Layout and styles are adapted from the supplied reference. External font stylesheets have local fallbacks.

## Verification
Run `node --test tests/search.test.cjs` for regressions covering an index without facet configuration or numeric date fields, combined filtering, inclusive dates, caching, error recovery, and retrieval-limit handling. Run `node --check app.js` for syntax.

Browser verification against the actual live Algolia index covered selecting Marc Shapiro by mouse and keyboard, speaker plus November 1–16 dates, Chanukah topic selection, a November 13-only range, removing a selected topic, clearing all filters, and expanding the filtered series. Results were checked, not just input changes. No credentials are committed or written into test files.

## Local preview
Run `python3 -m http.server 8765` in this directory and open http://localhost:8765. Direct file opening does not reliably load JSON.
