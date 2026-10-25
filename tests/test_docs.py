"""Check the catalogue's documentation for structure and broken links.

- every pattern README starts with its RHP ID and the at-a-glance block,
  and has the standard sections in order;
- the index table and the checklist in README.md list every pattern by ID,
  and each "Seen in the wild" count matches the pattern page;
- every relative link in the Markdown files resolves to a file in the repo;
- CITATION.cff has the required keys and matches the latest CHANGELOG entry.

Standard library only, no network access.

Usage:
    python -m pytest tests/
    python tests/test_docs.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATTERN_DIRS = sorted(d for d in (ROOT / "patterns").iterdir() if d.is_dir())
MARKDOWN_FILES = sorted(ROOT.glob("*.md")) + [d / "README.md" for d in PATTERN_DIRS]

GLANCE_LABELS = ["TL;DR", "Typical impact", "Quick test", "Automated check"]
SECTIONS = [
    ("What it is",),
    ("Why it matters",),
    ("Vulnerable grader",),
    ("Fixed grader", "Partially mitigated grader"),
    ("How to test for it",),
    ("Seen in the wild",),
]
GRADER_PROBE_DOCS = "https://github.com/holdout-cc/grader-probe/blob/main/docs/checks.md"
# Headings in grader-probe's docs/checks.md; each is also its anchor.
GRADER_PROBE_CHECKS = {
    "empty", "refusal", "wrong_answer", "wrong_superstring", "candidate_list",
    "rejects_gold", "gold_in_reasoning", "wrong_after_correct", "claims_correct",
    "long_padding", "prompt_echo", "custom_no_credit", "gold", "whitespace", "case",
    "trailing_period", "in_sentence", "numeric_format", "listed_equivalents",
    "known_correct", "custom_full_credit",
}
ISSUE_LINK = re.compile(r"\]\((https://github\.com/[^/\s)]+/[^/\s)]+/(?:issues|pull)/\d+)\)")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def number(d):
    return d.name[:2]


def readme(d):
    return (d / "README.md").read_text(encoding="utf-8")


def seen_in_the_wild_links(d):
    section = readme(d).split("\n## Seen in the wild\n", 1)[1].split("\n## ", 1)[0]
    return set(ISSUE_LINK.findall(section))


def top_readme():
    return (ROOT / "README.md").read_text(encoding="utf-8")


def test_pattern_folders_are_numbered():
    numbers = [number(d) for d in PATTERN_DIRS]
    for d in PATTERN_DIRS:
        assert re.fullmatch(r"\d\d-[a-z0-9-]+", d.name), f"unexpected folder name {d.name}"
    assert numbers == [f"{i:02d}" for i in range(1, len(numbers) + 1)], f"numbers have gaps or repeats: {numbers}"


def test_pattern_titles_carry_ids():
    for d in PATTERN_DIRS:
        first = readme(d).split("\n", 1)[0]
        assert re.match(rf"# RHP-{number(d)}\. \S", first), f"{d.name}: title should start '# RHP-{number(d)}. ', got {first!r}"


def test_pattern_at_a_glance_block():
    for d in PATTERN_DIRS:
        lines = readme(d).split("\n")
        assert lines[1] == "", f"{d.name}: blank line expected after the title"
        for i, label in enumerate(GLANCE_LABELS):
            line = lines[2 + i]
            prefix = f"- **{label}:** "
            assert line.startswith(prefix) and line[len(prefix):].strip(), f"{d.name}: line {3 + i} should be {prefix!r} plus text, got {line!r}"
        assert lines[6] == "", f"{d.name}: blank line expected after the at-a-glance block"

        check_line = lines[5]
        anchors = re.findall(re.escape(GRADER_PROBE_DOCS) + r"#([A-Za-z0-9_-]+)\)", check_line)
        assert anchors or "Not covered by grader-probe" in check_line, f"{d.name}: Automated check needs a grader-probe link or 'Not covered by grader-probe'"
        unknown = set(anchors) - GRADER_PROBE_CHECKS
        assert not unknown, f"{d.name}: unknown grader-probe check anchors {sorted(unknown)}"
        assert check_line.count("grader-probe/") == len(anchors), f"{d.name}: grader-probe link without a check anchor"


def test_pattern_sections_in_order():
    for d in PATTERN_DIRS:
        headings = re.findall(r"^## (.+)$", readme(d), flags=re.M)
        pos = -1
        for options in SECTIONS:
            found = [i for i, h in enumerate(headings) if h.startswith(options)]
            assert found, f"{d.name}: missing section {options[0]!r}"
            assert found[0] > pos, f"{d.name}: section {options[0]!r} out of order"
            pos = found[0]


def test_index_table_lists_every_pattern():
    rows = re.findall(r"^\| (RHP-\d\d) \| \[[^\]]+\]\(patterns/([^)]+)/\) \| .+ \| (\d+) \|$", top_readme(), flags=re.M)
    by_id = {rid: (folder, int(count)) for rid, folder, count in rows}
    assert len(rows) == len(by_id), "duplicate IDs in the index table"
    assert sorted(by_id) == [f"RHP-{number(d)}" for d in PATTERN_DIRS], f"index table IDs: {sorted(by_id)}"
    for d in PATTERN_DIRS:
        folder, count = by_id[f"RHP-{number(d)}"]
        assert folder == d.name, f"RHP-{number(d)} links {folder}, expected {d.name}"
        links = seen_in_the_wild_links(d)
        assert count == len(links), f"RHP-{number(d)}: table says {count} public issues, the page links {len(links)}"


def test_checklist_items_carry_ids():
    section = top_readme().split("\n## Checklist before you ship an environment\n", 1)[1].split("\n## ", 1)[0]
    ids = re.findall(r"^\d+\. (RHP-\d\d): \S", section, flags=re.M)
    assert ids == [f"RHP-{number(d)}" for d in PATTERN_DIRS], f"checklist IDs: {ids}"


def test_relative_links_resolve():
    broken = []
    for md in MARKDOWN_FILES:
        text = md.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)  # code blocks are not links
        for target in MD_LINK.findall(text):
            if re.match(r"[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            resolved = (md.parent / path).resolve()
            if not resolved.exists() or (ROOT not in resolved.parents and resolved != ROOT):
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    assert not broken, "broken relative links:\n" + "\n".join(broken)


def read_cff():
    """Top-level 'key: value' pairs of CITATION.cff, enough for a key check."""
    data = {}
    for line in (ROOT / "CITATION.cff").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([a-z][a-z-]*):\s*(.*)$", line)
        if m:
            data[m.group(1)] = m.group(2).strip().strip('"')
    return data


def test_citation_cff():
    cff = read_cff()
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert cff.get("cff-version") == "1.2.0"
    for key in ("message", "title", "authors", "url", "repository-code", "license", "version", "date-released"):
        assert key in cff, f"CITATION.cff has no {key!r}"
    assert cff["title"], "CITATION.cff title is empty"
    assert re.search(r"^authors:\n  - name: \S", text, flags=re.M), "CITATION.cff authors need a name"
    assert cff["license"] == "MIT"
    for key in ("url", "repository-code"):
        assert cff[key] == "https://github.com/holdout-cc/reward-hack-patterns", f"unexpected {key}: {cff[key]}"
    assert re.fullmatch(r"\d+\.\d+\.\d+", cff["version"]), f"version {cff['version']!r} is not X.Y.Z"
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", cff["date-released"]), f"date-released {cff['date-released']!r} is not YYYY-MM-DD"

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## (\d+\.\d+\.\d+) - (\d{4}-\d\d-\d\d)$", changelog, flags=re.M)
    assert m, "CHANGELOG.md has no '## X.Y.Z - YYYY-MM-DD' entry"
    assert (cff["version"], cff["date-released"]) == m.groups(), (
        f"CITATION.cff says {cff['version']} ({cff['date-released']}), latest CHANGELOG entry is {m.group(1)} ({m.group(2)})"
    )


TESTS = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]


def main():
    failed = 0
    for test in TESTS:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {test.__name__}\n      {exc}")
        else:
            print(f"PASS  {test.__name__}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} documentation checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
