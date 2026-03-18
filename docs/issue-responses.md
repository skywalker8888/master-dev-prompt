# Drafted Issue Responses

These are ready-to-paste responses for open GitHub issues. Copy each into the relevant issue comment.

---

## demo-repository #6 — "Why can't I do talk-to-text?"

> Paste this as a comment on https://github.com/skywalker8831/demo-repository/issues/6

Thanks for the report! Talk-to-text (speech input) is not currently implemented in this project — the UI accepts pasted text only.

Here's the current status and the path forward:

**Why it's not there yet:**
The backend processes text transcripts via a REST endpoint (`POST /process`). There is no audio capture or speech-to-text (STT) pipeline wired up on either the frontend or backend.

**How to add it (for anyone who wants to contribute):**
1. **Browser-side STT** — the Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`) works in Chrome and Edge without any backend changes. A small JS addition to `static/index.html` can capture speech and populate the textarea.
2. **Server-side STT** — for higher accuracy or non-Chrome browsers, wire in [OpenAI Whisper](https://github.com/openai/whisper) or the Whisper API. Add a `POST /transcribe` endpoint that accepts audio and returns text.

Option 1 is the quickest path if you only need Chrome support. I'm happy to help with a PR for either approach — let me know which you'd prefer.

---

## master #6, #7, #12, #13, #15 — Open Bugs (triage template)

> Use this as a starting comment if bug details are missing:

Thanks for filing this! To help reproduce and fix the issue, could you share:

1. **Steps to reproduce** — what exact action triggers the bug?
2. **Expected behavior** — what should happen?
3. **Actual behavior** — what happens instead? (include any error messages or stack traces)
4. **Environment** — OS, Python version, browser (if UI-related)?

Once we have those details, I'll dig in and open a fix PR.

---

## desktop-tutorial #162 — Bug (triage template)

> Same triage template as above applies. Add after reviewing the issue body.

---

## Copilot Instructions Issues (desktop-tutorial #131, #129, #124, #120, #107 · op2 #2 · master #4, #2)

> Paste this as a comment after creating the COPILOT_INSTRUCTIONS.md file in each repo:

Done! I've added `.github/COPILOT_INSTRUCTIONS.md` to this repository.

The file gives Copilot guidance on:
- Coding conventions and style (Python 3.11+, FastAPI, Pydantic v2)
- Project structure and key patterns
- PR/issue workflow requirements
- What to avoid (secrets, blocking calls, missing tests)

Feel free to open a follow-up issue if you'd like to extend or adjust the instructions.
