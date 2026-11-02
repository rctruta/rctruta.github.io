"""Package only validated public files for GitHub Pages."""
import pathlib
import shutil

from config_loader import load_config
from contracts import ROOT, ContractError
from validate_site import validate_outputs


def package_site(destination):
    destination = pathlib.Path(destination)
    if destination.resolve() == ROOT.resolve() or ROOT.resolve().is_relative_to(destination.resolve()):
        raise ContractError('Output directory must not contain the source repository.')
    if destination.resolve().is_relative_to(ROOT.resolve()) and destination.resolve() != ROOT / 'dist':
        raise ContractError('The repository output directory must be dist/.')
    validate_outputs()
    config = load_config()
    files = ['index.html', 'style.css', 'CNAME', '.nojekyll']
    files += [item['href'] for item in config['navigation']]
    directories = ['assets', 'schemas', 'pagefind']
    for name in files + directories:
        path = ROOT / name
        if not path.exists():
            raise ContractError(f'Missing public input: {name}')
        if path.is_symlink() or (path.is_dir() and any(p.is_symlink() for p in path.rglob('*'))):
            raise ContractError(f'Public input contains a symbolic link: {name}')
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for name in files:
        shutil.copyfile(ROOT / name, destination / name)
    for name in directories:
        shutil.copytree(ROOT / name, destination / name)
    for path in destination.rglob('*'):
        path.chmod(0o755 if path.is_dir() else 0o644)
    return destination


if __name__ == '__main__':
    package_site(ROOT / 'dist')
    print('Public site packaged in dist/.')
