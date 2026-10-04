"""Generate teaching.html from data/teaching.yaml.

    python3 tools/build_teaching.py

Generates teaching statement, academic leadership, course operations,
student testimonials, sample materials (PDFs), course catalog, and service.
"""
import html
import pathlib
import re
import sys
from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()
SPEC = ROOT / "data" / "teaching.yaml"

AUTHOR = CONFIG["site"]["author"].get("name", "Author")
SITE_TITLE = CONFIG["site"].get("title", AUTHOR)
SITE_URL = CONFIG["site"].get("url", "")
SITE_IMAGE = CONFIG["site"].get("image", f"{SITE_URL}/assets/photo.jpg")
LICENSE_LABEL = CONFIG["site"].get("copyright_license", "CC BY-NC-SA 4.0")
LICENSE_URL = CONFIG["site"].get("copyright_license_url", "https://creativecommons.org/licenses/by-nc-sa/4.0/")


def slug(tag):
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def format_inline(text):
    if not text:
        return ""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = text.replace("—", "&mdash;").replace("“", "&ldquo;").replace("”", "&rdquo;").replace("’", "&lsquo;").replace("'", "&rsquo;")
    return text


def format_paragraphs(text):
    if not text:
        return ""
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    return "\n\n  ".join(f"<p>{format_inline(b)}</p>" for b in blocks)


def parse_simple_yaml(text):
    """Parse teaching.yaml using zero-dependency block parser."""
    import yaml_like_parser
    return yaml_like_parser.parse(text)


def parse_teaching_yaml(text):
    """Zero-dependency parser tailored to data/teaching.yaml structure."""
    sections = {}
    current_sec = None
    current_key = None
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        trimmed = line.strip()
        indent = len(line) - len(line.lstrip())

        if not trimmed or trimmed.startswith("#"):
            i += 1
            continue

        if indent == 0 and line.endswith(":"):
            current_sec = line[:-1].strip()
            sections[current_sec] = {}
            current_key = None

        elif indent == 2 and current_sec and line.endswith(":"):
            current_key = line[:-1].strip()
            sections[current_sec][current_key] = {}

        i += 1

    return sections


