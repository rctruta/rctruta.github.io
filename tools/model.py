"""Pydantic data models and validation loaders for portfolio data files."""
import os
import pathlib
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()
VOCAB_FILENAME = CONFIG["data"]["controlled_vocabulary"]

# Employment history lives OUTSIDE this repository, which is public.
#
# It was briefly committed here on 2026-10-15 and should never have been: it
# carries a contract role deliberately absent from the portfolio, and notes
# about which dates are still unconfirmed. check_private.py did not catch it
# because that gate looks for email addresses and phone numbers, and this is
# neither — it is private by subject, not by pattern.
#
# The website has never needed employment rows: it is organised by project
# (work.yaml) and by teaching artifact (teaching.yaml). Only the résumé needs
# titles and dates, so the file belongs beside the résumés.
_PRIVATE_DIR = os.environ.get("SITE_PRIVATE_DIR")
EMPLOYMENT_PATH = (pathlib.Path(_PRIVATE_DIR) / "employment.yaml"
                   if _PRIVATE_DIR else pathlib.Path("/nonexistent/employment.yaml"))


class FacetMeta(BaseModel):
    label: str
    note: str = ""
    order: int = 99


class KindMeta(BaseModel):
    category: str
    note: str = ""      # the scope note: what belongs under this kind
    order: int = 99


class TagVocabulary(BaseModel):
    facets: Dict[str, FacetMeta] = Field(default_factory=dict)
    kinds: Dict[str, KindMeta] = Field(default_factory=dict)
    vocabulary: Dict[str, str] = Field(default_factory=dict)   # term -> facet
    notes: Dict[str, str] = Field(default_factory=dict)         # term -> scope note
    # The synonym ring (Z39.19 UF, "used for"): labels a reader or a keyword
    # filter might arrive with, pointing at the one term that is preferred here.
    # An entry term is deliberately NOT a descriptor — nothing is ever tagged
    # with it, and it carries no count of its own.
    synonyms: Dict[str, List[str]] = Field(default_factory=dict)  # term -> entry terms

    def validate_tag(self, tag: str, context: str = ""):
        if tag not in self.vocabulary:
            msg = f"Tag '{tag}' not in controlled vocabulary data/{VOCAB_FILENAME}"
            if tag in self.entry_terms():
                msg += (f" — it is an entry term for "
                        f"'{self.entry_terms()[tag]}'. Tag with that instead.")
            if context:
                msg += f" (on {context})"
            raise ValueError(msg)

    def entry_terms(self) -> Dict[str, str]:
        """entry term -> the descriptor it points to."""
        return {syn: term for term, syns in self.synonyms.items() for syn in syns}


class Figure(BaseModel):
    src: str
    alt: str = ""
    caption: str = ""


class ExternalLink(BaseModel):
    text: str
    url: str


class Note(BaseModel):
    """A caveat: a date, a limit, a thing the entry is NOT claiming."""
    text: Optional[str] = None
    label: Optional[str] = None
    url: Optional[str] = None


class Recognition(BaseModel):
    """Someone else chose this work. Not a caveat, so not a Note.

    Recognition was briefly written into `notes`, which renders in the same
    box as "what this entry does not claim" -- so being selected by a third
    party looked identical to a disclaimer.

    Every field here is REQUIRED, which is the point. Recognition without a
    date and a link is the exact shape of a claim that inflates quietly: no
    way to check who said it or when. The schema refuses an unsourced one
    rather than relying on whoever is editing to remember.
    """
    who: str
    what: str
    date: str
    url: str
    terms: str = ""     # licence or attribution conditions, when they matter
    # An image the recognising party serves and updates themselves. Optional,
    # and preferable to a score typed into `what`: a number in prose is true
    # on the day it is written and silently wrong afterwards, while a badge
    # fetched from the source cannot disagree with the source. mcprush's score
    # was published here as 93/100 and was stale within two days.
    badge: str = ""
    badge_alt: str = ""


