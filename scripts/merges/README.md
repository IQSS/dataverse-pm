# Who merges Dataverse pull requests?

Counts who merged each pull request into `develop` in
[IQSS/dataverse](https://github.com/IQSS/dataverse), including squash merges.

## Why the GitHub API is needed

- **Regular merges** create a "Merge pull request #N from …" commit. When the
  merge is done in GitHub's web UI, the commit's author is the person who
  clicked merge, so git alone gives the answer.
- **Squash merges** produce a single commit whose author is the PR author and
  whose committer is "GitHub". Git doesn't record who merged it. GitHub does,
  in the PR's `merged_by` field, which this script fetches.

Direct pushes to `develop` (non-merge commits without `(#N)` at the end of the
subject) aren't PRs and are skipped.

## Usage

Requires Python 3 (standard library only) and a local clone of the repo
(default `~/github/iqss/dataverse`; override with `--git-dir`).

```bash
cd scripts/merges
python3 merges.py collect                  # git history -> out/prs.csv
python3 merges.py fetch                    # GitHub API -> cache/<pr>.json
python3 merges.py report --since 2026-05-05  # -> out/merges.csv + tables
```

`collect` defaults to PRs merged since 2023-11-05 (`--since` to change).

### Charts

```bash
./render.sh
```

This runs `report` (saving its output to `out/report.txt`), then
`plot.py`, which writes three HTML charts to `out/` (gitignored), then takes a PNG screenshot of
each with headless Google Chrome (set `CHROME` to use a different path):

| Chart | What |
|---|---|
| `merges-per-month` | Stacked bars per month: the top 6 mergers, "Other", and "squash merge" (not looked up yet) |
| `merges-per-month-line` | The same series as lines |
| `merges-per-month-people` | One small panel per person, all on the same scale |

The HTML versions have hover details, and the bar chart has a table view.

### Unauthenticated (default)

No login needed because the repo is public, but GitHub allows only **60
requests per hour** per IP address. The ~135 squash merges take about three
hours.

- `fetch` stops when the limit is hit and says when it resets. Run it again
  then. Results are cached in `cache/` (gitignored), so nothing is fetched twice.
- `fetch --wait` sleeps through each reset and finishes on its own. Run it
  in the background, for example:

  ```bash
  mkdir -p out && nohup python3 merges.py fetch --wait > out/fetch.log 2>&1 &
  ```

- `fetch --limit 5` fetches only a few, which is handy for testing.

### Authenticated (5,000 requests per hour)

Any of these will do:

```bash
brew install gh && gh auth login
python3 merges.py fetch --gh --all
```

```bash
GITHUB_TOKEN=... python3 merges.py fetch --all
```

```bash
python3 merges.py fetch --token ... --all
```

With the higher limit, `--all` is cheap: it also fetches `merged_by` for the
regular merges (about 970), so `report` can check the git-author method
against GitHub's records.

## Output

Nothing below is committed: `cache/` and `out/` are both gitignored. Run
`collect`, `fetch` and `./render.sh` to rebuild everything. The cache is what
takes time to rebuild, about 3 hours without a login (see above).

| Path | What |
|---|---|
| `out/prs.csv` | One row per merged PR from git: `pr`, `date`, `method` (`merge` or `squash`), `git_merger` (merge commits), `git_author` (squash commits), `subject`, `sha` |
| `cache/<pr>.json` | Cached API answer per PR: `author`, `merged_by`, `merged_at`, `merge_commit_sha`, `base`, `fetched_at` |
| `out/merges.csv` | Final table: `pr`, `date`, `method`, `merger`, `source` (`git`, `api`, `none`), `pr_author`, `subject`, `url` |
| `out/fetch.log` | Log from a background `fetch --wait`, if you use one |
| `out/report.txt` | Output of `report`, saved by `render.sh` |
| `out/merges-per-month*.html`, `.png` | Charts from `plot.py` and `render.sh` |

## Notes

- Git records names ("John Doe") and the API records logins
  ("jdoe"). `report` learns which name goes with which login from
  the API data (squash-merge PR authors, and regular merges fetched with
  `--all`) and lists each person under their login. Anyone it hasn't learned
  a login for keeps their git name, so fetching more data makes the tables
  more consistent.
- See `ALIASES` for mapping names and GitHub usernames.
- Squash merges not fetched yet are listed as "squash merge".