# Alternative lightweight yaml load for teaching.yaml
def load_teaching_spec():
    text = SPEC.read_text(encoding="utf-8")

    def tag_row(tags):
        return '<div class="tags">' + "".join(
            f'<a class="tag" href="tags.html#{slug(t)}">{html.escape(t)}</a>' for t in tags
        ) + '</div>'

    # Extract sections using targeted regex patterns
    # 1. Philosophy
    m_lede = re.search(r"philosophy:\s*\n\s*lede: \|\n(.*?)(?=\n\s*quote:)", text, re.S)
    m_qtext = re.search(r'quote:\s*\n\s*text: "(.*?)"', text)
    m_qcite = re.search(r'cite: "(.*?)"', text)
    m_princ = re.search(r"principles: \|\n(.*?)(?=\n\nleading:|\nleading:)", text, re.S)

    lede_html = f"<p>{format_inline(m_lede.group(1).strip())}</p>" if m_lede else ""
    quote_html = (
        f'  <blockquote class="praise">\n'
        f'    <p>&ldquo;{html.escape(m_qtext.group(1))}&rdquo;</p>\n'
        f'    <cite>{html.escape(m_qcite.group(1))}</cite>\n'
        f'  </blockquote>'
    ) if m_qtext and m_qcite else ""

    princ_html = format_paragraphs(m_princ.group(1)) if m_princ else ""

    phil_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="philosophy">Teaching</h2>\n\n'
        f'  {lede_html}\n\n'
        f'{quote_html}\n\n'
        f'  {princ_html}\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 2. Leading
    m_lead_id = re.search(r"leading:\s*\n\s*id: ([\w-]+)", text)
    m_lead_title = re.search(r'leading:.*?title: "(.*?)"', text, re.S)
    m_lead_tags = re.search(r"leading:.*?tags: \[(.*?)\]", text, re.S)
    m_lead_desc = re.search(r"leading:.*?description: \|\n(.*?)(?=\n\nproduct:|\nproduct:)", text, re.S)

    lead_id = m_lead_id.group(1) if m_lead_id else "academic-leadership"
    lead_title = m_lead_title.group(1) if m_lead_title else "Academic leadership & TA management"
    lead_tags = [t.strip() for t in m_lead_tags.group(1).split(",")] if m_lead_tags else []
    lead_desc = format_paragraphs(m_lead_desc.group(1)) if m_lead_desc else ""

    leading_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="leading">Leading and managing</h2>\n\n'
        f'  <div class="proj" id="{lead_id}">\n'
        f'    <h3>{html.escape(lead_title)}</h3>\n'
        f'    {lead_desc}\n'
        f'    {tag_row(lead_tags)}\n'
        f'  </div>\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 3. Product
    m_prod_id = re.search(r"product:\s*\n\s*id: ([\w-]+)", text)
    m_prod_title = re.search(r'product:.*?title: "(.*?)"', text, re.S)
    m_prod_tags = re.search(r"product:.*?tags: \[(.*?)\]", text, re.S)
    m_prod_intro = re.search(r'product:.*?intro: "(.*?)"', text, re.S)
    m_prod_outro = re.search(r'product:.*?outro: "(.*?)"', text, re.S)
    m_prod_hl = re.search(r"highlights:\s*\n(.*?)(?=\n\s*outro:)", text, re.S)

    prod_id = m_prod_id.group(1) if m_prod_id else "course-product-design"
    prod_title = m_prod_title.group(1) if m_prod_title else "A course is a product — course operations & engineering"
    prod_tags = [t.strip() for t in m_prod_tags.group(1).split(",")] if m_prod_tags else []
    prod_intro = m_prod_intro.group(1) if m_prod_intro else ""
    prod_outro = m_prod_outro.group(1) if m_prod_outro else ""

    hl_items = []
    if m_prod_hl:
        for line in m_prod_hl.group(1).splitlines():
            line_str = line.strip()
            if line_str.startswith("- "):
                clean_text = line_str[2:].strip().strip('"')
                hl_items.append(f'      <li>{format_inline(clean_text)}</li>')
    hl_html = "\n".join(hl_items)

    product_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="product">A course is a product</h2>\n\n'
        f'  <div class="proj" id="{prod_id}">\n'
        f'    <h3>{html.escape(prod_title)}</h3>\n'
        f'    <p>{format_inline(prod_intro)}</p>\n\n'
        f'    <ul class="courses">\n{hl_html}\n    </ul>\n\n'
        f'    <p>{format_inline(prod_outro)}</p>\n'
        f'    {tag_row(prod_tags)}\n'
        f'  </div>\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 4. Testimonials
    m_test_while = re.findall(r'quote: "(.*?)"\s*\n\s*cite: "(.*?)"', text[text.find("while_students:"):text.find("years_later:")], re.S)
    m_test_years = re.findall(r'quote: "(.*?)"\s*\n\s*cite: "(.*?)"', text[text.find("years_later:"):text.find("materials:")], re.S)

    while_html = "\n\n".join(
        f'  <blockquote class="praise">\n'
        f'    <p>&ldquo;{html.escape(q)}&rdquo;</p>\n'
        f'    <cite>{html.escape(c)}</cite>\n'
        f'  </blockquote>'
        for q, c in m_test_while
    )

    years_html = "\n\n".join(
        f'  <blockquote class="praise">\n'
        f'    <p>&ldquo;{html.escape(q)}&rdquo;</p>\n'
        f'    <cite>{html.escape(c)}</cite>\n'
        f'  </blockquote>'
        for q, c in m_test_years
    )

    postscript = "At the end of one course, a group of around ten students wrote to the department unprompted to nominate me for a teaching award. One of them asked my permission first, in case I would rather they didn't."

    testimonials_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="testimonials">Student testimonials</h2>\n\n'
        f'  <h3>While they were students</h3>\n\n'
        f'  <p>From student emails. Quoted with first names only, or anonymously.</p>\n\n'
        f'{while_html}\n\n'
        f'  <p>{postscript}</p>\n\n'
        f'  <h3>Years later</h3>\n\n'
        f'  <p>Written publicly, under their own names, by students who took my courses and then went on to build things.</p>\n\n'
        f'{years_html}\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 5. Materials
    mat_blocks = []
    m_mat_all = re.findall(r'- id: ([\w-]+)\s*\n\s*title: "(.*?)"\s*\n\s*activity:.*?\n\s*url: "(.*?)"\s*\n\s*meta: "(.*?)"\s*\n\s*tags: \[(.*?)\].*?description: \|\n(.*?)(?=\n  - id:|\ncourses:|\n\ncourses:)', text, re.S)

    for mid, mtitle, murl, mmeta, mtags_str, mdesc in m_mat_all:
        mtags = [t.strip() for t in mtags_str.split(",")]
        desc_formatted = format_paragraphs(mdesc)
        mat_blocks.append(
            f'  <div class="proj" id="{mid}">\n'
            f'  <h3><a href="{murl}">{html.escape(mtitle)}</a>\n'
            f'  <span class="meta">{html.escape(mmeta)}</span></h3>\n\n'
            f'  {desc_formatted}\n\n'
            f'  {tag_row(mtags)}\n'
            f'  </div>'
        )

    materials_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="assignment">Sample materials</h2>\n\n'
        f'{chr(10).join(mat_blocks)}\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 6. Courses
    courses_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="courses">Courses</h2>\n\n'
        f'  <p class="role">Instructor of record</p>\n\n'
        f'  <p class="inst">University of Toronto <span class="dept">&mdash; Computer Science</span></p>\n'
        f'  <ul class="courses">\n'
        f'    <li>Introduction to Databases</li>\n'
        f'    <li>Database System Technology</li>\n'
        f'    <li>Programming on the Web</li>\n'
        f'    <li>Software Engineering I</li>\n'
        f'    <li>Design Project &mdash; student supervisor</li>\n'
        f'    <li>Project Course in Computer Science &mdash; student supervisor</li>\n'
        f'  </ul>\n\n'
        f'  <p class="inst">&ldquo;Iuliu Hațieganu&rdquo; University of Medicine and Pharmacy, Romania\n'
        f'  <span class="dept">&mdash; Biostatistics and Computer Science</span></p>\n'
        f'  <ul class="courses">\n'
        f'    <li>Design and Implementation of Medical Information Systems</li>\n'
        f'  </ul>\n\n'
        f'  <p class="role">Teaching assistant</p>\n\n'
        f'  <p class="inst">University of Toronto <span class="dept">&mdash; Computer Science</span></p>\n'
        f'  <ul class="courses">\n'
        f'    <li>Introduction to Databases</li>\n'
        f'    <li>Software Design</li>\n'
        f'    <li>Programming on the Web</li>\n'
        f'    <li>Data Management Systems</li>\n'
        f'    <li>Principles of Programming Languages</li>\n'
        f'    <li>File Structures and Data Management</li>\n'
        f'  </ul>\n\n'
        f'  <p class="inst">&ldquo;Iuliu Hațieganu&rdquo; University of Medicine and Pharmacy, Romania</p>\n'
        f'  <ul class="courses">\n'
        f'    <li>Introduction to Biomedical Informatics and Biostatistics</li>\n'
        f'    <li>Design and Implementation of Medical Information Systems</li>\n'
        f'  </ul>\n\n'
        f'  <p class="inst">&ldquo;Babeș-Bolyai&rdquo; University, Romania\n'
        f'  <span class="dept">&mdash; Computer Science</span></p>\n'
        f'  <ul class="courses">\n'
        f'    <li>Introduction to Computer Science</li>\n'
        f'    <li>Office Automation</li>\n'
        f'    <li>Graduation Project &mdash; student supervisor</li>\n'
        f'  </ul>\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 7. Education & Credentials
    education_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="education">Education &amp; credentials</h2>\n\n'
        f'  <h3>Degrees</h3>\n'
        f'  <ul class="courses">\n'
        f'    <li><strong>M.Sc. Computer Science</strong> &mdash; University of Toronto, 2004. Thesis:\n'
        f'    <em>Structural and Semantic Query Optimization in XQuery</em>, supervised by Alberto O. Mendelzon</li>\n'
        f'    <li><strong>M.Sc. Computer Science</strong> &mdash; &ldquo;Babeș-Bolyai&rdquo; University, Romania, 1997.\n'
        f'    Thesis: <em>Multimedia Synchronization</em></li>\n'
        f'    <li><strong>B.Sc. Mathematics &amp; Computer Science</strong> &mdash; &ldquo;Babeș-Bolyai&rdquo; University, 1996</li>\n'
        f'  </ul>\n\n'
        f'  <h3>Certificates</h3>\n'
        f'  <ul class="courses">\n'
        f'    <li>Business Analyst Certificate &mdash; University of Waterloo, 2012</li>\n'
        f'    <li>Teaching Certificate &mdash; &ldquo;Babeș-Bolyai&rdquo; University: psychology, pedagogy, methodology, practicum</li>\n'
        f'    <li>Neo4j Certified Professional</li>\n'
        f'    <li>Applied Data Science: Leveraging AI for Effective Decision Making &mdash; MIT Professional Education, 2023</li>\n'
        f'    <li>Large Language Models &mdash; Databricks / edX, 2023</li>\n'
        f'    <li>Delivering a Polished Classroom Presentation &mdash; Office of Teaching Advancement, University of Toronto</li>\n'
        f'  </ul>\n\n'
        f'  <h3>Honours</h3>\n'
        f'  <ul class="courses">\n'
        f'    <li>Nominee, University of Toronto Scarborough Teaching Award</li>\n'
        f'    <li>Recipient, Grace Hopper Celebration of Women in Computing Scholarship</li>\n'
        f'    <li>Recipient, International Recruitment Award, University of Toronto</li>\n'
        f'    <li>Recipient, &ldquo;Babeș-Bolyai&rdquo; University Honours Scholarship, Romania</li>\n'
        f'  </ul>\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    # 8. Service
    service_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="service">Service</h2>\n\n'
        f'  <h3>Reviewing and editorial</h3>\n'
        f'  <ul class="courses">\n'
        f'    <li>Reviewer, <em>Journal of Information Systems Education</em> (2008&ndash;2011)</li>\n'
        f'    <li>Reviewer, Data Warehousing and Knowledge Discovery (DaWaK)</li>\n'
        f'    <li>Peer reviewer, Computer and Mathematical Sciences, U of T Scarborough</li>\n'
        f'    <li>Notes editing, <em>Elements of Finite Model Theory</em>, Leonid Libkin (Springer)</li>\n'
        f'  </ul>\n\n'
        f'  <h3>Outreach and mentoring</h3>\n'
        f'  <ul class="courses">\n'
        f'    <li>Group leader, Gr8 Designs for Gr8 Girls, University of Toronto</li>\n'
        f'    <li>Mentoring female students in computer science, throughout my teaching</li>\n'
        f'    <li>Recipient, Grace Hopper Celebration of Women in Computing Scholarship</li>\n'
        f'    <li>Invited lecture, Computing Insights, University of Toronto</li>\n'
        f'  </ul>\n\n'
        f'  <p>Encouraging women in computing was not an add-on. Female enrolment in Canadian computer\n'
        f'  science and engineering programs is small, and students told me directly that having a\n'
        f'  female instructor mattered, and that they had felt threatened by male peers. That is a\n'
        f'  thing a teacher can do something about from inside a classroom.</p>\n\n'
        f'  <h3>Professional affiliations</h3>\n'
        f'  <ul class="courses">\n'
        f'    <li>Canadian Association of University Teachers</li>\n'
        f'    <li>Computer Science Teachers Association</li>\n'
        f'    <li>Society for Teaching and Learning in Higher Education</li>\n'
        f'    <li>ACM Special Interest Group on Management of Data</li>\n'
        f'  </ul>\n\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

    return f"{phil_section}\n\n{leading_section}\n\n{product_section}\n\n{testimonials_section}\n\n{materials_section}\n\n{courses_section}\n\n{education_section}\n\n{service_section}"


