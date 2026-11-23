# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/cryptorecceh/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/cryptorecceh/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One image summing up 23 November 2026 world news: 54 sourced stories on a
single dense front page — three leads (COP31 collapses with no deal, Asian
markets plunge on an AI rout, Iran hits US bases in Bahrain), twelve medium
stories, a UTC timeline, a numbered world map, two story lists and a date
check separating today's news from older stories.

## Run it

```sh
python3 main.py --check   # render + validate, writes nothing
python3 main.py           # writes entry.png (1024x1024, pure stdlib)
```

`main.py` is pure Python 3 stdlib — no Pillow, no third-party packages. It
draws the whole page with its own canvas, a bitmap-font typer and a Paeth
PNG encoder, so the output is byte-identical on every run.

## Contents

- `main.py` — the whole renderer: fonts, canvas, typer, PNG encoder,
  pictograms, the 54-story data tables, layout and CLI.
- Every story is attributed to its source (Reuters, AP, AFP, BBC, IANS, UN
  and others) and dated to Monday 23 November 2026.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
