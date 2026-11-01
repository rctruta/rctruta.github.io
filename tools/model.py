"""Rendering adapters for source data validated by portable JSON Schemas."""
import os
import pathlib
import re
from typing import Dict, List, Optional
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


from config_loader import load_config
from contracts import content_document, taxonomy_document, render_tags, read_document

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()
VOCAB_FILENAME = CONFIG["data"]["controlled_vocabulary"]

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
    synonyms: Dict[str, List[str]] = Field(default_factory=dict)  # term -> entry terms

    search_terms: Dict[str, List[str]] = Field(default_factory=dict)
    anchors: Dict[str, str] = Field(default_factory=dict)

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
    """Third-party recognition with attribution, date and source."""
    who: str
    what: str
    date: str
    url: str
    terms: str = ""     # licence or attribution conditions, when they matter
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
    date: Optional[str] = None

    @property
    def one_line(self) -> str:
        """Return the explicit summary or the first description sentence."""
        if self.blurb:
            return self.blurb
        text = " ".join(self.description.strip().split())
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
    data = taxonomy_document()
    concepts = data['concepts']
    return TagVocabulary(
        facets={key: FacetMeta(**value) for key, value in data['facets'].items()},
        kinds={key: KindMeta(**value) for key, value in data['kinds'].items()},
        vocabulary={c['label']: c['facet'] for c in concepts.values()},
        notes={c['label']: c['scope_note'] for c in concepts.values() if 'scope_note' in c},
        synonyms={c['label']: c['alternate_labels'] for c in concepts.values() if c.get('alternate_labels')},
        search_terms={c['label']: c['search_terms'] for c in concepts.values() if c.get('search_terms')},
        anchors={c['label']: c['anchor'] for c in concepts.values()},
    )

def load_work_sections(vocab: TagVocabulary) -> List[WorkSection]:
    data = content_document('work')
    taxonomy = taxonomy_document()
    return [WorkSection(**{**s, 'items': [ProjectItem(**render_tags(i, taxonomy)) for i in s['items']]})
            for s in data['sections']]

def load_articles(vocab: TagVocabulary) -> List[Article]:
    taxonomy = taxonomy_document()
    return sorted([Article(**render_tags(item, taxonomy)) for item in content_document('writing')],
                  key=lambda a: a.date, reverse=True)

def load_appearances(vocab: TagVocabulary) -> List[Appearance]:
    taxonomy = taxonomy_document()
    return sorted([Appearance(**render_tags(item, taxonomy)) for item in content_document('appearances')['items']],
                  key=lambda a: a.date, reverse=True)

class Degree(BaseModel):
    year: Optional[str] = None
    degree: str
    institution: str
    thesis: Optional[str] = None
    advisor: Optional[str] = None
    url: Optional[str] = None          # the deposited copy, if there is one
    isbn: Optional[str] = None


class Certificate(BaseModel):
    """Certificate metadata and optional verification link."""
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
    return Education(**content_document('teaching')['education'])

def load_service() -> Service:
    return Service(**content_document('teaching')['service'])

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
    data = read_document('contact')
    concepts = taxonomy_document()['concepts']
    for item in data['services']:
        if item['tag'] not in concepts:
            raise ValueError(f"contact services reference unknown concept ID {item['tag']!r}")
        item['tag'] = concepts[item['tag']]['label']
    for card in data['cards']:
        if card['link'] not in CONFIG['site']['author']:
            raise ValueError(f"contact card references unknown author field {card['link']!r}")
    return ContactPage(**data)


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
    return HomePage(**read_document('home'))


def count_testimonials() -> int:
    return sum(len(group['items']) for group in content_document('teaching')['testimonials'].values())

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
    """Employment history. Every work_id must exist in work.yaml."""
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
    return Courses(**content_document('teaching')['courses'])

def load_testimonial_notes() -> Dict[str, str]:
    data = content_document('teaching')['testimonials']
    return {'while_students': data['while_students']['note'],
            'years_later': data['years_later']['note'],
            'postscript': data['while_students']['postscript']}
