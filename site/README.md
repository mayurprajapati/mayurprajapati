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

Deploy the contents of `public/` to Nginx (e.g. `/var/www/mayurprajapati`) behind Cloudflare Tunnel.

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
