"""Generate teaching.html from data/teaching.yaml using Jinja2 templates."""
import html
import pathlib
import re
from model import load_education, load_service, load_courses
from contracts import content_document, taxonomy_document, render_tags
from page import render_template, format_inline, format_blocks, render_tag_chips, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "data" / "teaching.yaml"


def load_teaching_html_sections():
    data = content_document('teaching')
    taxonomy = taxonomy_document()

    def section(anchor, title, body):
        return (f'<section><div class="wrap"><h2 id="{anchor}">{title}</h2>\n'
                f'{body}\n<p class="totop"><a href="#top">&uarr; Top</a></p></div></section>')

    def quote(text, cite):
        return (f'<blockquote class="praise"><p>&ldquo;{html.escape(text)}&rdquo;</p>'
                f'<cite>{html.escape(cite)}</cite></blockquote>')

    philosophy = data['philosophy']
    phil_section = section('philosophy', 'Teaching philosophy',
        f"<p>{format_inline(philosophy['lede'].strip())}</p>"
        + quote(philosophy['quote']['text'], philosophy['quote']['cite'])
        + format_blocks(philosophy['principles']))

    leading = render_tags(data['leading'], taxonomy)
    leading_section = section('leading', 'Leading and managing',
        f'<div class="proj" id="{leading["id"]}"><h3>{html.escape(leading["title"])}</h3>'
        + format_blocks(leading['description']) + render_tag_chips(leading['tags']) + '</div>')

    product = render_tags(data['product'], taxonomy)
    highlights = ''.join(f'<li>{format_inline(item)}</li>' for item in product['highlights'])
    product_section = section('product', 'A course is a product',
        f'<div class="proj" id="{product["id"]}"><h3>{html.escape(product["title"])}</h3>'
        + f'<p>{format_inline(product["intro"])}</p><ul class="courses">{highlights}</ul>'
        + f'<p>{format_inline(product["outro"])}</p>' + render_tag_chips(product['tags']) + '</div>')

    testimonial_body = []
    for key, label in [('while_students', 'While they were students'), ('years_later', 'Years later')]:
        group = data['testimonials'][key]
        testimonial_body.append(f'<h3>{label}</h3><p>{format_inline(group["note"])}</p>')
        testimonial_body.extend(quote(item['quote'], item['cite']) for item in group['items'])
        if 'postscript' in group:
            testimonial_body.append(f'<p>{format_inline(group["postscript"])}</p>')
    testimonials_section = section('testimonials', 'Student testimonials', '\n'.join(testimonial_body))

    materials = []
    for item in data['materials']:
        item = render_tags(item, taxonomy)
        materials.append(f'<div class="proj" id="{item["id"]}">'
            + f'<h3><a href="{html.escape(item["url"], quote=True)}">{html.escape(item["title"])}</a>'
            + f' <span class="meta">{html.escape(item["meta"])}</span></h3>'
            + format_blocks(item['description']) + render_tag_chips(item['tags']) + '</div>')
    materials_section = section('assignment', 'Sample materials', '\n'.join(materials))

    courses = load_courses()

    def course_group(g):
        dept = f' <span class="dept">&mdash; {html.escape(g.dept)}</span>' if g.dept else ""
        items = "".join(f'    <li>{format_inline(c)}</li>\n' for c in g.courses)
        return (f'  <p class="inst">{format_inline(g.institution)}{dept}</p>\n'
                f'  <ul class="courses">\n{items}  </ul>\n\n')

    courses_section = (
        '<section><div class="wrap">\n'
        '  <h2 id="courses">Courses</h2>\n\n'
        '  <p class="role">Instructor of record</p>\n\n'
        + "".join(course_group(g) for g in courses.instructor_of_record)
        + '  <p class="role">Teaching assistant</p>\n\n'
        + "".join(course_group(g) for g in courses.teaching_assistant)
        + '  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        '</div></section>'
    )

    edu, svc = load_education(), load_service()

    def degree_line(d):
        s = f'<strong>{html.escape(d.degree)}</strong> &mdash; {html.escape(d.institution)}'
        if d.thesis:
            title = f'<em>{html.escape(d.thesis)}</em>'
            if d.url:
                title = f'<a href="{d.url}">{title}</a>'
            s += f'. Thesis: {title}'
            if d.advisor:
                s += f', supervised by {html.escape(d.advisor)}'
            if d.isbn:
                s += f' <span class="meta">ISBN {html.escape(d.isbn)}</span>'
        return s

    def ul(items, render=html.escape):
        return ('  <ul class="courses">\n'
                + "".join(f'    <li>{render(i)}</li>\n' for i in items)
                + '  </ul>\n\n')

    def cert_line(c):
        """A certificate, linked to its proof when the issuer provides one."""
        text = format_inline(c.name)
        if not c.url:
            return text
        meta = ""
        if c.expires:
            meta = f' <span class="meta">expires {html.escape(c.expires)}</span>'
        if "<a " in text:
            return (f'{text} <a href="{c.url}" target="_blank" rel="noopener" '
                    f'class="meta">verify</a>{meta}')
        return (f'<a href="{c.url}" target="_blank" rel="noopener">{text}</a>'
                f'{meta}')

    def course_certificates_html(courses):
        """Render course certificates grouped by issuer."""
        if not courses:
            return ""
        by_issuer = {}
        for c in courses:
            by_issuer.setdefault(c.issuer or "Other", []).append(c)
        order = sorted(by_issuer, key=lambda k: (-len(by_issuer[k]), k.lower()))

        out = ['  <h3>Courses</h3>\n']
        for issuer in order:
            items = sorted(by_issuer[issuer], key=lambda c: c.name.lower())
            out.append(f'  <h4>{html.escape(issuer)}</h4>\n')
            out.append('  <ul class="courses">\n')
            for c in items:
                name = html.escape(c.name)
                body = (f'<a href="{c.url}" target="_blank" rel="noopener">{name}</a>'
                        if c.url else name)
                if c.date:
                    body += f' <span class="meta">{html.escape(c.date)}</span>'
                out.append(f'    <li>{body}</li>\n')
            out.append('  </ul>\n\n')
        return "".join(out)

    education_section = (
        '<section><div class="wrap">\n'
        '  <h2 id="education">Education &amp; credentials</h2>\n\n'
        '  <h3>Degrees</h3>\n' + ul(edu.degrees, degree_line)
        + '  <h3>Certificates</h3>\n' + ul(edu.professional_certificates, cert_line)
        + course_certificates_html(edu.course_certificates)
        + '  <h3>Honours</h3>\n' + ul(edu.honours, format_inline)
        + '  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        '</div></section>'
    )

    service_section = (
        '<section><div class="wrap">\n'
        '  <h2 id="service">Service</h2>\n\n'
        '  <h3>Reviewing and editorial</h3>\n' + ul(svc.reviewing, format_inline)
        + '  <h3>Outreach</h3>\n' + ul(svc.outreach, format_inline)
        + (f'  <p class="sub small">{format_inline(svc.outreach_note)}</p>\n\n' if svc.outreach_note else "")
        + (('  <h3>Volunteering</h3>\n' + ul(svc.volunteering, format_inline)) if svc.volunteering else "")
        + '  <h3>Affiliations</h3>\n' + ul(svc.affiliations, format_inline)
        + '  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        '</div></section>'
    )

    return f"{phil_section}\n\n{leading_section}\n\n{product_section}\n\n{testimonials_section}\n\n{materials_section}\n\n{courses_section}\n\n{education_section}\n\n{service_section}"


body_html = load_teaching_html_sections()
subnav_html = "\n".join(
    f'  <a href="#{hid}">{re.sub(r"<[^>]+>", "", label).strip()}</a>'
    for hid, label in re.findall(r'<h2 id="([a-z0-9-]+)">(.*?)</h2>', body_html, re.S)
)

doc = render_template(
    template_name="teaching.html",
    title=f"{AUTHOR} — Teaching",
    here_page="teaching",
    generator_name="build_teaching.py",
    source_yaml="teaching.yaml",
    subnav_html=subnav_html,
    body_html=body_html
)

(ROOT / "teaching.html").write_text(doc, encoding="utf-8")
print("teaching.html: generated successfully from data/teaching.yaml")
