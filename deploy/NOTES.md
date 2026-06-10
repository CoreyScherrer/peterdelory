# Deploy notes — peterdeloryphotographer.com

Standalone static nginx site on Corey's iMac, mirroring the **coreyiscorey.com**
pattern. Nothing here runs automatically — these are drafts for a deliberate,
operator-run deploy step.

## Target

| | |
|---|---|
| Domain | `peterdeloryphotographer.com` (+ `www.`) — registered 2026-06-09 |
| Repo | `https://github.com/CoreyScherrer/peterdelory` |
| Webroot | `/var/www/peterdeloryphotographer/www/public` |
| nginx conf | `deploy/peterdeloryphotographer.com.conf` |
| Deploy script | `deploy/deploy-peterdelory-www.sh.draft` |
| Backend | none — pure static, no daemon, no port |
| TLS | reuses the `coreyscherrer.com` origin cert; real TLS terminates at the Cloudflare tunnel edge (`noTLSVerify`) |

## One-time setup (operator, with sudo)

1. **DNS / tunnel** — confirm `peterdeloryphotographer.com` (and `www`) resolve
   through the Cloudflare tunnel to this origin. (DNS is managed in the
   Cloudflare dashboard, not in these scripts.)

2. **nginx conf** — version-control it with the other domains, then symlink:
   ```sh
   cp deploy/peterdeloryphotographer.com.conf \
      /Users/admin/Sites/scripts/nginx/peterdeloryphotographer.com.conf
   sudo ln -s /Users/admin/Sites/scripts/nginx/peterdeloryphotographer.com.conf \
              /usr/local/etc/nginx/servers/peterdeloryphotographer.com.conf
   sudo nginx -t && sudo nginx -s reload
   ```

3. **Deploy script** — copy into the Sites deploy dir (it sources
   `deploy-common.sh` from there):
   ```sh
   cp deploy/deploy-peterdelory-www.sh.draft \
      /Users/admin/Sites/scripts/deploy/deploy-peterdelory-www.sh
   chmod +x /Users/admin/Sites/scripts/deploy/deploy-peterdelory-www.sh
   ```

4. **First deploy** (merge this branch to `main` first — the script pulls
   `origin/main`):
   ```sh
   /Users/admin/Sites/scripts/deploy/deploy-peterdelory-www.sh --yes
   ```

## Optional — register in the service dashboard

Add to `/Users/admin/Sites/dev/blog-app/config/services.yaml` so the site shows
up in health monitoring + auto-propagation:

```yaml
- key: peterdelory
  name: Peter de Lory Photographer
  description: Photographer portfolio — static nginx site
  type: web
  probe_url: https://peterdeloryphotographer.com/
  expected_codes: [200, 301, 302]
  domain: system
  schedule: static (nginx)
  tier: non-critical
  icon: bi-camera
```

And optionally add `peterdelory-www` to `dev-ops.sh` `VALID_SERVICES` +
`get_dev_dir`/`get_prod_dir` to deploy via the unified wrapper.

## This is a public prod site

Unlike the dev-only services, this domain is **meant** to be reachable on the
public internet — the dev-only-on-prod-hostname rule does not apply here.

## Images

Heroes/thumbnails are placeholder black bands for now. The Google Drive file IDs
for candidate images are preserved in `content/**.json` (as `hero`/`thumb`
fields with `drive.google.com` URLs, which `build.py` deliberately treats as
"not yet available" because Drive doesn't hotlink). To go live with real images:
download the originals into `public/assets/img/`, update the content JSON to
point at `/assets/img/...`, and re-run `python3 build.py`.
