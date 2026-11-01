"""Portable JSON Schema validation plus mandatory cross-record constraints."""
import copy
import json
import pathlib
from urllib.parse import unquote, urlsplit

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = pathlib.Path(__file__).resolve().parent.parent


class ContractError(ValueError):
    """Invalid source data. Never recover by dropping a record."""


class UniqueKeyLoader(yaml.SafeLoader):
    yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)


for _key, _rules in UniqueKeyLoader.yaml_implicit_resolvers.items():
    UniqueKeyLoader.yaml_implicit_resolvers[_key] = [
        rule for rule in _rules if rule[0] != 'tag:yaml.org,2002:timestamp'
    ]


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ContractError(f'{key_node.start_mark}: mapping keys must be strings')
        if key in result:
            raise ContractError(f'{key_node.start_mark}: duplicate mapping key {key!r}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def parse_yaml(text, source='<input>'):
    try:
        if any(isinstance(token, yaml.tokens.AliasToken) for token in yaml.scan(text)):
            raise ContractError('YAML aliases are not part of the portable document contract')
        return yaml.load(text, Loader=UniqueKeyLoader)
    except (yaml.YAMLError, ContractError) as exc:
        raise ContractError(f'{source}: {exc}') from exc


def norm(value):
    return ' '.join(value.split()).casefold()


def fail(source, path, message):
    raise ContractError(f'{source} → {path}: {message}')


def schema_validate(data, name, source):
    schema = json.loads((ROOT / 'schemas' / f'{name}.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: str(list(e.absolute_path)))
    if errors:
        messages = []
        for err in errors:
            path = '.'.join(str(p) for p in err.absolute_path) or '<root>'
            messages.append(f'{source} → {path}: {err.message}')
        raise ContractError('\n'.join(messages))


def read_document(name):
    if name == 'taxonomy':
        config = parse_yaml((ROOT / 'config.yaml').read_text(), 'config.yaml')
        schema_validate(config, 'config', 'config.yaml')
        filename = config['data']['controlled_vocabulary']
        if pathlib.Path(filename).name != filename or not filename.endswith('.yaml'):
            fail('config.yaml', 'data.controlled_vocabulary', 'expected a YAML filename beneath data/')
    else:
        filename = f'{name}.yaml'
    path = ROOT / 'data' / filename
    data = parse_yaml(path.read_text(), str(path.relative_to(ROOT)))
    schema_validate(data, name, f'data/{filename}')
    return data


def validate_taxonomy(data):
    source = 'data/TAGS.yaml'
    concepts = data['concepts']
    labels, anchors = {}, {}
    for cid, concept in concepts.items():
        if concept['facet'] not in data['facets']:
            fail(source, cid, f"unknown facet {concept['facet']!r}")
        for label in [concept['label']] + concept.get('alternate_labels', []):
            key = norm(label)
            if key in labels:
                fail(source, cid, f'label collision {label!r} with {labels[key]}')
            labels[key] = cid
        anchor = concept['anchor']
        if anchor in anchors or anchor in {'top', *data['facets']} or anchor.startswith('terms-'):
            fail(source, cid, f'anchor collision {anchor!r}')
        anchors[anchor] = cid
        keywords = [norm(x) for x in concept.get('search_terms', [])]
        if len(keywords) != len(set(keywords)):
            fail(source, cid, 'duplicate normalized search term')
        for target in concept.get('related', []):
            if target not in concepts or target == cid:
                fail(source, cid, f'invalid related concept {target!r}')
    return data


def validate_tags(record, taxonomy, source, path):
    for cid in record['tags']:
        if cid not in taxonomy['concepts']:
            fail(source, path + '.tags', f'unknown concept ID {cid!r}')


def validate_reference(url, source, path, external_only=False):
    if any(ch.isspace() for ch in url) or any(ch in url for ch in '\\<>"'):
        fail(source, path, f'malformed URL/path {url!r}')
    parsed = urlsplit(url)
    if parsed.scheme:
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
            fail(source, path, f'unsupported or invalid URL {url!r}')
        try:
            _port = parsed.port
        except ValueError as exc:
            fail(source, path, str(exc))
    else:
        if external_only or parsed.netloc or not parsed.path:
            fail(source, path, f'expected absolute HTTP(S) URL: {url!r}')
        target = (ROOT / unquote(parsed.path)).resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            fail(source, path, f'missing or out-of-root local file {url!r}')


def validate_records(name, data, taxonomy):
    source = f'data/{name}.yaml'
    reserved = {
        'work': {'top'},
        'teaching': {'top', 'philosophy', 'leading', 'product', 'testimonials', 'assignment', 'courses', 'education', 'service'},
        'appearances': {'top', 'talks', 'podcasts', 'guest-host', 'as-guest'},
        'writing': {'top'},
    }
    seen = set(reserved[name])
    if name == 'writing':
        seen.update('y' + record['date'][:4] for record in data)
    if name == 'work':
        records = []
        for section in data['sections']:
            if section['id'] in seen:
                fail(source, section['id'], 'duplicate/reserved section ID')
            seen.add(section['id'])
            records.extend(section['items'])
    elif name == 'teaching':
        records = [data['leading'], data['product'], *data['materials']]
    else:
        records = data['items'] if name == 'appearances' else data
    for i, record in enumerate(records):
        path = f'record[{i}] ({record["id"]})'
        if record['id'] in seen:
            fail(source, path, 'duplicate/reserved ID')
        seen.add(record['id'])
        validate_tags(record, taxonomy, source, path)
        if '[YOURS' in record.get('resume', ''):
            fail(source, path + '.resume', 'unapproved draft is not exportable text')
        for key in ('url', 'slidesUrl', 'videoUrl', 'transcriptUrl'):
            if key in record:
                validate_reference(record[key], source, path + '.' + key)
        for link in record.get('links', []):
            validate_reference(link['url'], source, path + '.links')
        for figure in record.get('figures', []):
            if urlsplit(figure['src']).scheme:
                fail(source, path + '.figures', 'figure must reference a local asset')
            validate_reference(figure['src'], source, path + '.figures')
        for note in record.get('notes', []):
            if 'url' in note:
                validate_reference(note['url'], source, path + '.notes')
        for recognition in record.get('recognition', []):
            validate_reference(recognition['url'], source, path + '.recognition', external_only=True)
            if 'badge' in recognition:
                validate_reference(recognition['badge'], source, path + '.badge', external_only=True)
    return data


def taxonomy_document():
    return validate_taxonomy(read_document('taxonomy'))


def content_document(name):
    return validate_records(name, read_document(name), taxonomy_document())


def render_tags(record, taxonomy):
    """Adapt stable references to labels for existing presentation templates."""
    return {**record, 'tags': [taxonomy['concepts'][cid]['label'] for cid in record['tags']]}


def published(record):
    return record['kind'] == 'talk' or bool(record.get('url'))


def index_records():
    """One validated projection; no filename heuristics or synthetic dates."""
    tax = taxonomy_document()
    records = []

    def add(item, kind, page):
        if kind not in tax['kinds']:
            fail(page, item['id'], f'undeclared kind {kind!r}')
        records.append({'id':item['id'], 'kind':kind, 'page':page,
                        'title':item['title'], 'tags':item['tags'],
                        'date':item.get('date')})

    for section in content_document('work')['sections']:
        for item in section['items']:
            add(item, 'project', 'work.html')
    teaching = content_document('teaching')
    for item in [teaching['leading'], teaching['product']]:
        add(item, 'teaching', 'teaching.html')
    for item in teaching['materials']:
        add(item, 'course material', 'teaching.html')
    for item in content_document('writing'):
        add(item, 'article', 'writing.html')
    for item in content_document('appearances')['items']:
        if published(item):
            add({**item, 'title':f"{item['org']} — {item['title']}"}, item['kind'], 'speaking.html')
    return records


def validate_all():
    taxonomy_document()
    for name in ('work', 'writing', 'appearances', 'teaching'):
        content_document(name)
    index_records()


if __name__ == '__main__':
    validate_all()
    print('Taxonomy, Work, writing, appearances, teaching and index references validated.')
