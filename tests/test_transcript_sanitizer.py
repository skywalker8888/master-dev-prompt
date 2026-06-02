from transcript_sanitizer import sanitize_transcript


def test_sanitize_transcript_removes_wispr_flow_markers():
    noisy = (
        "Wispr FlowCanWispr Flow Wispr FlowyouWispr Flow Wispr FlowfixWispr Flow "
        "myWispr Flow Wispr FlowagentWispr Flow canWispr Flow'Wispr Flowt read it?"
    )

    assert sanitize_transcript(noisy) == "Can you fix my agent can't read it?"


def test_sanitize_transcript_leaves_clean_text_readable():
    text = "We need this live in 3 weeks."
    assert sanitize_transcript(text) == text


def test_sanitize_transcript_handles_marker_only_and_punctuation_spacing():
    assert sanitize_transcript("Wispr Flow Wispr Flow") == ""
    assert sanitize_transcript("Hello ,   world !") == "Hello, world!"