# The sub-nav is derived from the headings it points at. Hard-coding it meant
# the nav said "Philosophy" while the heading said "Teaching" — two sources for
# one label, which is the thing this pipeline exists to prevent.
def make_subnav(html_body):
    links = re.findall(r'<h2 id="([a-z-]+)">(.*?)</h2>', html_body, re.S)
    items = "\n".join(
        f'  <a href="#{hid}">{re.sub(r"<[^>]+>", "", label).strip()}</a>'
        for hid, label in links
    )
    return f'<div class="wrap">\n{items}\n</div>'


body = load_teaching_spec()
subnav = make_subnav(body)

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(AUTHOR)} &mdash; Teaching</title>
<meta name="description" content="Teaching: philosophy, courses taught, and academic service.">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
<meta property="og:type" content="website">
<meta property="og:title" content="Teaching &mdash; {html.escape(AUTHOR)}">
<meta property="og:description" content="Teaching philosophy, course design, student testimonials, materials, and academic leadership.">
<meta property="og:image" content="{html.escape(SITE_IMAGE)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Teaching &mdash; {html.escape(AUTHOR)}">
<meta name="twitter:description" content="Teaching philosophy, course design, student testimonials, materials, and academic leadership.">
<meta name="twitter:image" content="{html.escape(SITE_IMAGE)}">
<link rel="stylesheet" href="style.css"></head><body>
<!-- Generated by tools/build_teaching.py from data/teaching.yaml. Do not edit by hand. -->
<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html">{html.escape(AUTHOR)}</a>
  <span class="navlinks">
    <a href="work.html">Work</a>
    <a href="teaching.html" class="here">Teaching</a>
    <a href="speaking.html">Speaking</a>
    <a href="writing.html">Writing</a>
    <a href="contact.html">Contact</a>
  </span>
</div></nav>
<nav class="subnav" id="top">{subnav}</nav>

{body}

<footer><div class="wrap"><span>&copy; 2025&ndash;2026 {html.escape(AUTHOR)} &middot; <a href="{html.escape(LICENSE_URL)}" rel="license">{html.escape(LICENSE_LABEL)}</a> &middot; <a href="contact.html">Contact</a></span></div></footer>
</body></html>
"""

(ROOT / "teaching.html").write_text(doc, encoding="utf-8")
print("teaching.html: generated successfully from data/teaching.yaml")
