"""Generate teaching.html from data/teaching.yaml.

    python3 tools/build_teaching.py
"""
import html
import pathlib
import model
import re
from page import render_tag_chips, render_page_shell, format_inline, format_blocks, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "data" / "teaching.yaml"


def load_teaching_html_sections():
    text = SPEC.read_text(encoding="utf-8")

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

    princ_html = format_blocks(m_princ.group(1)) if m_princ else ""

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
    lead_desc = format_blocks(m_lead_desc.group(1)) if m_lead_desc else ""

    leading_section = (
        f'<section><div class="wrap">\n'
        f'  <h2 id="leading">Leading and managing</h2>\n\n'
        f'  <div class="proj" id="{lead_id}">\n'
        f'    <h3>{html.escape(lead_title)}</h3>\n'
        f'    {lead_desc}\n'
        f'    {render_tag_chips(lead_tags)}\n'
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
        f'    {render_tag_chips(prod_tags)}\n'
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
        desc_formatted = format_blocks(mdesc)
        mat_blocks.append(
            f'  <div class="proj" id="{mid}">\n'
            f'  <h3><a href="{murl}">{html.escape(mtitle)}</a>\n'
            f'  <span class="meta">{html.escape(mmeta)}</span></h3>\n\n'
            f'  {desc_formatted}\n\n'
            f'  {render_tag_chips(mtags)}\n'
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

    # 7 & 8. Education and Service — rendered from data/teaching.yaml via
    # validated models. These were previously hardcoded here, which is why
    # editing the data had no effect and one honour rendered twice.
    edu = model.load_education()
    svc = model.load_service()

    def ul(items):
        return ('  <ul class="courses">\n'
                + "".join(f'    <li>{format_inline(i)}</li>\n' for i in items)
                + '  </ul>\n\n')

    def degree_line(d):
        s = f'<strong>{html.escape(d.degree)}</strong> &mdash; {html.escape(d.institution)}'
        if d.thesis:
            title = f'<em>{html.escape(d.thesis)}</em>'
            if d.url:
                title = f'<a href="{d.url}">{title}</a>'
            s += f'. Thesis: {title}'
            if d.advisor:
                s += f', supervised by {html.escape(d.advisor)}'
        return s

    education_section = (
        '<section><div class="wrap">\n'
        '  <h2 id="education">Education &amp; credentials</h2>\n\n'
        '  <h3>Degrees</h3>\n'
        + '  <ul class="courses">\n'
        + "".join(f'    <li>{degree_line(d)}</li>\n' for d in edu.degrees)
        + '  </ul>\n\n'
        + '  <h3>Certificates</h3>\n' + ul(edu.certificates)
        + '  <h3>Honours</h3>\n' + ul(edu.honours)
        + '  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        + '</div></section>'
    )

    service_section = (
        '<section><div class="wrap">\n'
        '  <h2 id="service">Service</h2>\n\n'
        '  <h3>Reviewing and editorial</h3>\n' + ul(svc.reviewing)
        + '  <h3>Outreach and mentoring</h3>\n' + ul(svc.outreach)
        + (f'  <p>{format_inline(svc.outreach_note)}</p>\n\n' if svc.outreach_note else '')
        + ('  <h3>Volunteering</h3>\n' + ul(svc.volunteering) if svc.volunteering else '')
        + '  <h3>Professional affiliations</h3>\n' + ul(svc.affiliations)
        + '  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        + '</div></section>'
    )

    return f"{phil_section}\n\n{leading_section}\n\n{product_section}\n\n{testimonials_section}\n\n{materials_section}\n\n{courses_section}\n\n{education_section}\n\n{service_section}"


body_html = load_teaching_html_sections()
# Derived from the headings it points at. A hardcoded list meant the nav read
# "Philosophy" over a heading reading "Teaching" — two labels for one thing, and
# it came back the moment this file was refactored. tools/test_tools.py now
# fails the build if they ever diverge again.
subnav_html = "\n".join(
    f'  <a href="#{hid}">{re.sub(r"<[^>]+>", "", label).strip()}</a>'
    for hid, label in re.findall(r'<h2 id="([a-z0-9-]+)">(.*?)</h2>', body_html, re.S)
)

title = f"{AUTHOR} — Teaching"
description = "Teaching philosophy, course design, student testimonials, materials, and academic leadership."

doc = render_page_shell(
    title=title,
    description=description,
    here_page="teaching",
    subnav_html=subnav_html,
    body_html=body_html,
    generator_name="build_teaching.py",
    source_yaml="teaching.yaml"
)

(ROOT / "teaching.html").write_text(doc, encoding="utf-8")
print("teaching.html: generated successfully from data/teaching.yaml")
