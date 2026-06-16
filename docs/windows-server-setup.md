# Windows Server And Cloudflare Setup

Use this when the greenhouse server and Cloudflare Tunnel run in Docker Desktop on the
always-on Windows PC.

## 1. Install tools on the Windows PC

Install:

- Docker Desktop
- Git
- Python, only if you want to run tests locally outside Docker

Docker Desktop is the normal deployment path. Python is optional for the running server,
but useful when testing changes.

## 2. Create the local `.env` file

Copy the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and fill in:

```text
CLOUDFLARE_TUNNEL_TOKEN=<the token from Cloudflare>
GREENHOUSE_READ_TOKEN=<long random token for the iPhone/iPad app>
GREENHOUSE_INGEST_TOKEN=<long random token for ESP32 uploads>
GREENHOUSE_CLIENT_DEVICE_ID=greenhouse
GREENHOUSE_SNAPSHOT_WINDOW_MINUTES=5
```

Never commit `.env`. It is ignored by Git.

Generate long random tokens with PowerShell:

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

Run it twice: once for `GREENHOUSE_READ_TOKEN`, once for `GREENHOUSE_INGEST_TOKEN`.

## 3. Configure Cloudflare Tunnel

In Cloudflare Zero Trust:

1. Create a Cloudflared tunnel.
2. Name it `greenhouse-basement-pc` or similar.
3. Choose the Docker connector option and copy the tunnel token into `.env`.
4. Add a public hostname, for example `greenhouse-api.nathansapps.ca`.
5. Set the service to:

```text
Type: HTTP
URL: greenhouse-server:8000
```

Leave the Cloudflare path field empty unless you intentionally want path-specific routing.
The app will call:

```text
https://greenhouse-api.nathansapps.ca/api/v1/app/latest
```

Do not put `/api/v1/app/latest` in the Cloudflare service URL.

## 4. Start Docker Desktop services

From the project root:

```powershell
docker compose up -d --build
```

This starts:

- `greenhouse-server`: Flask + SQLite API
- `greenhouse-cloudflared`: Cloudflare Tunnel connector

The local ESP32 upload endpoint is still:

```text
http://<windows-pc-ip>:8000/api/v1/readings
```

The mobile app endpoint through Cloudflare is:

```text
https://greenhouse-api.nathansapps.ca/api/v1/app/latest
```

Check the containers:

```powershell
docker compose ps
docker compose logs -f greenhouse-server
docker compose logs -f cloudflared
```

## 5. Verify the API

Local health check on the Windows PC:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Mobile API check:

```powershell
$headers = @{ Authorization = "Bearer $env:GREENHOUSE_READ_TOKEN" }
Invoke-RestMethod https://greenhouse-api.nathansapps.ca/api/v1/app/latest -Headers $headers
```

If you did not export the token into the current PowerShell session, paste the token directly:

```powershell
$headers = @{ Authorization = "Bearer paste-read-token-here" }
```

## 6. Point ESP32 boards at the Windows PC

Update:

- `esp32/boards/greenhouse/app_config.py`
- `esp32/boards/outdoor/app_config.py`

Set:

```python
SERVER_URL = "http://<windows-pc-ip>:8000/api/v1/readings"
TEMP_WINDOWS_SERVER_URL = None
SERVER_UPLOAD_TOKEN = "<same value as GREENHOUSE_INGEST_TOKEN>"
```

Keep the ESP32 boards pointed at the local Windows PC, not Cloudflare. The MicroPython
client intentionally uses local `http://` for reliability and simplicity.

## 7. Allow the local ESP32 port through Windows Firewall

Allow inbound TCP `8000` on the Windows PC so the ESP32 boards can post locally.

Cloudflare Tunnel does not require opening a public inbound port. This firewall rule is
only for devices on your home network.

## 8. Make Docker Desktop start with Windows

In Docker Desktop settings, enable start-on-login.

The containers use:

```yaml
restart: unless-stopped
```

so once Docker Desktop starts, the server and tunnel containers come back automatically.

Important limitation:

- Docker Desktop normally starts when your Windows user session starts
- if you need services to come up before user login, a native Windows service or Scheduled Task is more reliable than Docker Desktop alone

## 9. Update the basement PC without deleting the folder

Do not delete the project folder. Use Git to pull only changed tracked files.

From the project root:

```powershell
git status
git pull
docker compose up -d --build
```

This keeps local ignored files/folders such as:

- `.env`
- `data/`
- `.venv/`

If Git says local changes would be overwritten, check what changed:

```powershell
git status
```

Usually you should only edit `.env` on the Windows PC. If you edited tracked files like
`docker-compose.yml` or files under `server/`, copy your notes somewhere first, then ask
before forcing anything.

## 10. Verify outage recovery

Test one full restart cycle before leaving it unattended:

1. Reboot the Windows PC.
2. Confirm Docker Desktop starts.
3. Confirm the `greenhouse-server` and `greenhouse-cloudflared` containers come back.
4. Power-cycle each ESP32.
5. Confirm the app/API repopulates without manual intervention.

The ESP32 firmware already auto-runs from `boot.py` and `main.py`, and `main.py` resets
the board after unexpected failures. The firmware also keeps a short in-memory backlog so
if the PC or Docker takes a bit longer to start, the boards can flush pending readings
once the server is reachable again.

## Local Python testing

Docker is the main deployment path, but keeping Python available locally is still useful for testing.

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
