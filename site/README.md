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

Worth saving as a one-liner, e.g. `~/mayurprajapati/site/deploy.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd ~/mayurprajapati/site
git pull
npm run build
rsync -a --delete public/ /var/www/mayurprajapati/
```
```bash
chmod +x ~/mayurprajapati/site/deploy.sh
```
Then deploying is just `~/mayurprajapati/site/deploy.sh`.

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
