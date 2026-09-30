# Step 4: Nginx Static Asset Cache Fix

This folder contains the deployable fix for the immediate performance bottleneck:
large Three.js/WebGL static assets are served by `play.otterlantis.com` with weak
cache headers and slow origin delivery.

## Files

- `play-otterlantis-static-cache.include.conf`: paste/include inside the
  `server { ... }` block for `play.otterlantis.com`.
- `nginx-dry-run.conf`: portable syntax-test template for machines with Nginx.
- `validate-nginx-config.sh`: renders the template and runs `nginx -t`.
- `verify-step4-headers.sh`: checks production response headers after reload.
- `validation-report.txt`: result from this local machine.

## Deployment

On the server, place `play-otterlantis-static-cache.include.conf` inside the
existing `play.otterlantis.com` Nginx server block, before generic fallback
locations.

Then run:

```bash
nginx -t
systemctl reload nginx
```

If using BT panel, paste the snippet into the site config for
`play.otterlantis.com`, save, test config, and reload Nginx.

To syntax-check this folder on a machine with Nginx installed:

```bash
./validate-nginx-config.sh
```

After reload, verify production headers:

```bash
./verify-step4-headers.sh https://play.otterlantis.com
```

## Expected Headers After Deploy

```bash
curl -I https://play.otterlantis.com/model-site/scene-terrain-opt.glb
curl -I https://play.otterlantis.com/assets/SectionParkour-Ba-Fk1Jk.js
curl -I https://play.otterlantis.com/index.html
```

Expected:

- HTML: `Cache-Control: no-cache, must-revalidate`
- hashed JS/CSS: `Cache-Control: public, max-age=31536000, immutable`
- GLB/images: `Cache-Control: public, max-age=2592000`
- GLB: `Content-Type: model/gltf-binary`
- GLB: `Access-Control-Allow-Origin: *`

This fix improves repeat loads and CDN behavior. If first-load speed remains
slow, the next production fix is CDN/object-storage delivery for GLB and large
chunks.
