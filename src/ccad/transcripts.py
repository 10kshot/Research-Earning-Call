"""Parse Thomson Reuters StreetEvents transcript XML (`*_T.xml`) into call and turn records.

Step 03 of the plan: split each call into prepared remarks and Q&A, tag speaker
roles, split long prepared turns at paragraph breaks, and pair every Q&A answer
with the analyst question before it.
"""

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

EARNINGS_EVENT_TYPE = "Earning Conference Call/Presentation"
MAX_UNIT_WORDS = 250  # prepared-remarks turns are split into units of about this size

RULE = re.compile(r"^(=|-){20,}\s*$")
SPEAKER = re.compile(r"^\s*(?P<head>.+?)\s+\[(?P<n>\d+)\]\s*$")
SECTION_NAMES = {"Presentation": "prepared", "Questions and Answers": "qa"}
BLOCK_NAMES = {"Corporate Participants", "Conference Call Participants", "Definitions", "Disclaimer", *SECTION_NAMES}


def _text(root: ET.Element, tag: str) -> str:
    el = root.find(tag)
    return html.unescape(el.text.strip()) if el is not None and el.text else ""


def _parse_date(s: str) -> str | None:
    for fmt in ("%d-%b-%y %I:%M%p GMT", "%d-%b-%y %I:%M%p %Z"):
        try:
            return datetime.strptime(s.replace("am", "AM").replace("pm", "PM"), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _blocks(body: str) -> list[tuple[str, list[str]]]:
    """Split the body into (header, content lines). A header is a line with a
    ==== or ---- rule directly above and below it that is a known block name or a
    speaker line ending in [n]; adjacent headers may share a rule."""
    lines = body.splitlines()
    is_rule = [bool(RULE.match(l)) for l in lines]
    heads = [i for i in range(1, len(lines) - 1)
             if is_rule[i - 1] and is_rule[i + 1]
             and (lines[i].strip() in BLOCK_NAMES or SPEAKER.match(lines[i]))]
    out = []
    for k, i in enumerate(heads):
        stop = heads[k + 1] - 1 if k + 1 < len(heads) else len(lines)
        content = [l for l, r in zip(lines[i + 2:stop], is_rule[i + 2:stop]) if not r]
        out.append((lines[i].strip(), content))
    return out


def _participants(lines: list[str]) -> list[tuple[str, str]]:
    """'*  Name' followed by 'Firm - Title' lines -> [(name, 'Firm - Title')]."""
    out = []
    for k, line in enumerate(lines):
        if line.strip().startswith("*"):
            name = line.strip().lstrip("*").strip()
            desc = lines[k + 1].strip() if k + 1 < len(lines) else ""
            out.append((name, desc))
    return out


def _role(name: str, desc: str, corporate: set[str]) -> str:
    if name == "Operator":
        return "operator"
    if name.startswith("Unidentified"):
        return "unidentified_company" if "Company" in name or "Representative" in name else "unidentified"
    title = desc.rsplit(" - ", 1)[-1].lower() if " - " in desc else ""
    if name in corporate:
        if re.search(r"\bceo\b|chief executive", title):
            return "CEO"
        if re.search(r"\bcfo\b|chief financial", title):
            return "CFO"
        return "other_executive"
    if "analyst" in title or name not in corporate:
        return "analyst"
    return "other"


def _split_units(paragraphs: list[str]) -> list[str]:
    units, cur, words = [], [], 0
    for p in paragraphs:
        n = len(p.split())
        if cur and words + n > MAX_UNIT_WORDS:
            units.append("\n".join(cur))
            cur, words = [], 0
        cur.append(p)
        words += n
    if cur:
        units.append("\n".join(cur))
    return units


def parse_file(path: str | Path) -> tuple[dict, list[dict]]:
    """Return (call record, turn records) for one transcript file."""
    path = Path(path)
    return parse_xml(path.read_bytes(), path.name)


def parse_xml(xml: str | bytes, file_name: str) -> tuple[dict, list[dict]]:
    """Parse one transcript from its XML text, whatever source it came from."""
    root = ET.fromstring(xml)
    story = root.find("EventStory")
    body = html.unescape(story.findtext("Body") or "") if story is not None else ""
    call = {
        "transcript_id": root.get("Id"),
        "file_name": file_name,
        "event_type": root.get("eventTypeName"),
        "event_title": _text(root, "eventTitle"),
        "company_name": _text(root, "companyName"),
        "company_ticker": _text(root, "companyTicker"),
        "start_date_raw": _text(root, "startDate"),
        "call_date": _parse_date(_text(root, "startDate")),
        "city": _text(root, "city"),
        "version": story.get("version") if story is not None else None,
    }

    corporate, turns = set(), []
    section, last_question = None, None
    for header, content in _blocks(body):
        if header == "Corporate Participants":
            corporate |= {n for n, _ in _participants(content)}
        elif header in SECTION_NAMES:
            section = SECTION_NAMES[header]
        elif header in ("Definitions", "Disclaimer"):
            section = None
        elif section and (m := SPEAKER.match(header)):
            name, _, desc = m.group("head").partition(",")
            name, desc = name.strip(), desc.strip()
            _add_turn(turns, call, section, int(m.group("n")), name, desc, _role(name, desc, corporate), content)

    # Pair answers with the most recent preceding question in Q&A.
    for t in turns:
        if t["segment"] != "qa":
            continue
        if t["speaker_role"] in ("analyst", "unidentified"):
            last_question = t["turn_index"]
        elif t["speaker_role"] != "operator":
            t["question_turn_index"] = last_question
    call["n_turns"] = len({(t["segment"], t["turn_index"]) for t in turns})  # numbering restarts per section
    call["has_qa"] = any(t["segment"] == "qa" for t in turns)
    return call, turns


def _add_turn(turns, call, section, n, name, desc, role, content):
    paras = [p.strip() for p in content if p.strip()]
    units = _split_units(paras) if section == "prepared" else ["\n".join(paras)]
    for u, text in enumerate(units):
        turns.append({
            "transcript_id": call["transcript_id"],
            "call_date": call["call_date"],
            "segment": section,
            "turn_index": n,
            "unit_index": u,
            "speaker_name": name,
            "speaker_desc": desc,
            "speaker_role": role,
            "question_turn_index": None,
            "text": text,
        })
