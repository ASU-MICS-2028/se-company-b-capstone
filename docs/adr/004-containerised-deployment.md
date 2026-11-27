# ADR-004: Containerised deployment with separate staging and production

**Status:** Accepted (2026-11-27): host is a Contabo VPS running Coolify · **Date:** 2026-11-24, updated 2026-11-27 · **Owner:** Eugene

## Context

We need a hosted **staging** environment for demo candidates and usability tests, and a **production** environment for the final demo on 10 and 18 December. The proposal requires HTTPS for any deployed service. Budget is close to zero, and the team has limited ops experience. A local Docker dev setup (bind-mounted source) is also being considered so teammates don't need Python and Node installed.

## Decision

**Host (decided 2026-11-27):** the team's existing **Contabo VPS running [Coolify](https://coolify.io)**, a self-hosted platform that deploys Docker Compose apps from GitHub and handles HTTPS (Let's Encrypt) and routing. This is the "VPS + Docker Compose" option below, with Coolify taking care of the parts that needed an owner: TLS, redeploys and logs. Staging goes first; production follows from a tagged release on `main`.


- Package the app as **two Docker images**: `autocare-api` (uvicorn) and `autocare-web` (static `vite build` behind nginx, which also proxies `/api`), defined in `docker-compose.yml`. For now Coolify builds them on the server from the branch it tracks. Pushing to GHCR and promoting the same image to production is the next step.
- Run **staging** and **production** as separate deployments of the *same image*, differing only in env vars and secrets (GitHub Environments).
- Deploy flow: push to `staging` → build, deploy to staging, smoke-test `/api/health`. Tag `vX.Y.Z` on `main` → promote the same image to production, with manual approval.
- Hosting target: chosen on 2026-11-27 (see above).

## Options compared

| | VPS + Docker Compose (e.g. Hetzner, DigitalOcean) | Render / Railway | AWS (ECS Fargate or Lightsail) |
|---|---|---|---|
| Cost | ~€4–6/month, flat | Free or hobby tier; may sleep when idle | Free tier is limited; easy to overspend |
| Setup | Medium: SSH, Compose, Caddy for HTTPS | Low: connect repo, set env vars | High: IAM, networking, load balancer |
| SQLite persistence | Easy: host volume | Needs a paid persistent disk | EFS or a move to RDS |
| HTTPS | Caddy or Let's Encrypt (automatic) | Built in | ACM + ALB |
| Staging + prod | Two Compose projects on one box | Two services | Two services or stacks |
| Learning value for the course | High (real DevOps) | Low | High, but costly in time |

**Chosen: VPS + Docker Compose, through Coolify on the team's Contabo VPS** (2026-11-27). Originally the leaning: It's the cheapest option that keeps SQLite on a real disk, and Compose files can be shared with local dev. **Render** is the fallback if nobody can own a VPS.

## Consequences

- The Dockerfiles and Compose files are written once and used for local dev, staging and production.
- Someone must own server patching and secrets if we pick a VPS.
- Until a target is chosen, `deploy-staging.yml` and `deploy-prod.yml` stay manual placeholders.

## Alternatives considered

- **No containers** (run uvicorn and nginx directly on a host): fewer moving parts, but environment drift between laptops, CI and servers. That's the problem we already hit with macOS vs Linux lockfiles.
- **A single environment:** cheaper, but no safe place to test a demo candidate before the graded demo.
