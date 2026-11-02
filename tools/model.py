"""Load schema-generated models and provide rendering helpers."""
import os
import pathlib
import re

from config_loader import load_config
from contracts import content_document, taxonomy_document, read_document, parse_yaml, schema_validate
from generated.appearances_schema import PortfolioAppearancesDocument
from generated.contact_schema import PortfolioContactDocument
from generated.employment_schema import PortfolioEmploymentDocument, Role as SourceRole
from generated.home_schema import PortfolioHomeDocument
from generated.taxonomy_schema import PortfolioTaxonomyDocument
from generated.teaching_schema import PortfolioTeachingDocument, Education as SourceEducation
from generated.work_schema import PortfolioWorkDocument, Project as SourceProject
from generated.writing_schema import PortfolioWritingDocument

CONFIG = load_config()
_PRIVATE_DIR = os.environ.get("SITE_PRIVATE_DIR")
EMPLOYMENT_PATH = (pathlib.Path(_PRIVATE_DIR) / "employment.yaml"
                   if _PRIVATE_DIR else pathlib.Path("/nonexistent/employment.yaml"))


class TagVocabulary:
    """Display lookups derived from validated taxonomy concepts."""

    def __init__(self, source: PortfolioTaxonomyDocument):
        self.source = source
        self.facets = source.facets
        self.kinds = source.kinds
        self.vocabulary = {c.label: c.facet for c in source.concepts.values()}
        self.notes = {c.label: c.scope_note for c in source.concepts.values() if c.scope_note}
        self.synonyms = {c.label: c.alternate_labels for c in source.concepts.values() if c.alternate_labels}
        self.search_terms = {c.label: c.search_terms for c in source.concepts.values() if c.search_terms}
        self.anchors = {c.label: c.anchor for c in source.concepts.values()}

    def entry_terms(self):
        return {syn: term for term, synonyms in self.synonyms.items() for syn in synonyms}

    def validate_tag(self, tag, context=""):
        if tag not in self.vocabulary:
            raise ValueError(f"Unknown taxonomy label {tag!r} ({context})")


class Education(SourceEducation):
    @property
    def professional_certificates(self):
        return [c for c in self.certificates if c.professional]

    @property
    def course_certificates(self):
        return [c for c in self.certificates if not c.professional]


class ProjectItem(SourceProject):
    @property
    def one_line(self):
        if self.blurb:
            return self.blurb
        text = " ".join(self.description.strip().split())
        text = re.sub(r"^\*\*[^*]+\*\* — ", "", text)
        return re.split(r"(?<=[.!?]) ", text)[0]


class Role(SourceRole):
    @property
    def dates(self):
        return f"{self.start} - {self.end}"

    @property
    def needs_input(self):
        return "[YOURS" in self.start or "[YOURS" in self.end


def load_taxonomy():
    return TagVocabulary(PortfolioTaxonomyDocument.model_validate(taxonomy_document()))


def load_work_sections(vocab):
    document = PortfolioWorkDocument.model_validate(content_document('work'))
    for section in document.sections:
        section.items = [ProjectItem.model_validate(item.model_dump(exclude_unset=True))
                         for item in section.items]
    return document.sections


def load_articles(vocab):
    document = PortfolioWritingDocument.model_validate(content_document('writing'))
    return sorted(document.root, key=lambda a: a.date, reverse=True)


def load_appearances(vocab):
    document = PortfolioAppearancesDocument.model_validate(content_document('appearances'))
    return sorted(document.items, key=lambda a: a.date, reverse=True)


def load_teaching():
    return PortfolioTeachingDocument.model_validate(content_document('teaching'))


def load_education():
    return Education.model_validate(load_teaching().education.model_dump(exclude_unset=True))


def load_service():
    return load_teaching().service


def load_courses():
    return load_teaching().courses


def load_contact(vocab):
    document = PortfolioContactDocument.model_validate(read_document('contact'))
    for service in document.services:
        if service.tag not in vocab.source.concepts:
            raise ValueError(f"Contact service references unknown concept ID {service.tag!r}")
    for card in document.cards:
        if card.link not in CONFIG['site']['author']:
            raise ValueError(f"Contact card references unknown author field {card.link!r}")
    return document


def load_home():
    return PortfolioHomeDocument.model_validate(read_document('home'))


def count_testimonials():
    data = load_teaching().testimonials
    return len(data.while_students.items) + len(data.years_later.items)


def load_testimonial_notes():
    data = load_teaching().testimonials
    return {'while_students': data.while_students.note,
            'years_later': data.years_later.note,
            'postscript': data.while_students.postscript}


def load_employment(work_ids=None):
    data = parse_yaml(EMPLOYMENT_PATH.read_text(encoding='utf-8'), 'private employment.yaml')
    schema_validate(data, 'employment', 'private employment.yaml')
    document = PortfolioEmploymentDocument.model_validate(data)
    document.roles = [Role.model_validate(role.model_dump(exclude_unset=True))
                      for role in document.roles]
    if work_ids is not None:
        for role in document.roles:
            unknown = set(role.work_ids or []) - work_ids
            if unknown:
                raise ValueError(f"Employment references unknown work IDs: {sorted(unknown)}")
    return document
