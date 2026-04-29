---
title: "Building a Website with Hugo and GitHub Pages: A Complete Guide"
date: 2025-06-28
slug: hugo-website-github-pages
summary: "Learn how to create a fast, secure website using Hugo static site generator and host it for free on GitHub Pages. Step-by-step guide."
banner_image: "gh_actions_success.jpeg"
tags: ["hugo", "github-pages", "static-site", "web-development"]
draft: false
---

## Intro

After years of using WordPress for my personal projects, I decided to try something different for my portfolio site. I wanted a solution that was fast, secure, and didn't require constant updates and maintenance. That's when I discovered **Hugo and GitHub Pages** - a powerful combination for creating static websites.

In this guide, I'll walk you through my complete process of building this very website using Hugo and deploying it to GitHub Pages. You'll learn how to set up a development environment, create content with Markdown, customize themes, and automate deployment - all for free (almost) and without worrying about databases or server management.

## What is Hugo?

[Hugo](https://gohugo.io/about/introduction/) is a static site generator written in Go, optimized for speed and designed for flexibility.

You can use Hugo’s embedded web server during development to instantly see changes to content, structure, behavior, and presentation. Then deploy the site to your host, or push changes to your Git provider for automated builds and deployment.

## Setting Up Hugo

## Prerequisites

1. [Install](https://gohugo.io/installation/) Hugo
2. Install Git
3. Have Github account

## Create a site

There are probably couple ways of doing that, but I have decided to create website theme and the main website separately and install it as Hugo module. Link to my theme is here: [github.com/miroslawsteblik/hugo-theme-data-blog](github.com/miroslawsteblik/hugo-theme-data-blog)

## Create theme

```sh
hugo new site hugo-theme-data-blog
cd hugo-theme-data-blog
git init
```

I have created folder and file structure following Hugo documentation and once completed pushed to github.

### Theme repository

```sh
hugo-theme-data-blog/
├── archetypes/
├── assets/
├── layouts/
├── static/
├── theme.toml  # created this for theme only
├── go.mod
└── README.md
```

### Why you should create a theme

If you package your site's layout, partials, styles, etc., into a Hugo theme:

- It becomes modular and reusable.
- You can include it in other Hugo projects
- Your main site(s) can stay clean and only define content + config.
- You can version the theme and keep it separate from site-specific content.

More information on [Hugo Quick start](https://gohugo.io/getting-started/quick-start/)

## Create main website

Initialize your site as Hugo module:

```sh
# In your main site directory
hugo mod init github.com/yourusername/exampleSite

# Clean any existing module cache
hugo mod clean

# Get the module
hugo mod get github.com/miroslawsteblik/hugo-theme-data-blog
```

Add the theme to your `hugo.toml`:

```yaml
[module]
[[module.imports]]
  path = "github.com/miroslawsteblik/hugo-theme-data-blog"
```

Update modules:

```sh
# Update module to the last version
hugo mod get -u
# Verify it's downloaded
hugo mod graph
```

Run Hugo

```sh
hugo server
```

### Main site repository

```sh
exampleSite/
├── .github/workflows/
├── content/
├── static/
├── hugo.toml
├── go.mod
└── go.sum
```

## Files structure

1. Added images under `static/images/`
2. Added css files under `assets/css/` and under `static/css/`
3. Added Hugo shortcodes under `layouts/shortcodes/` to allow safe usage of HTML in content files
4. Updated and created HTML files under `layouts/`
5. Build my website menu with three items: `Home`, `About`, `Blog`
6. Added main content under `content/`

## Creating First Content

Add a new page to the site

```sh
hugo new content content/posts/my-first-post.md
```

Hugo created file in the `content/posts/` directory. Note that `draft` is set to true. By defaul Hugo does not publish draft content when you build site.

To see draft content run

```sh
hugo server --buildDrafts
```

## Custom Domain Setup

I purchased my custom domain through [GoDaddy](https://www.godaddy.com/en-uk), which provided a straightforward purchase experience.

## DNS Configuration

The main setup involved configuring DNS records in the domain provider portal:

**Add Type A records** with the following configuration:

- Name: `@`
- Value: GitHub Pages IP addresses

## Common Issues

**Important:** GitHub requires that only Type A records point to their IP addresses. I encountered issues because GoDaddy automatically created default records for their "coming soon" page and WebBuilder service, which needed to be deleted before the custom domain would work properly.

## Additional Setup

I also created a `CNAME` file in the `static/` directory containing my domain name to complete the GitHub Pages configuration.

## Resources

For detailed instructions, see GitHub's official documentation: [Configuring a custom domain for GitHub Pages site](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

## Deploying to GitHub Pages

**GitHub Pages:** Uses the built-in Pages action to deploy directly to username.github.io or a custom domain.

```sh
git add . && git commit -m "development complete"
```

Added `.github/workflow/hugo.yml` to my root

```
name: Deploy Hugo site to Pages

on:
  push:
    branches:
      - master  # Set a branch to deploy
  pull_request:

jobs:
  deploy:
    runs-on: ubuntu-22.04
    permissions:
      contents: read
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true  # Fetch Hugo themes (true OR recursive)
          fetch-depth: 0    # Fetch all history for .GitInfo and .Lastmod

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: 'latest'
          extended: true

      - name: Build
        run: hugo --minify

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

I navigated to my repository **Settings** and under **Pages** -> **Build and deployment** _Source_ selected `Github Actions`.
Then added custom domain, DNS check was performed, once succesfull i added _Enforce HTTPS_

**Trigger:** The workflow activates when you push to a specific branch (usually main or master) or create a pull request.

**Build Process:** GitHub Actions spins up a virtual machine, installs Hugo, checks out code, and runs hugo to generate the static site files in the public/ directory.

**Deployment:** The generated files are then deployed to hosting platform.

Now each time I run `git push` github action provides automatic deployment, version control integration, build error detection, and the ability to preview changes through pull requests before they go live.

**See you next time!**
