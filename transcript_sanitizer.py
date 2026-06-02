import re

_MARKER_RE = re.compile(r"wispr\s*flow", re.IGNORECASE)


def sanitize_transcript(transcript: str) -> str:
    cleaned = _MARKER_RE.sub(" ", transcript)
    apostrophe_spacing_patterns = (" ' ", " '", "' ")
    for pattern in apostrophe_spacing_patterns:
        cleaned = cleaned.replace(pattern, "'")
    for punct in ",.;:!?":
        cleaned = cleaned.replace(f" {punct}", punct).replace(f"\t{punct}", punct)

    normalized_lines = []
    for line in cleaned.splitlines():
        normalized = " ".join(line.split())
        if normalized:
            normalized_lines.append(normalized)

    return "\n".join(normalized_lines).strip()
