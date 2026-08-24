"""Word-level diff between two normalized text blobs, using difflib
(stdlib, no extra dependency, deterministic). Produces added/removed
phrase lists rather than a line-oriented diff, since pages are single
blobs of flowing text after normalization."""
import difflib


def word_diff(old_text: str, new_text: str) -> dict:
    old_words = old_text.split()
    new_words = new_text.split()

    matcher = difflib.SequenceMatcher(a=old_words, b=new_words, autojunk=False)

    added, removed, modified = [], [], []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_chunk = " ".join(old_words[i1:i2]).strip()
        new_chunk = " ".join(new_words[j1:j2]).strip()
        if tag == "insert" and new_chunk:
            added.append(new_chunk)
        elif tag == "delete" and old_chunk:
            removed.append(old_chunk)
        elif tag == "replace":
            if old_chunk or new_chunk:
                modified.append({"before": old_chunk, "after": new_chunk})

    total_words = max(len(old_words), len(new_words), 1)
    changed_words = sum(len(a.split()) for a in added) + \
        sum(len(r.split()) for r in removed) + \
        sum(len(m["before"].split()) + len(m["after"].split()) for m in modified)
    change_ratio = min(changed_words / total_words, 1.0)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "change_ratio": round(change_ratio, 4),
    }
