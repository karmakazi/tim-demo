# Torah in Motion — search prototype

A plain static prototype with 264 public records (120 classes and 144 articles). No build step, framework, dependencies, or Drupal installation required.

## Deploy on Vercel
1. Unzip this package. Put the files inside `vercel-demo` at the root of a GitHub repository.
2. Import that repository in Vercel.
3. Set Framework Preset to **Other**. Leave Build Command empty and Output Directory at the project root (`.`). No install command is needed.
4. Deploy.

Alternatively, run the Vercel CLI from inside `vercel-demo` and follow its prompts. No environment variables are required for this static prototype.

## Connect Algolia
1. Create an index named `torah_demo` and upload `records.json` using **Upload a File**.
2. In index configuration, set searchable attributes to `title`, `speakers`, `topics`, `series`, `description`, in that order.
3. Set attributes for faceting to `content_type`, `formats`, `searchable(speakers)`, `searchable(topics)`. The corresponding settings are in `algolia-settings.json`.
4. Add the synonym groups from `algolia-synonyms.json` in the Synonyms settings.
5. Create an API key with only the **search** permission, restricted to `torah_demo`.
6. Click **Connect Algolia** in the prototype and enter the Application ID, search-only key, and index name. Settings are saved in that browser only.

To connect Algolia for every visitor, fill in `appId`, `apiKey`, and `indexName` in `config.js` and redeploy. These values are visible to visitors: use only the index-restricted search key. Never place an Admin or write key in this package. Vercel environment variables do not automatically populate static JavaScript.

## What is included
- Search as you type, sample-mode typo tolerance and transliteration matching
- Content type, format, teacher, and topic filters
- Pagination, empty state, and connection error messages
- Original content links; no media hosting or playback
- Algolia REST search integration ready for account credentials

Without Algolia credentials, search runs locally and is labeled Sample library. Algolia ranking, typo tolerance, and synonyms use your index configuration once connected. Date sorting is available locally; Algolia mode uses relevance and disables date sorting until sort replicas are implemented. Filter options and counts come from the bundled sample, so refresh records.json if the index grows beyond it.

The data was collected from public listing pages on November 18, 2026. Article descriptions are short listing excerpts; recordings have no transcripts. Class topics were not present on the listing pages and remain empty; series and titles are searchable. This is a sample of the full library. Nothing is installed on Torah in Motion's live website.

## Local preview
Serve this directory using any static web server, for example `python3 -m http.server 8765`, then open http://localhost:8765. Opening index.html directly from disk will not load records.json in most browsers.

Browser checks covered local speaker search and the empty state. Live Algolia connection cannot be verified until credentials and an uploaded index are available. Vercel deployment is prepared, not deployed by this package.
