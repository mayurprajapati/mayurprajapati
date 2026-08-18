# Personal site (Hugo + CareerCanvas)

Portfolio and blog for [mayurprajapati.in](https://mayurprajapati.in/), built with [Hugo](https://gohugo.io/getting-started/) and the [CareerCanvas](https://themes.gohugo.io/themes/careercanvas/) theme.

## Prerequisites

- Hugo Extended **v0.158+** (`hugo version`)
- Node.js + npm (Tailwind CSS build)
- Git (theme submodule)

## Setup

```bash
cd site
git submodule update --init --recursive
npm install
npm run build:css
```

## Develop

```bash
npm run dev
# → http://127.0.0.1:1313/
```

Or separately:

```bash
npm run watch:css   # terminal 1
hugo server -D      # terminal 2
```

## Publish

```bash
npm run build
# output → public/
```

This runs `tailwindcss` (rebuilds `assets/css/main.css`) then `hugo --gc --minify` (rebuilds `public/`). `public/` is a fully static site — no Hugo process needs to run in production.

## Deploy to Nginx (Ubuntu server)

The repo is cloned directly on the Ubuntu server at `~/mayurprajapati` (this `site/` folder is `~/mayurprajapati/site`). Deploying means: pull the latest changes, rebuild, then sync the freshly built `public/` into the directory Nginx actually serves. Nginx itself needs **no reload** for content changes (it just serves whatever's on disk) — reload is only needed if the Nginx **config** changes (step 3).

We copy `public/` into `/var/www/mayurprajapati` rather than pointing Nginx's `root` straight at `~/mayurprajapati/site/public`, because Nginx runs as `www-data` and typically can't traverse into a user's home directory (`~` is `750`/`700` by default) — `/var/www` avoids that permissions headache.

### 0. One-time server setup

```bash
sudo apt update
sudo apt install -y nginx
sudo mkdir -p /var/www/mayurprajapati
sudo chown -R $USER:$USER /var/www/mayurprajapati   # so your user can rsync into it without sudo each time
sudo systemctl enable --now nginx
```

### 1. Pull, build, sync — every time you deploy

```bash
cd ~/mayurprajapati/site
git pull
git submodule update --init --recursive   # only needed if the theme submodule moved
npm install                               # only needed if package.json changed
npm run build                             # → rebuilds public/
rsync -a --delete public/ /var/www/mayurprajapati/
```
`--delete` prunes files in `/var/www/mayurprajapati` that no longer exist in `public/` (renamed/removed pages) — drop it if you'd rather not prune. This is a local copy (same machine), so no SSH/network involved.

Worth saving on the server as `/opt/mayurprajapati/poll-deploy.sh` and running it with `--force` — that is the same script the auto-deploy poller runs (see [Auto-Deploy on Push](#auto-deploy-on-push), below), so a manual deploy and an automatic one do exactly the same thing.

### 2. Nginx config (one-time setup, or whenever the config itself changes)

Example server block:
```nginx
server {
    listen 80;
    server_name mayurprajapati.in;
    root /var/www/mayurprajapati;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location = /404.html {
        internal;
    }
}
```

After editing the Nginx config:
```bash
sudo nginx -t              # validate syntax before reloading
sudo systemctl reload nginx   # reload without dropping connections
# or: sudo nginx -s reload
```
`reload` re-reads config and gracefully finishes in-flight requests — no downtime, unlike `restart`.

### 3. Cloudflare Tunnel

If the site is exposed via `cloudflared` rather than a public IP/port, the tunnel process on the server just needs to already be pointed at `http://localhost:80` (or wherever Nginx listens) — it doesn't need restarting when content or Nginx config changes, only if the tunnel's own config (`config.yml` / ingress rules) changes:
```bash
sudo systemctl restart cloudflared   # only after editing cloudflared config
```

### Quick troubleshooting

| Symptom | Likely cause |
|---|---|
| Old content still showing | Browser/Cloudflare cache — hard refresh, or purge cache in Cloudflare dashboard |
| 404 on a page that exists in `public/` | Files didn't actually copy — check `ls /var/www/mayurprajapati` on the server |
| Nginx won't reload | `sudo nginx -t` will show the syntax error |
| Site unreachable via tunnel but works on `localhost` | `cloudflared` process down — `sudo systemctl status cloudflared` |

## Auto-Deploy on Push

Push to `main` on GitHub and the server picks it up within a minute — no webhook, no runner, no inbound port. A **systemd timer** runs a poll script every minute; the script compares `HEAD` against `origin/main` and does nothing at all unless they differ. When they do: pull → rebuild → sync into `/var/www/mayurprajapati`.

Nothing restarts nginx — the site is static files on disk, so publishing *is* the deploy.

```
┌──────────────┐     git push      ┌──────────┐
│  Dev Machine │ ───────────────►  │  GitHub  │
└──────────────┘                   └────┬─────┘
                                        │
                              poll every 1 min
                                        │
                              ┌─────────▼──────────────┐
                              │  Ubuntu Server         │
                              │                        │
                              │  systemd timer runs    │
                              │  poll-deploy.sh        │
                              │       │                │
                              │       ▼                │
                              │  git pull              │
                              │  (npm ci if deps moved)│
                              │  npm run build         │
                              │       │                │
                              │       ▼                │
                              │  rsync → /var/www/…    │
                              │       │                │
                              │       ▼                │
                              │  nginx serves static   │
                              └────────────────────────┘
```

### 1. Prerequisites on the server

```bash
sudo apt update
sudo apt install -y git rsync nginx nodejs npm

# Hugo Extended v0.158+ — apt's build is usually too old / not extended:
wget https://github.com/gohugoio/hugo/releases/download/v0.158.0/hugo_extended_0.158.0_linux-amd64.deb
sudo dpkg -i hugo_extended_0.158.0_linux-amd64.deb && rm hugo_extended_0.158.0_linux-amd64.deb
hugo version   # must say "extended"
```

Clone the repo and install node deps once:

```bash
git clone https://github.com/mayurprajapati/mayurprajapati.git ~/mayurprajapati
cd ~/mayurprajapati/site && npm ci
```

The poller pulls over HTTPS, so give git a credential store (or switch `origin` to SSH with a deploy key) — otherwise the fetch sits at the same commit forever:

```bash
git config --global credential.helper store   # then `git fetch` once and paste a PAT
```

> **Note on the theme.** `site/themes/careercanvas` is declared in `.gitmodules` but is *not* committed as a gitlink (`git ls-files site/themes` is empty), so `--recurse-submodules` will **not** bring it down. The script below handles it: if `site/themes/careercanvas/layouts` is missing it tries `git submodule update --init` and then falls back to cloning the theme URL directly. The durable fix is to commit the theme properly (`git submodule add https://github.com/felipecordero/careercanvas.git site/themes/careercanvas`, or vendor the folder into the repo) — worth doing, since local theme edits currently live only on your machine and would be lost on the server's fresh clone.

### 2. Create the Auto-Deploy Script

```bash
sudo mkdir -p /opt/mayurprajapati
sudo nano /opt/mayurprajapati/poll-deploy.sh
```

```bash
#!/usr/bin/env bash
#
# poll-deploy.sh — poll GitHub for new commits and redeploy the Hugo site.
#
#   ./poll-deploy.sh            deploy only if origin/<branch> moved ahead
#   ./poll-deploy.sh --force    rebuild and publish unconditionally
#
# Defaults below can be overridden in /etc/default/mayurprajapati-deploy.
#
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/mario/mayurprajapati}"
SITE_DIR="${SITE_DIR:-$REPO_DIR/site}"
WEB_ROOT="${WEB_ROOT:-/var/www/mayurprajapati}"
BRANCH="${BRANCH:-main}"
LOG="${LOG:-/var/log/mayurprajapati-deploy.log}"
LOCK="${LOCK:-/tmp/mayurprajapati-deploy.lock}"

FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

# systemd gives a bare PATH; make sure hugo/node/npm are reachable.
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
# shellcheck disable=SC1090
[ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG"; }

# Only one deploy at a time — the timer fires every minute, a build takes longer.
exec 9>"$LOCK"
if ! flock -n 9; then
    exit 0
fi

cd "$REPO_DIR"
git fetch origin "$BRANCH" --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ] && [ "$FORCE" -eq 0 ]; then
    exit 0
fi

if [ "$FORCE" -eq 1 ]; then
    log "Forced deploy requested."
else
    log "Changes detected (${LOCAL:0:7} -> ${REMOTE:0:7}). Deploying..."
fi

# Work out what changed *before* pulling, so we can skip the slow steps.
CHANGED=$(git diff --name-only HEAD "origin/$BRANCH" || true)
DEPS_CHANGED=0
SUBMODULE_CHANGED=0
echo "$CHANGED" | grep -qE '^site/(package\.json|package-lock\.json)$' && DEPS_CHANGED=1
echo "$CHANGED" | grep -qE '^(\.gitmodules|site/themes/)' && SUBMODULE_CHANGED=1

git pull --ff-only origin "$BRANCH" >> "$LOG" 2>&1

# The CareerCanvas theme is declared in .gitmodules but is NOT committed as a
# gitlink, so `submodule update` alone can leave a fresh clone with no theme at
# all — fall back to cloning it straight from the URL in .gitmodules.
THEME_DIR="$SITE_DIR/themes/careercanvas"
THEME_URL="${THEME_URL:-$(git config -f .gitmodules submodule.site/themes/careercanvas.url 2>/dev/null || echo https://github.com/felipecordero/careercanvas.git)}"

if [ ! -d "$THEME_DIR/layouts" ]; then
    log "Theme missing — fetching CareerCanvas..."
    git submodule update --init --recursive >> "$LOG" 2>&1 || true
    if [ ! -d "$THEME_DIR/layouts" ]; then
        git clone --depth 1 "$THEME_URL" "$THEME_DIR" >> "$LOG" 2>&1
    fi
elif [ "$SUBMODULE_CHANGED" -eq 1 ]; then
    log "Updating theme..."
    if git ls-files --error-unmatch site/themes/careercanvas >/dev/null 2>&1; then
        git submodule update --init --recursive >> "$LOG" 2>&1
    else
        git -C "$THEME_DIR" pull --ff-only >> "$LOG" 2>&1 || log "WARN: theme pull failed, using existing checkout."
    fi
fi

cd "$SITE_DIR"

if [ "$DEPS_CHANGED" -eq 1 ] || [ ! -d node_modules ]; then
    log "npm dependencies changed, running npm ci..."
    npm ci --no-audit --no-fund >> "$LOG" 2>&1
fi

log "Building site (tailwind + hugo)..."
npm run build >> "$LOG" 2>&1

# Sanity check: never publish an empty build over a working site.
if [ ! -s public/index.html ]; then
    log "ERROR: build produced no public/index.html — keeping the existing site."
    exit 1
fi

log "Publishing to $WEB_ROOT ..."
rsync -a --delete public/ "$WEB_ROOT/" >> "$LOG" 2>&1

log "Deploy complete ($(git -C "$REPO_DIR" rev-parse --short HEAD))."
```

Make it executable, create the log file, and make sure the web root belongs to your user — so the deploy needs **no `sudo` at all** and nothing has to be added to `visudo`:

```bash
sudo chmod +x /opt/mayurprajapati/poll-deploy.sh
sudo touch /var/log/mayurprajapati-deploy.log
sudo chown mario:mario /var/log/mayurprajapati-deploy.log
sudo mkdir -p /var/www/mayurprajapati
sudo chown -R mario:mario /var/www/mayurprajapati
```

Optional — override paths or branch without editing the script:

```bash
sudo nano /etc/default/mayurprajapati-deploy
```

```bash
REPO_DIR=/home/mario/mayurprajapati
SITE_DIR=/home/mario/mayurprajapati/site
WEB_ROOT=/var/www/mayurprajapati
BRANCH=main
LOG=/var/log/mayurprajapati-deploy.log
```

### 3. Create systemd Service

The site itself is static — nginx already serves it — so the systemd unit is the **poller**, not an app process. It is `Type=oneshot`: it runs, deploys if needed, and exits.

```bash
sudo nano /etc/systemd/system/mayurprajapati-deploy.service
```

```ini
[Unit]
Description=Poll GitHub and deploy mayurprajapati.in (Hugo -> Nginx)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=mario
Group=mario
Environment="HOME=/home/mario"
EnvironmentFile=-/etc/default/mayurprajapati-deploy
WorkingDirectory=/home/mario/mayurprajapati
ExecStart=/opt/mayurprajapati/poll-deploy.sh
TimeoutStartSec=600
```

### 4. Create the Timer (Git Polling)

```bash
sudo nano /etc/systemd/system/mayurprajapati-deploy.timer
```

```ini
[Unit]
Description=Check GitHub for new mayurprajapati commits every minute

[Timer]
OnBootSec=2min
OnUnitActiveSec=1min
AccuracySec=10s
Unit=mayurprajapati-deploy.service

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mayurprajapati-deploy.timer
systemctl list-timers mayurprajapati-deploy.timer --no-pager
```

Prefer cron? The script takes its own `flock`, so it is cron-safe too — use this *instead of* the timer:

```bash
crontab -e
# * * * * * /opt/mayurprajapati/poll-deploy.sh
```

### 5. Log Rotation (optional)

```bash
sudo nano /etc/logrotate.d/mayurprajapati-deploy
```

```
/var/log/mayurprajapati-deploy.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    copytruncate
}
```

### 6. First Deploy

```bash
/opt/mayurprajapati/poll-deploy.sh --force     # build + publish right now
tail -f /var/log/mayurprajapati-deploy.log
```

### How It Works

| Event | What happens |
|---|---|
| **Nothing pushed** | Fetch, hashes match, exit — no build, no log noise |
| **Push to `main`** | Pull → build → `rsync --delete` into `/var/www/mayurprajapati` within ~1 min |
| **`package.json` / `package-lock.json` changed** | `npm ci` runs before the build |
| **Theme moved (`.gitmodules`, `site/themes/`)** | Theme is updated, or cloned if missing, first |
| **A build is still running** | The next tick sees the `flock` and exits immediately — no overlap |
| **Build fails or emits no `index.html`** | Publish is skipped; the currently-live site stays up |
| **Server reboots** | Timer re-arms 2 min after boot; nginx is already `enabled` |

### Useful Commands

| Command | Description |
|---|---|
| `systemctl list-timers mayurprajapati-deploy.timer` | When it last ran / next runs |
| `sudo systemctl status mayurprajapati-deploy` | Result of the most recent poll |
| `journalctl -u mayurprajapati-deploy -f` | Live unit logs (errors from the script) |
| `tail -f /var/log/mayurprajapati-deploy.log` | Deploy log — what was pulled and built |
| `sudo systemctl start mayurprajapati-deploy` | Poll right now instead of waiting |
| `sudo systemctl stop mayurprajapati-deploy.timer` | Pause auto-deploy (e.g. while debugging on the box) |
| `/opt/mayurprajapati/poll-deploy.sh --force` | Force a rebuild + publish of the current checkout |

## Content

| Path | Purpose |
|------|---------|
| `content/en/about.md` | About section |
| `content/en/skills.md` | Skills cards |
| `content/en/experience.md` | Timeline |
| `content/en/technical.md` | Tech stack icons |
| `content/en/contact.md` | Contact |
| `content/en/blog/` | Blog posts |
| `hugo.toml` | Site config / SEO / social |
| `static/images/` | Profile photo, etc. |
| `static/files/` | Resume PDF |

New post:

```bash
hugo new content content/en/blog/my-post.md
```
