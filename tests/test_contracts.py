"""Exercise rejected input at the publication boundary, not only happy paths."""
import copy
import unittest
from unittest.mock import patch

from contracts import (ContractError, content_document, index_records, parse_yaml,
                       published, read_document, schema_validate, taxonomy_document,
                       validate_records, validate_taxonomy)
from model import load_articles, load_taxonomy
import validate_site


class TestContracts(unittest.TestCase):
    def setUp(self):
        self.taxonomy = taxonomy_document()

    def test_nested_duplicate_yaml_key_fails(self):
        with self.assertRaisesRegex(ContractError, 'duplicate mapping key'):
            parse_yaml('outer:\n  name: first\n  name: second\n', 'fixture.yaml')

    def test_yaml_alias_is_rejected(self):
        with self.assertRaisesRegex(ContractError, 'aliases'):
            parse_yaml('a: &shared [one]\nb: *shared\n')

    def test_yaml_multiline_and_escaping_survive(self):
        data = parse_yaml('note: >-\n  a long\n  note\nlink: "<a href=\\"https://example.com\\">link</a>"\n')
        self.assertEqual('a long note', data['note'])
        self.assertIn('href="https://example.com"', data['link'])

    def test_missing_article_title_fails_instead_of_disappearing(self):
        data = read_document('writing')
        del data[0]['title']
        with self.assertRaisesRegex(ContractError, "title.*required"):
            schema_validate(data, 'writing', 'fixture.yaml')
        real_reader = read_document
        def altered(name):
            if name == 'writing':
                schema_validate(data, name, 'fixture.yaml')
                return data
            return real_reader(name)
        with patch('contracts.read_document', side_effect=altered):
            with self.assertRaises(ContractError):
                load_articles(load_taxonomy())

    def test_unknown_field_rejected(self):
        data = read_document('work')
        data['sections'][0]['items'][0]['titel'] = 'typo'
        with self.assertRaisesRegex(ContractError, 'titel'):
            schema_validate(data, 'work', 'fixture.yaml')

    def test_wrong_scalar_type_rejected(self):
        data = read_document('work')
        data['sections'][0]['items'][0]['title'] = 123
        with self.assertRaises(ContractError):
            schema_validate(data, 'work', 'fixture.yaml')

    def test_unknown_concept_reference_fails(self):
        data = read_document('work')
        data['sections'][0]['items'][0]['tags'] = ['unregistered']
        with self.assertRaisesRegex(ContractError, 'unknown concept ID'):
            validate_records('work', data, self.taxonomy)

    def test_duplicate_and_reserved_ids_fail(self):
        for value in ('top', 'data-engineering'):
            with self.subTest(value=value):
                data = read_document('work')
                data['sections'][0]['items'][0]['id'] = value
                with self.assertRaisesRegex(ContractError, 'duplicate/reserved'):
                    validate_records('work', data, self.taxonomy)

    def test_duplicate_tag_fails(self):
        data = read_document('work')
        item = data['sections'][0]['items'][0]
        item['tags'].append(item['tags'][0])
        with self.assertRaises(ContractError):
            schema_validate(data, 'work', 'fixture.yaml')

    def test_normalized_label_collision_fails(self):
        data = copy.deepcopy(self.taxonomy)
        data['concepts']['python']['alternate_labels'] = ['  DATA   MODELING ']
        with self.assertRaisesRegex(ContractError, 'label collision'):
            validate_taxonomy(data)

    def test_unknown_facet_and_relation_fail(self):
        for key, value in [('facet', 'unregistered'), ('related', ['unregistered'])]:
            with self.subTest(key=key):
                data = copy.deepcopy(self.taxonomy)
                data['concepts']['python'][key] = value
                with self.assertRaises(ContractError):
                    validate_taxonomy(data)

    def test_anchor_collision_fails(self):
        data = copy.deepcopy(self.taxonomy)
        data['concepts']['python']['anchor'] = 'sql'
        with self.assertRaisesRegex(ContractError, 'anchor collision'):
            validate_taxonomy(data)

    def test_label_change_does_not_change_identity_or_anchor(self):
        data = copy.deepcopy(self.taxonomy)
        data['concepts']['python']['label'] = 'Python language'
        validate_taxonomy(data)
        self.assertEqual('python', data['concepts']['python']['anchor'])
        self.assertIn('python', data['concepts'])

    def test_impossible_date_rejected(self):
        data = read_document('appearances')
        data['items'][0]['date'] = '2026-02-30'
        with self.assertRaises(ContractError):
            schema_validate(data, 'appearances', 'fixture.yaml')

    def test_unpublished_record_validated_before_filtering(self):
        data = read_document('appearances')
        item = next(item for item in data['items'] if item['kind'] == 'podcast')
        item.pop('url', None)
        self.assertFalse(published(item))
        item['tags'] = ['unregistered']
        with self.assertRaises(ContractError):
            validate_records('appearances', data, self.taxonomy)

    def test_draft_resume_rejected(self):
        data = read_document('work')
        data['sections'][0]['items'][0]['resume'] = '[YOURS: draft]'
        with self.assertRaisesRegex(ContractError, 'unapproved draft'):
            validate_records('work', data, self.taxonomy)

    def test_empty_note_and_half_link_rejected(self):
        for note in ({}, {'label': 'incomplete'}):
            with self.subTest(note=note):
                data = read_document('work')
                data['sections'][0]['items'][0]['notes'] = [note]
                with self.assertRaises(ContractError):
                    schema_validate(data, 'work', 'fixture.yaml')

    def test_missing_asset_and_unsafe_link_rejected(self):
        for url in ('assets/does-not-exist.pdf', 'javascript:alert(1)', '../outside.txt'):
            with self.subTest(url=url):
                data = read_document('work')
                data['sections'][0]['items'][0]['links'] = [{'text':'test', 'url':url}]
                with self.assertRaises(ContractError):
                    validate_records('work', data, self.taxonomy)

    def test_index_has_no_synthetic_work_or_teaching_dates(self):
        records = index_records()
        self.assertEqual(20, sum(r['kind'] == 'project' for r in records))
        self.assertTrue(all(r['date'] is None for r in records if r['page'] in {'work.html','teaching.html'}))

    def test_real_folded_note_and_caption_are_parsed(self):
        appearances = content_document('appearances')
        note = next(i['note'] for i in appearances['items'] if i['id'] == 'joe-reis-2026')
        self.assertIn('Second recording;', note)
        work = content_document('work')
        item = next(i for s in work['sections'] for i in s['items'] if i['id'] == 'lakehouse-semantics')
        self.assertIn('href="https://docs.databricks.com', item['figures'][0]['caption'])

    def test_wrong_term_membership_fails_even_when_global_counts_match(self):
        original = validate_site.Page

        def altered(text):
            page = original(text)
            for i, (term, ref) in enumerate(page.tag_refs):
                if ref.startswith('work.html#') and term:
                    page.tag_refs[i] = ('wrong-term', ref)
                    break
            return page

        with patch.object(validate_site, 'Page', side_effect=altered):
            with self.assertRaisesRegex(ContractError, 'index membership mismatch'):
                validate_site.validate_outputs()

    def test_missing_template_value_is_an_error(self):
        from jinja2 import UndefinedError
        from page import env
        with self.assertRaises(UndefinedError):
            env.from_string('{{ missing_contract_field }}').render()


if __name__ == '__main__':
    unittest.main()
