"""Parse and validate public configuration using its JSON Schema."""
from contracts import ROOT, parse_yaml, schema_validate
from generated.config_schema import PortfolioConfigDocument


def load_config():
    data = parse_yaml((ROOT / 'config.yaml').read_text(), 'config.yaml')
    schema_validate(data, 'config', 'config.yaml')
    PortfolioConfigDocument.model_validate(data)
    ids, destinations = set(), set()
    for nav in data['navigation']:
        if nav['id'] in ids or nav['href'] in destinations:
            raise ValueError('config.yaml: duplicate navigation ID or destination')
        ids.add(nav['id'])
        destinations.add(nav['href'])
    return {**data, 'navigation': [n for n in data['navigation'] if n['enabled']]}
