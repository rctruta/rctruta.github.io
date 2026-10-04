"""Pydantic data models and validation loaders for portfolio data files."""
import pathlib
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

ROOT = pathlib.Path(__file__).resolve().parent.parent


class FacetMeta(BaseModel):
    label: str
    note: str = ""
    order: int = 99


class KindMeta(BaseModel):
    category: str
    order: int = 99


class TagVocabulary(BaseModel):
    facets: Dict[str, FacetMeta] = Field(default_factory=dict)
    kinds: Dict[str, KindMeta] = Field(default_factory=dict)
    vocabulary: Dict[str, str] = Field(default_factory=dict)

    def validate_tag(self, tag: str, context: str = ""):
        if tag not in self.vocabulary:
            msg = f"Tag '{tag}' not in controlled vocabulary data/TAGS.yaml"
            if context:
                msg += f" (on {context})"
            raise ValueError(msg)


class Figure(BaseModel):
    src: str
    alt: str = ""
    caption: str = ""


class ExternalLink(BaseModel):
    text: str
    url: str


class Note(BaseModel):
    text: Optional[str] = None
    label: Optional[str] = None
    url: Optional[str] = None


class ProjectItem(BaseModel):
    id: str
    title: str
    activity: str = "built"
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    figures: List[Figure] = Field(default_factory=list)
    links: List[ExternalLink] = Field(default_factory=list)
    notes: List[Note] = Field(default_factory=list)
    meta: Optional[str] = None
    url: Optional[str] = None
    source_page: str = "work.html"
    kind: str = "project"
    date_val: str = "2026"


class WorkSection(BaseModel):
    id: str
    title: str
    summary: str = ""
    items: List[ProjectItem] = Field(default_factory=list)


class Article(BaseModel):
    id: str
    title: str
    url: str
    platform: str
    date: str
    argues: str
    tags: List[str] = Field(default_factory=list)


class Appearance(BaseModel):
    id: str
    title: str
    org: str = ""
    date: str
    kind: str = "talk"
    format: str = ""
    role: str = ""
    tags: List[str] = Field(default_factory=list)
    eventType: str = ""
    location: str = ""
    slidesUrl: Optional[str] = None
    videoUrl: Optional[str] = None
    transcriptUrl: Optional[str] = None


def load_taxonomy() -> TagVocabulary:
    """Load data/TAGS.yaml into TagVocabulary model."""
    spec_path = ROOT / "data" / "TAGS.yaml"
    text = spec_path.read_text(encoding="utf-8")

    facets_meta = {}
    kinds_meta = {}
    vocab = {}

    section = None
    current_item = None
    facet_name = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            current_item = None
            continue

        if section == "facets":
            if indent == 2 and line.endswith(":"):
                current_item = line[:-1]
                facets_meta[current_item] = {"label": current_item.title(), "note": "", "order": 99}
            elif indent == 4 and current_item and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                v = v.strip('"\'')
                if k == "order":
                    v = int(v)
                facets_meta[current_item][k] = v

        elif section == "kinds":
            if indent == 2 and line.endswith(":"):
                current_item = line[:-1]
                kinds_meta[current_item] = {"category": current_item.title(), "order": 99}
            elif indent == 4 and current_item and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                v = v.strip('"\'')
                if k == "order":
                    v = int(v)
                kinds_meta[current_item][k] = v

        elif section == "vocabulary":
            if indent == 2 and line.endswith(":"):
                facet_name = line[:-1]
                continue
            if indent == 4 and facet_name and ":" in line:
                term = line.split(":", 1)[0].strip()
                vocab[term] = facet_name

    facets_obj = {k: FacetMeta(**v) for k, v in facets_meta.items()}
    kinds_obj = {k: KindMeta(**v) for k, v in kinds_meta.items()}

    return TagVocabulary(facets=facets_obj, kinds=kinds_obj, vocabulary=vocab)


