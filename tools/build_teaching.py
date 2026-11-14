"""Generate teaching.html from validated teaching data and its Jinja template."""
import html
import pathlib

from model import load_teaching
from page import AUTHOR, render_template

ROOT = pathlib.Path(__file__).resolve().parent.parent
teaching = load_teaching()

course_certificates = {}
for certificate in teaching.education.certificates:
    if not certificate.professional:
        course_certificates.setdefault(certificate.issuer or "Other", []).append(certificate)
course_certificate_groups = [
    (issuer, sorted(items, key=lambda item: item.name.lower()))
    for issuer, items in sorted(
        course_certificates.items(), key=lambda pair: (-len(pair[1]), pair[0].lower())
    )
]

service = teaching.service
show_service = bool(service and any((
    service.reviewing, service.outreach, service.outreach_note,
    service.volunteering, service.affiliations,
)))

sections = [
    ("philosophy", "Teaching philosophy"),
    ("leading", "Leading and managing"),
    ("product", "A course is a product"),
    ("testimonials", "Student testimonials"),
    ("assignment", "Sample materials"),
    ("courses", "Courses"),
    ("education", "Education & credentials"),
]
if show_service:
    sections.append(("service", "Service"))
subnav_html = "\n".join(
    f'  <a href="#{anchor}">{html.escape(title)}</a>' for anchor, title in sections
)

doc = render_template(
    template_name="teaching.html",
    title=f"{AUTHOR} — Teaching",
    here_page="teaching",
    generator_name="build_teaching.py",
    source_yaml="teaching.yaml",
    subnav_html=subnav_html,
    teaching=teaching,
    professional_certificates=[c for c in teaching.education.certificates if c.professional],
    course_certificate_groups=course_certificate_groups,
    show_service=show_service,
)

(ROOT / "teaching.html").write_text(doc, encoding="utf-8")
print("teaching.html: generated successfully from data/teaching.yaml")
