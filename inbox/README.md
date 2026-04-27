# 📥 Inbox — Drag-and-drop your sources here

> Visible drop zone at the project root for content that doesn't have a public URL — PDFs, decks exported from Google Slides, screenshots of paywalled articles, scanned notes, etc. The agent scans this folder and pulls anything new into the living library.

---

## Where this lives

**Physical path** (visible in Finder, not hidden):

```
/Users/danielstarr/Desktop/Startup Ideation/inbox/
```

Open Finder → navigate to **Desktop → Startup Ideation → inbox** → drag your file in.

That's it. No terminal, no hidden folders, no git knowledge required.

---

## How to use

1. **Drag your file into this folder.** (Or copy/save it here.)
   - Best format: `.pdf` (the agent's Read tool handles even multi-hundred-page decks via page-range chunking)
   - Also works: `.txt`, `.md`, `.html`
   - Naming: anything you want — the agent renames it during extraction
2. **Tell the agent:** *"I dropped X in inbox"* — or just paste the filename
3. **The agent does the rest:**
   - Reads the file
   - Runs **dedupe check** (matches against existing notes)
   - Extracts per the standard knowledge schema → writes a note to `knowledge/articles/{slug}.md`
   - Runs the **cross-correlation synthesis pass** (see below)
   - Cascades meta-files (INDEX, TAGS, THEMES, TENSIONS, PERSONA)
   - Moves your raw file to `inbox/processed/` so it doesn't get re-scanned
   - Auto-commits + pushes the .md note (the raw file itself stays on your disk only)

---

## What the synthesis pass surfaces

Beyond the standard extraction, every new ingestion runs a **cross-correlation sweep** against your existing library:

### 1. Tag overlap
For each tag the new note carries, list every other note that shares it. *"This note now connects to X, Y, Z."*

### 2. Named-entity overlap
Scans for **companies, people, technologies, frameworks, investors, products** mentioned. For each, greps across the library to find other notes that name the same thing. Surfaces threads:
- *"Rob Snyder mentions Stripe — also referenced in YC Lightcone (process power example)."*
- *"This deck cites Hamilton Helmer's Seven Powers — same framework as YC Lightcone moats discussion."*

### 3. Theme reinforcement / extension
Does this reinforce an existing theme in `knowledge/THEMES.md`? Add it as a source. Does it bridge two previously-unrelated notes into a new ≥2-source theme? Create one.

### 4. Tension surfacing
Does this contradict an existing source on the same decision? Log to `knowledge/TENSIONS.md` as Active.

### 5. Tag-vocab additions
If the source introduces concepts that don't fit the existing tag vocab, propose new tags + add to `CLAUDE.md` controlled vocab in the same turn.

---

## Why raw uploads aren't pushed to GitHub

`.gitignore` excludes raw files from this folder — only the structure (README, `.gitignore`, `processed/.gitkeep`) is tracked. **Reasoning:** PDFs are large binary blobs that bloat git repos. The .md extraction is what carries lasting value. Raw files stay on your disk for reference; the synthesis goes to GitHub.

If you ever want to re-extract from a raw file, it's still in `inbox/processed/`.

---

## Folder structure

```
inbox/
├── README.md           ← this file
├── .gitignore          ← keeps raw uploads out of git
├── {your-file}.pdf     ← drop here (unprocessed)
└── processed/          ← agent moves files here after ingestion
    └── {your-file}.pdf
```

---

## Auto-detection

- **At session start:** `/start-session` runs `ls inbox/` and surfaces any unprocessed files in the 📥 Inbox section of the boot output.
- **In-session:** when you mention an upload OR provide a path under `inbox/`, the agent immediately scans, identifies the new file, and starts processing.

---

## Notes

- Original files stay in `inbox/processed/` after ingestion — provenance preserved on your disk, can re-extract if the schema evolves.
- Large PDFs (>10 pages) are read in page-range chunks — no upper limit on deck size.
- If extraction fails (corrupted file, OCR issues, auth-walled content), the agent surfaces the failure cleanly — never silently drops content.
