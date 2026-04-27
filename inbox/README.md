# 📥 Inbox — Drop new sources here

> Local-storage drop zone for content that doesn't have a public URL — PDFs, decks exported from Google Slides, screenshots of paywalled articles, scanned notes, etc. The agent scans this folder for new files and pulls them into the living library.

---

## How to use

1. **Drop your file here** (in `inbox/`, not `inbox/processed/`)
   - Supported: `.pdf` (best — Read tool handles natively, even multi-hundred-page decks via page-range parameter), `.txt`, `.md`, `.html`
   - Naming: anything goes — agent renames at extraction time
2. **Tell the agent:** *"I dropped X in inbox"* — or just paste the path
3. **The agent does the rest:**
   - Reads the file (PDF page-range chunks if large)
   - Runs **dedupe** (file-hash + title-match against existing notes)
   - Extracts per the standard knowledge schema → `knowledge/articles/{slug}.md`
   - Runs **post-extraction synthesis pass** (see below)
   - Cascades meta-files (INDEX, TAGS, THEMES, TENSIONS, PERSONA)
   - Moves source to `inbox/processed/{filename}` so it's not re-scanned
   - Auto-commits + pushes everything

---

## What the synthesis pass does

Beyond the standard extraction, every new ingestion now includes a **cross-correlation sweep** against the existing library:

### 1. Tag overlap
For each tag the new note carries, list every other note that shares it. Surface this in the extraction summary so the founder can see *"this is now connected to X, Y, Z."*

### 2. Named-entity overlap
Scan the new note for **companies, people, technologies, frameworks** mentioned. For each, grep across `knowledge/` to find other notes that name the same entity. Surface threads:
- *"Rob Snyder mentions Stripe — also referenced in YC Lightcone (process power example)."*
- *"This deck cites Hamilton Helmer's Seven Powers — same framework as YC Lightcone moats discussion."*

### 3. Theme reinforcement / extension
Does this note reinforce an existing theme in `knowledge/THEMES.md`? Add it as a source. Does it bridge two previously-unrelated notes into a new ≥2-source theme? Create one.

### 4. Tension surfacing
Does this note contradict an existing source on the same decision? Log to `knowledge/TENSIONS.md` as Active.

### 5. Tag-vocab additions
If the source introduces concepts that don't fit the existing tag vocab, propose new tags + add to `CLAUDE.md` controlled vocab in the same turn.

---

## Folder structure

```
inbox/
├── README.md           ← this file
├── {your-file}.pdf     ← drop here (unprocessed)
└── processed/          ← moved here after ingestion (raw archive)
    └── {your-file}.pdf
```

---

## Auto-detection

- **In-session:** when the founder mentions an upload OR provides a path under `inbox/`, the agent immediately `ls`'s the folder, identifies unprocessed files, and starts processing.
- **At session start:** `/start-session` runs `ls inbox/` and surfaces any unprocessed files in the boot output as `📥 Inbox: N file(s) waiting to be ingested`.

---

## Notes

- Original files are kept in `inbox/processed/` after ingestion — provenance preserved, can re-extract if the schema evolves.
- Large PDFs (>10 pages) are read via the `pages` parameter in chunks — no upper limit on deck size, just costs more tokens to ingest.
- If the source is auth-walled or extraction fails, the agent surfaces the failure cleanly — never silently drops content.