class ProjectItem(BaseModel):
    id: str
    title: str
    blurb: str = ""     # one line for the GitHub profile, where the full description does not fit
    resume: str = ""    # the master résumé's bullet, subject included; read only by build_resume.py
    activity: str = "built"
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    figures: List[Figure] = Field(default_factory=list)
    links: List[ExternalLink] = Field(default_factory=list)
    notes: List[Note] = Field(default_factory=list)
    recognition: List[Recognition] = Field(default_factory=list)
    meta: Optional[str] = None
    url: Optional[str] = None
    source_page: str = "work.html"
    kind: str = "project"
    date_val: str = "2026"

    @property
    def one_line(self) -> str:
        """The item's own one-liner, else its first sentence.

        Truncating to a first sentence inverted a finding once — podcast-rag
        read as "no error of any kind", which is the opposite of what the study
        found — so an item can carry its own summary and these do.

        Lives on the model because the GitHub profile and the master résumé
        both need it, and two copies of this rule would drift the way every
        other duplicated value in this repository has.
        """
        if self.blurb:
            return self.blurb
        text = " ".join(self.description.strip().split())
        # a description that opens by repeating the repository name in bold
        text = re.sub(r"^\*\*[^*]+\*\* — ", "", text)
        return re.split(r"(?<=[.!?]) ", text)[0]


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
    url: Optional[str] = None          # the published episode or talk page
    counterpart: Optional[str] = None  # who I interviewed, when guest host
    note: Optional[str] = None
    slidesUrl: Optional[str] = None
    videoUrl: Optional[str] = None
    transcriptUrl: Optional[str] = None