def load_work_sections(vocab: TagVocabulary) -> List[WorkSection]:
    """Load data/work.yaml and validate all tags against controlled vocabulary."""
    work_path = ROOT / "data" / "work.yaml"
    text = work_path.read_text(encoding="utf-8")

    sections = []
    current_sec = None
    current_item = None
    in_figures = False
    in_links = False
    in_notes = False

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        raw_indent = len(line) - len(line.lstrip())
        trimmed = line.strip()

        if not trimmed or trimmed.startswith("#"):
            i += 1
            continue

        if raw_indent == 2 and trimmed.startswith("- id:"):
            current_sec = {"id": trimmed.split(":", 1)[1].strip(), "title": "", "summary": "", "items": []}
            sections.append(current_sec)
            current_item = None
            in_figures = in_links = in_notes = False

        elif raw_indent == 4 and current_sec and not current_item:
            if trimmed.startswith("title:"):
                current_sec["title"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("summary:"):
                current_sec["summary"] = trimmed.split(":", 1)[1].strip().strip('"')

        elif raw_indent == 6 and trimmed.startswith("- id:"):
            current_item = {
                "id": trimmed.split(":", 1)[1].strip(),
                "title": "",
                "activity": "built",
                "tags": [],
                "description": "",
                "figures": [],
                "links": [],
                "notes": [],
                "source_page": "work.html",
                "kind": "project"
            }
            current_sec["items"].append(current_item)
            in_figures = in_links = in_notes = False

        elif raw_indent == 8 and current_item:
            if trimmed.startswith("title:"):
                current_item["title"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("activity:"):
                current_item["activity"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("tags:"):
                tag_str = trimmed.split(":", 1)[1].strip().strip("[]")
                current_item["tags"] = [t.strip() for t in tag_str.split(",") if t.strip()]
            elif trimmed.startswith("description: |"):
                desc_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_line.strip() and next_indent <= 8 and not next_line.lstrip().startswith("#"):
                        i -= 1
                        break
                    desc_lines.append(next_line[10:] if len(next_line) >= 10 else next_line.lstrip())
                    i += 1
                current_item["description"] = "\n".join(desc_lines).strip()
            elif trimmed.startswith("figures:"):
                in_figures = True
                in_links = in_notes = False
            elif trimmed.startswith("links:"):
                in_links = True
                in_figures = in_notes = False
            elif trimmed.startswith("notes:"):
                in_notes = True
                in_figures = in_links = False

        elif raw_indent == 10 and current_item:
            if in_figures and trimmed.startswith("- src:"):
                fig = {"src": trimmed.split(":", 1)[1].strip().strip('"'), "alt": "", "caption": ""}
                current_item["figures"].append(fig)
            elif in_links and trimmed.startswith("- text:"):
                lnk = {"text": trimmed.split(":", 1)[1].strip().strip('"'), "url": ""}
                current_item["links"].append(lnk)
            elif in_notes and trimmed.startswith("-"):
                nt = {}
                if ":" in trimmed:
                    k, v = trimmed[1:].split(":", 1)
                    nt[k.strip()] = v.strip().strip('"')
                current_item["notes"].append(nt)

        elif raw_indent == 12 and current_item:
            if in_figures and current_item["figures"]:
                fig = current_item["figures"][-1]
                if trimmed.startswith("alt:"):
                    fig["alt"] = trimmed.split(":", 1)[1].strip().strip('"')
                elif trimmed.startswith("caption:"):
                    fig["caption"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif in_links and current_item["links"]:
                lnk = current_item["links"][-1]
                if trimmed.startswith("url:"):
                    lnk["url"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif in_notes and current_item["notes"]:
                nt = current_item["notes"][-1]
                if ":" in trimmed:
                    k, v = trimmed.split(":", 1)
                    nt[k.strip()] = v.strip().strip('"')

        i += 1

    result = []
    for s in sections:
        items_objs = []
        for item in s["items"]:
            for t in item["tags"]:
                vocab.validate_tag(t, f"work project {item['id']}")
            items_objs.append(ProjectItem(**item))
        s["items"] = items_objs
        result.append(WorkSection(**s))

    return result


def load_articles(vocab: TagVocabulary) -> List[Article]:
    """Load data/writing.yaml into Article models."""
    spec_path = ROOT / "data" / "writing.yaml"
    text = spec_path.read_text(encoding="utf-8")

    if "[YOURS]" in text:
        bad = re.findall(r"^  (\w+): \[YOURS\]", text, re.M)
        raise ValueError(f"writing.yaml still has unfilled placeholder fields: {', '.join(sorted(set(bad)))}")

    articles = []
    for block in re.split(r"\n(?=- id:)", text):
        if not block.lstrip().startswith("- id:"):
            continue
        def field(k):
            m = re.search(rf"^\s*(?:-\s*)?{k}: (.+?)\s*(?:#.*)?$", block, re.M)
            return m.group(1).strip().strip('"') if m else None

        aid = field("id")
        title = field("title")
        url = field("url")
        platform = field("platform")
        date = field("date")
        argues = field("argues")
        m_tags = re.search(r"^  tags: \[(.*)\]\s*$", block, re.M)
        tags = [t.strip() for t in m_tags.group(1).split(",")] if m_tags else []

        for t in tags:
            vocab.validate_tag(t, f"article {aid}")

        if aid and title and url and platform and date and argues:
            articles.append(Article(
                id=aid, title=title, url=url, platform=platform, date=date, argues=argues, tags=tags
            ))

    articles.sort(key=lambda a: a.date, reverse=True)
    return articles


def load_appearances(vocab: TagVocabulary) -> List[Appearance]:
    """Load data/appearances.yaml into Appearance models."""
    spec_path = ROOT / "data" / "appearances.yaml"
    text = spec_path.read_text(encoding="utf-8")

    appearances = []
    for block in re.split(r"\n(?=- id:)", text):
        if not block.lstrip().startswith("- id:"):
            continue
        def field(k):
            m = re.search(rf"^\s*(?:-\s*)?{k}: (.+?)\s*(?:#.*)?$", block, re.M)
            return m.group(1).strip().strip("'\"") if m else None

        aid = field("id")
        title = field("title")
        org = field("org") or ""
        date = field("date") or "2026"
        kind = field("kind") or "talk"
        format_val = field("format") or ""
        role = field("role") or ""
        eventType = field("eventType") or ""
        location = field("location") or ""
        slidesUrl = field("slidesUrl")
        videoUrl = field("videoUrl")
        transcriptUrl = field("transcriptUrl")

        m_tags = re.search(r"^  tags: \[(.*)\]\s*$", block, re.M)
        tags = [t.strip() for t in m_tags.group(1).split(",")] if m_tags else []

        for t in tags:
            vocab.validate_tag(t, f"appearance {aid}")

        if aid and title:
            appearances.append(Appearance(
                id=aid, title=title, org=org, date=date, kind=kind, format=format_val,
                role=role, tags=tags, eventType=eventType, location=location,
                slidesUrl=slidesUrl, videoUrl=videoUrl, transcriptUrl=transcriptUrl
            ))

    appearances.sort(key=lambda a: a.date, reverse=True)
    return appearances


# --- teaching: education and service -----------------------------------------
# These were hardcoded as HTML inside tools/build_teaching.py while the same
# facts sat unused in data/teaching.yaml. Editing the data changed nothing, and
# one honour was written into two sections, so it rendered twice.

class Degree(BaseModel):
    degree: str
    institution: str
    thesis: Optional[str] = None
    advisor: Optional[str] = None
    url: Optional[str] = None          # the deposited copy, if there is one
    isbn: Optional[str] = None
    # `year` is deliberately absent: dates invite age inference and add nothing.


class Education(BaseModel):
    degrees: List[Degree] = Field(default_factory=list)
    certificates: List[str] = Field(default_factory=list)
    honours: List[str] = Field(default_factory=list)


class Service(BaseModel):
    reviewing: List[str] = Field(default_factory=list)
    outreach: List[str] = Field(default_factory=list)
    outreach_note: str = ""
    volunteering: List[str] = Field(default_factory=list)
    affiliations: List[str] = Field(default_factory=list)


def _block(text: str, key: str) -> str:
    """The lines belonging to a top-level key, up to the next top-level key."""
    m = re.search(rf"^{key}:\n(.*?)(?=^\w|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def _str_list(block: str, key: str) -> List[str]:
    sub = re.search(rf"^  {key}:\n((?:\s+- .*\n?)+)", block, re.M)
    if not sub:
        return []
    return [re.sub(r'^\s*- ', '', ln).strip().strip('"')
            for ln in sub.group(1).splitlines() if ln.strip().startswith("- ")]


def load_education() -> Education:
    text = (ROOT / "data" / "teaching.yaml").read_text()
    block = _block(text, "education")
    degrees = []
    for chunk in re.split(r"\n(?=    - degree:)", block):
        if "- degree:" not in chunk:
            continue
        def f(k):
            m = re.search(rf'^\s+(?:- )?{k}: "(.*?)"\s*$', chunk, re.M)
            return m.group(1) if m else None
        degrees.append(Degree(degree=f("degree"), institution=f("institution"),
                              thesis=f("thesis"), advisor=f("advisor"),
                              url=f("url"), isbn=f("isbn")))
    return Education(degrees=degrees,
                     certificates=_str_list(block, "certificates"),
                     honours=_str_list(block, "honours"))


def load_service() -> Service:
    text = (ROOT / "data" / "teaching.yaml").read_text()
    block = _block(text, "service")
    note = re.search(r"^\s+note: \|\n((?:\s{6,}.*\n?)+)", block, re.M)
    return Service(reviewing=_str_list(block, "reviewing"),
                   outreach=_str_list(block, "outreach"),
                   outreach_note=" ".join(l.strip() for l in note.group(1).splitlines()) if note else "",
                   volunteering=_str_list(block, "volunteering"),
                   affiliations=_str_list(block, "affiliations"))
