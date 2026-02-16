# Proper Plex Shuffle

[![Build and Push Docker Image](https://github.com/salilkansal/proper-plex-shuffle/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/salilkansal/proper-plex-shuffle/actions/workflows/docker-publish.yml)

Plex has a [well-documented](https://www.reddit.com/r/PleX/comments/5ic0fh/it_has_been_years_can_plex_please_fix_their/db7wdm1/) shuffle problem: because of the [Birthday Problem](https://en.wikipedia.org/wiki/Birthday_problem), truly random shuffles feel repetitive and keep surfacing recently-watched content.

**Proper Plex Shuffle** fixes this by automatically rebuilding your TV show playlists daily using a tiered shuffle algorithm that always puts your least-watched episodes first.

---

## How It Works

Every episode is placed into one of four tiers based on when you last watched it. Episodes within each tier are shuffled randomly, then the tiers are concatenated:

| Tier | Criteria | Result |
|------|----------|--------|
| 1 | Never watched | Shuffled, always first |
| 2 | Not watched in 90+ days | Shuffled |
| 3 | Not watched in 30–90 days | Shuffled |
| 4 | Watched in last 30 days | Shuffled, always last |

This means you always see fresh content first, with recently-watched episodes naturally falling to the bottom — without excluding anything.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker + Docker Compose
- A Plex account with a running Plex Media Server

### 1. Clone the repo

```bash
git clone https://github.com/salilkansal/proper-plex-shuffle.git
cd proper-plex-shuffle
```

### 2. Set up a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run setup

`setup.py` authenticates via Plex's OAuth flow (no credentials ever touch this app), then walks you through selecting your server, library, and shows interactively.

```bash
python setup.py
```

This will:
1. Open `app.plex.tv` in your browser for login
2. List your available Plex servers to pick from
3. List TV libraries on the chosen server
4. Show a checkbox picker for all shows in that library
5. Write a complete `plex_config.ini`

### 4. Deploy with Docker

```bash
docker compose build
docker compose up -d
```

The container runs as a background daemon and rebuilds your playlists daily at midnight. The token is refreshed on every run and written back to `plex_config.ini` via the volume mount.

---

## Configuration

`plex_config.ini` is created by `setup.py` and is gitignored. Its format:

```ini
[plex_config]
token = your_plex_token
server_name = MyPlexServer
library_name = TV Shows
tv_shows = Seinfeld, The Office (US), Brooklyn Nine-Nine
```

See `plex_config_sample.ini` for reference.

---

## Files

| File | Purpose |
|------|---------|
| `setup.py` | One-time interactive setup — OAuth login, server/library/show picker, writes config |
| `refresh_playlists.py` | Daily script — refreshes token, rebuilds playlists using tiered shuffle |
| `Dockerfile` | Python 3.12-slim image with cron |
| `docker-compose.yml` | Runs container as daemon, mounts config file |
| `crontab` | Runs `refresh_playlists.py` at midnight, logs to `/var/log/plex_shuffle.log` |
| `plex_config_sample.ini` | Config template — copy to `plex_config.ini` and fill in |

---

## Running Manually

To trigger a playlist refresh immediately without waiting for midnight:

```bash
docker exec plex_shuffle /usr/local/bin/python3 /app/refresh_playlists.py
```

To check logs:

```bash
docker exec plex_shuffle cat /var/log/plex_shuffle.log
```

---

## Token Management

- The Plex token is obtained once via `setup.py` using OAuth (no password stored)
- On every daily run, the token is re-validated against plex.tv and the refreshed token is written back to `plex_config.ini`
- The config file is volume-mounted so token updates persist across container restarts
- If your token is ever revoked (e.g. you sign out of all devices on plex.tv), re-run `setup.py`