def load_taxonomy() -> TagVocabulary:
    """Load controlled vocabulary into TagVocabulary model."""
    spec_path = ROOT / "data" / VOCAB_FILENAME
    text = spec_path.read_text(encoding="utf-8")

    facets_meta = {}
    kinds_meta = {}
    vocab = {}
    notes = {}
    synonyms = {}

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
                term, note = [x.strip() for x in line.split(":", 1)]
                vocab[term] = facet_name
                if note:
                    notes[term] = note.strip('"\'')

        elif section == "synonyms":
            if indent == 2 and ":" in line:
                term, raw_syns = [x.strip() for x in line.split(":", 1)]
                syns = [s.strip().strip('"\'') for s in
                        raw_syns.strip().lstrip("[").rstrip("]").split(",")]
                synonyms[term] = [s for s in syns if s]

    # A ring that points at a term nobody uses, or that collides with a real
    # descriptor, is worse than no ring: it sends a reader somewhere empty.
    seen = {}
    for term, syns in synonyms.items():
        if term not in vocab:
            raise ValueError(
                f"data/{VOCAB_FILENAME}: synonyms list '{term}', which is not a "
                f"term in the vocabulary. An entry term must point at a descriptor.")
        for syn in syns:
            if syn in vocab:
                raise ValueError(
                    f"data/{VOCAB_FILENAME}: '{syn}' is both a descriptor and an "
                    f"entry term for '{term}'. It must be one or the other.")
            if syn in seen:
                raise ValueError(
                    f"data/{VOCAB_FILENAME}: entry term '{syn}' points at both "
                    f"'{seen[syn]}' and '{term}'. One entry term, one descriptor.")
            seen[syn] = term

    facets_obj = {k: FacetMeta(**v) for k, v in facets_meta.items()}
    kinds_obj = {k: KindMeta(**v) for k, v in kinds_meta.items()}

    return TagVocabulary(facets=facets_obj, kinds=kinds_obj, vocabulary=vocab,
                         notes=notes, synonyms=synonyms)


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
    in_recog = False

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
            in_figures = in_links = in_notes = in_recog = False

        elif raw_indent == 4 and current_sec and not current_item:
            if trimmed.startswith("title:"):
                current_sec["title"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("summary:"):
                current_sec["summary"] = trimmed.split(":", 1)[1].strip().strip('"')

        elif raw_indent == 6 and trimmed.startswith("- id:"):
            current_item = {
                "id": trimmed.split(":", 1)[1].strip(),
                "title": "",
                "blurb": "",
                "activity": "built",
                "tags": [],
                "description": "",
                "figures": [],
                "links": [],
                "notes": [],
                "recognition": [],
                "source_page": "work.html",
                "kind": "project"
            }
            current_sec["items"].append(current_item)
            in_figures = in_links = in_notes = in_recog = False

        elif raw_indent == 8 and current_item:
            if trimmed.startswith("title:"):
                current_item["title"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("blurb:"):
                current_item["blurb"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("resume:"):
                current_item["resume"] = trimmed.split(":", 1)[1].strip().strip('"')
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
                in_links = in_notes = in_recog = False
            elif trimmed.startswith("links:"):
                in_links = True
                in_figures = in_notes = in_recog = False
            elif trimmed.startswith("notes:"):
                in_notes = True
                in_figures = in_links = in_recog = False
            elif trimmed.startswith("recognition:"):
                in_recog = True
                in_figures = in_links = in_notes = False

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
            elif in_recog and trimmed.startswith("-"):
                rc = {}
                if ":" in trimmed:
                    k, v = trimmed[1:].split(":", 1)
                    rc[k.strip()] = v.strip().strip('"')
                current_item["recognition"].append(rc)

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
            elif in_recog and current_item["recognition"]:
                rc = current_item["recognition"][-1]
                if ":" in trimmed:
                    k, v = trimmed.split(":", 1)
                    rc[k.strip()] = v.strip().strip('"')

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
        def field(k, block=block):
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
        def field(k, block=block):
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
        url = field("url")
        counterpart = field("counterpart")
        note = field("note")
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
                url=url, counterpart=counterpart, note=note,
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


class Certificate(BaseModel):
    """A certificate, with a link to the proof where one exists.

    These were plain strings until 2026-10-22, which meant a certificate could
    not carry its own verification link. The LinkedIn export supplies one for
    95 of 105, so the strings became records -- the same move `degrees` made
    earlier, for the same reason.

    `professional` marks the six that belong on a resume. The rest are course
    completions: they are published because each links to proof the course was
    taken, which is what makes the skill checkable rather than asserted.
    `build_resume.py` reads only the professional ones.
    """
    name: str
    issuer: str = ""
    url: Optional[str] = None          # the issuer's verification page
    date: str = ""                    # issue date
    expires: str = ""                 # LinkedIn's "Finished On"
    professional: bool = False


class Education(BaseModel):
    degrees: List[Degree] = Field(default_factory=list)
    certificates: List[Certificate] = Field(default_factory=list)
    honours: List[str] = Field(default_factory=list)

    @property
    def professional_certificates(self) -> List[Certificate]:
        return [c for c in self.certificates if c.professional]

    @property
    def course_certificates(self) -> List[Certificate]:
        return [c for c in self.certificates if not c.professional]


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
        def f(k, chunk=chunk):
            m = re.search(rf'^\s+(?:- )?{k}: "(.*?)"\s*$', chunk, re.M)
            return m.group(1) if m else None
        degrees.append(Degree(degree=f("degree"), institution=f("institution"),
                              thesis=f("thesis"), advisor=f("advisor"),
                              url=f("url"), isbn=f("isbn")))
    certs = []
    # `certificates:` is nested under `education:`, so _block -- which anchors
    # on a top-level key -- cannot reach it. Take the lines from that key to
    # the next key at the same indent.
    _cm = re.search(r"^  certificates:\n(.*?)(?=^  \w|\Z)", block, re.M | re.S)
    cert_block = _cm.group(1) if _cm else ""
    for chunk in re.split(r"\n(?=    - name:)", cert_block):
        if "- name:" not in chunk:
            continue

        def c(k, chunk=chunk):
            m = re.search(rf'^\s+(?:- )?{k}: "(.*?)"\s*$', chunk, re.M)
            return m.group(1) if m else None
        certs.append(Certificate(
            name=c("name"), issuer=c("issuer") or "", url=c("url"),
            date=c("date") or "", expires=c("expires") or "",
            professional=bool(re.search(r"^\s+professional: true\s*$",
                                        chunk, re.M))))
    return Education(degrees=degrees, certificates=certs,
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


# --- contact page -----------------------------------------------------------
# Every outbound address on the contact page (form endpoint, calendar,
# Substack) lives in config.yaml. `link` here names the config key; a key that
# is missing or empty raises at build time rather than rendering a dead button.

class ContactForm(BaseModel):
    heading: str
    intro: str
    button: str
    topics: List[str] = Field(default_factory=list)


class ContactCard(BaseModel):
    heading: str
    text: str
    button: str
    link: str                 # key under site.author in config.yaml


class ServiceOffer(BaseModel):   # what I offer; not the academic `Service` above
    tag: str                  # must be a term in data/TAGS.yaml
    label: str
    note: str = ""
    continues: bool = False   # True: the note finishes the sentence, no dash


class ContactPage(BaseModel):
    form: ContactForm
    cards: List[ContactCard] = Field(default_factory=list)
    services: List[ServiceOffer] = Field(default_factory=list)


def load_contact(vocab: TagVocabulary) -> ContactPage:
    text = (ROOT / "data" / "contact.yaml").read_text()

    def scalar(block: str, key: str, default=None):
        m = re.search(rf'^\s*(?:- )?{key}:\s*"(.*)"\s*$', block, re.M)
        if m:
            return m.group(1)
        m = re.search(rf"^\s*(?:- )?{key}:\s*(\S.*?)\s*$", block, re.M)
        return m.group(1) if m else default

    form_block = _block(text, "form")
    form = ContactForm(heading=scalar(form_block, "heading"),
                       intro=scalar(form_block, "intro"),
                       button=scalar(form_block, "button"),
                       topics=_str_list(form_block, "topics"))

    cards = [ContactCard(heading=scalar(c, "heading"), text=scalar(c, "text"),
                         button=scalar(c, "button"), link=scalar(c, "link"))
             for c in re.split(r"\n(?=  - )", _block(text, "cards")) if "heading:" in c]

    services = []
    for s in re.split(r"\n(?=  - )", _block(text, "services")):
        if "tag:" not in s:
            continue
        tag = scalar(s, "tag")
        vocab.validate_tag(tag, context="data/contact.yaml services")
        services.append(ServiceOffer(tag=tag, label=scalar(s, "label"),
                                note=scalar(s, "note", ""),
                                continues=scalar(s, "continues", "false") == "true"))

    return ContactPage(form=form, cards=cards, services=services)


# --- home page --------------------------------------------------------------

class Praise(BaseModel):
    quote: str
    author: str
    author_url: str
    source: str
    work: str
    work_url: str


class HomePage(BaseModel):
    description: str
    bio: str
    portrait_alt: str
    praise: Praise
    testimonials_link: str
    google_site_verification: str
    job_title: str


def load_home() -> HomePage:
    text = (ROOT / "data" / "home.yaml").read_text()

    def scalar(block: str, key: str):
        m = re.search(rf'^\s*{key}:\s*"(.*)"\s*$', block, re.M)
        return m.group(1) if m else None

    bio = re.search(r"^bio: \|\n((?:  .*\n?)+)", text, re.M)
    praise_block = _block(text, "praise")

    return HomePage(
        description=scalar(text, "description"),
        bio=" ".join(l.strip() for l in bio.group(1).splitlines() if l.strip()) if bio else "",
        portrait_alt=scalar(text, "portrait_alt"),
        praise=Praise(quote=scalar(praise_block, "quote"),
                      author=scalar(praise_block, "author"),
                      author_url=scalar(praise_block, "author_url"),
                      source=scalar(praise_block, "source"),
                      work=scalar(praise_block, "work"),
                      work_url=scalar(praise_block, "work_url")),
        testimonials_link=scalar(text, "testimonials_link"),
        google_site_verification=scalar(text, "google_site_verification"),
        job_title=scalar(text, "job_title"),
    )


def count_testimonials() -> int:
    """How many testimonials teaching.html actually shows, counted from the data."""
    text = (ROOT / "data" / "teaching.yaml").read_text()
    return len(re.findall(r"^\s+- quote:", _block(text, "testimonials"), re.M))


# --- teaching: courses and testimonial notes ---------------------------------
# These were rendered as literal HTML inside build_teaching.py while the same
# values sat in teaching.yaml. Fourteen course titles, three group notes.

class CourseGroup(BaseModel):
    institution: str
    dept: str = ""
    courses: List[str] = Field(default_factory=list)


class Courses(BaseModel):
    instructor_of_record: List[CourseGroup] = Field(default_factory=list)
    teaching_assistant: List[CourseGroup] = Field(default_factory=list)


class Role(BaseModel):
    """One employment row. It carries dates and a title, never the work."""
    role: str
    org: str = ""
    start: str
    end: str
    source: str = "self"
    note: str = ""
    work_ids: List[str] = Field(default_factory=list)

    @property
    def dates(self) -> str:
        return f"{self.start} - {self.end}"

    @property
    def needs_input(self) -> bool:
        return "[YOURS" in self.start or "[YOURS" in self.end


class Employment(BaseModel):
    tagline: str = ""
    roles: List[Role] = Field(default_factory=list)


def load_employment(work_ids: Optional[set] = None) -> Employment:
    """Employment history. Every work_id must exist in work.yaml.

    A dangling id is a hard failure rather than a silently dropped bullet: the
    point of referencing work.yaml is that the résumé cannot describe work the
    site does not, and a reference that resolves to nothing breaks that.
    """
    path = EMPLOYMENT_PATH
    text = path.read_text(encoding="utf-8")

    tag = re.search(r'^\s{2}tagline:\s*"(.*)"\s*$', text, re.M)

    roles = []
    block = _block(text, "roles")
    for chunk in re.split(r"\n(?=  - role:)", block):
        if "- role:" not in chunk:
            continue
        def field(name, default=None, chunk=chunk):
            m = re.search(rf'^\s+-?\s*{name}:\s*"(.*?)"\s*$', chunk, re.M)
            if m:
                return m.group(1)
            m = re.search(rf'^\s+-?\s*{name}:\s*(\S.*?)\s*$', chunk, re.M)
            return m.group(1) if m else default

        for required in ("role", "start", "end"):
            if field(required) is None:
                raise ValueError(
                    f"data/employment.yaml: a role is missing '{required}'")

        ids_raw = re.search(r"work_ids:\s*\[([^\]]*)\]", chunk, re.S)
        ids = [i.strip() for i in ids_raw.group(1).split(",")] if ids_raw else []
        ids = [i for i in ids if i]

        if work_ids is not None:
            unknown = [i for i in ids if i not in work_ids]
            if unknown:
                raise ValueError(
                    f"data/employment.yaml: role '{field('role')}' references "
                    f"work ids not in data/work.yaml: {unknown}")

        roles.append(Role(role=field("role"), org=field("org", "") or "",
                          start=field("start"), end=field("end"),
                          source=field("source", "self") or "self",
                          note=field("note", "") or "", work_ids=ids))

    if not roles:
        raise ValueError("data/employment.yaml: no roles found")

    return Employment(tagline=tag.group(1) if tag else "", roles=roles)


def load_courses() -> Courses:
    text = (ROOT / "data" / "teaching.yaml").read_text()
    block = _block(text, "courses")

    def groups(role: str) -> List[CourseGroup]:
        m = re.search(rf"^  {role}:\n((?:    .*\n|\n)*)", block, re.M)
        if not m:
            return []
        out = []
        for chunk in re.split(r"\n(?=    - institution:)", m.group(1)):
            inst = re.search(r'institution: "(.*?)"', chunk)
            if not inst:
                continue
            dept = re.search(r'dept: "(.*?)"', chunk)
            out.append(CourseGroup(
                institution=inst.group(1),
                dept=dept.group(1) if dept else "",
                courses=[c.strip().strip('"') for c in
                         re.findall(r'^\s+- "(.*)"\s*$', chunk, re.M)],
            ))
        return out

    return Courses(instructor_of_record=groups("instructor_of_record"),
                   teaching_assistant=groups("teaching_assistant"))


def load_testimonial_notes() -> Dict[str, str]:
    """The lines introducing each testimonial group, and the postscript.

    Keys: while_students, years_later, postscript. A missing one raises rather
    than falling back to a literal, which is how the hardcoded copies survived.
    """
    text = (ROOT / "data" / "teaching.yaml").read_text()
    block = _block(text, "testimonials")
    out = {}
    for group in ("while_students", "years_later"):
        m = re.search(rf'^  {group}:\n\s+note: "(.*?)"\s*$', block, re.M)
        if not m:
            raise ValueError(f"data/teaching.yaml: testimonials.{group}.note is missing")
        out[group] = m.group(1)
    m = re.search(r'^\s+postscript: "(.*?)"\s*$', block, re.M)
    if not m:
        raise ValueError("data/teaching.yaml: testimonials postscript is missing")
    out["postscript"] = m.group(1)
    return out
