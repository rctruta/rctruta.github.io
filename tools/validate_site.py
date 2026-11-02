"""Validate public inputs, and optionally every generated local link and index row."""
import argparse
import sys
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from contracts import ROOT, ContractError, index_records, taxonomy_document, validate_all
from config_loader import load_config
from model import load_contact, load_home, load_taxonomy
from search_contract import validate_search


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.refs = []
        self.tag_refs = []
        self.current_term = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
            if tag == 'h3':
                self.current_term = attrs['id']
        for attribute in ('href', 'src'):
            if attrs.get(attribute):
                self.refs.append(attrs[attribute])
                if attribute == 'href':
                    self.tag_refs.append((self.current_term, attrs[attribute]))


def validate_outputs():
    validate_search()
    config = load_config()
    names = ['index.html'] + [n['href'] for n in config['navigation']]
    pages = {}
    for name in names:
        path = ROOT / name
        if not path.is_file():
            raise ContractError(f'{name}: generated page missing')
        page = Page(path.read_text())
        repeated = [key for key, count in Counter(page.ids).items() if count > 1]
        if repeated:
            raise ContractError(f'{name}: duplicate output IDs {repeated}')
        pages[name] = page
    errors = []
    for name, page in pages.items():
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme in {'https', 'http', 'mailto', 'tel'}:
                continue
            if url.scheme or url.netloc or '\\' in ref or any(c in ref for c in '<>"'):
                errors.append(f'{name}: malformed or unsupported reference {ref!r}')
                continue
            target = (ROOT / unquote(url.path)).resolve() if url.path else ROOT / name
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                errors.append(f'{name}: missing local target {ref!r}')
                continue
            if url.fragment and target.suffix == '.html':
                relative = str(target.relative_to(ROOT))
                dest = pages[relative] if relative in pages else Page(target.read_text())
                if unquote(url.fragment) not in dest.ids:
                    errors.append(f'{name}: unresolved fragment {ref!r}')
    expected = Counter()
    taxonomy = taxonomy_document()
    for record in index_records():
        target = f'{record["page"]}#{record["id"]}'
        for cid in record['tags']:
            expected[(taxonomy['concepts'][cid]['anchor'], target)] += 1
        if record['id'] not in pages[record['page']].ids:
            errors.append(f'index: missing content destination {target}')
    content_pages = {'work.html', 'teaching.html', 'writing.html', 'speaking.html'}
    actual = Counter((term, ref) for term, ref in pages['tags.html'].tag_refs
                     if urlsplit(ref).path in content_pages and urlsplit(ref).fragment)
    if actual != expected:
        errors.append(f'index membership mismatch: expected {expected}, actual {actual}')
    if errors:
        raise ContractError('\n'.join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-only', action='store_true', help='Validate inputs before generation; output validation runs after generation.')
    args = parser.parse_args()
    validate_all()
    load_config()
    load_home()
    load_contact(load_taxonomy())
    if not args.sources_only:
        validate_outputs()
    print('Source contracts validated.' if args.sources_only else 'Source contracts, output links, anchors and index membership validated.')


if __name__ == '__main__':
    try:
        main()
    except (ContractError, ValueError) as exc:
        sys.exit(str(exc))
