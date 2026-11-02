# Development and release

## Git

Work on a feature or repair branch. The owner reviews changes and runs commit, push and merge commands. Local hooks reject commits and pushes to `main`; GitHub protection is authoritative.

Pull requests require the GitHub Actions `test` check on an up-to-date branch. Protection includes administrators and permits no PR bypass actors, force pushes or branch deletion. Squash merges use the reviewed PR title, which must follow Conventional Commits.

The policy requires a PR and successful CI. It does not require an external approving reviewer, allowing a solo maintainer to review and merge their own PR.

## Repository settings

Manage branch protection, merge options and Pages publishing in the GitHub repository settings. Pages uses GitHub Actions.

## Release

CI validates source contracts, lint, privacy, commit messages, PR titles, tests and generated HTML. Search artifacts are build-only because bundled vendor runtimes vary by platform. A manifest validates their inputs and file hashes.

`tools/package_site.py` copies only public pages, assets, schemas, CSS, search output and hosting metadata to `dist/`. The Pages artifact is uploaded after validation. Deployment depends on the successful `test` job and runs only for pushes to `main` after merge.

To remove previously tracked search artifacts from Git while retaining local build output:

```sh
git rm -r --cached -- pagefind
```
