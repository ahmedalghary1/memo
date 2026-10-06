# Connect memo-eg.io to the Hostinger VPS

## DNS records in Hostinger hPanel

Under **Domains → Domain portfolio → Manage → DNS / Nameservers → DNS records**, set:

| Type | Name | Target | TTL |
|---|---|---|---|
| A | @ | 179.198.215.77 | 14400 (or default) |
| CNAME | www | memo-eg.io | default |

Edit conflicting records instead of creating duplicates. Remove old A/AAAA records for these hosts only if they point to another server. Keep MX/TXT records used for email. DNS must be managed at Hostinger for these records to take effect there.

## Host Nginx and HTTPS

The Docker Nginx container publishes host port 8001. The host-level Nginx config in `deploy/nginx/memo-eg.io.conf` proxies the domain to `127.0.0.1:8001`.

On the VPS, after DNS resolves to this server:

```bash
sudo cp deploy/nginx/memo-eg.io.conf /etc/nginx/sites-available/memo-eg.io
sudo ln -s /etc/nginx/sites-available/memo-eg.io /etc/nginx/sites-enabled/memo-eg.io
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d memo-eg.io -d www.memo-eg.io
```

Allow inbound TCP 80 and 443 in the VPS firewall and Hostinger firewall. Certbot requires port 80 to reach this VPS for HTTP validation. Its Nginx plugin configures TLS and the HTTP-to-HTTPS redirect.

## Docker binding

The project `.env` is configured for `PUBLIC_ORIGIN=https://memo-eg.io`, Django host/CSRF allowlists for the apex and `www`, and `MEMO_BIND_IP=127.0.0.1` / `MEMO_PORT=8001`. This makes the app reachable through host Nginx while keeping port 8001 off the public interface.

After uploading the updated project and `.env` to the VPS:

```bash
docker compose up -d --build web nginx
docker compose ps
docker compose logs --tail=100 web nginx
```

Verify `https://memo-eg.io/` and `https://www.memo-eg.io/`. The Meta webhook URL is `https://memo-eg.io/api/whatsapp/webhook/`.
