# Windows Server Setup

Use this when the greenhouse server runs in Docker Desktop on the always-on Windows PC.

## 1. Install the project dependencies for local testing

Docker is the main deployment path, but keeping Python available locally is still useful for testing.

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Start the container with Docker Desktop

From the project root:

```powershell
docker compose up -d --build
```

This starts the greenhouse server container and maps:

```text
http://<windows-pc-ip>:8000/
```

to the dashboard.

The API endpoint for the ESP32 boards is:

```text
http://<windows-pc-ip>:8000/api/v1/readings
```

The SQLite database and exports stay on the Windows PC in the project `data` folder through the Docker bind mount.

## 3. Point both ESP32 boards at the Windows PC

Update:

- `esp32/boards/greenhouse/app_config.py`
- `esp32/boards/outdoor/app_config.py`

Set:

- `SERVER_URL = "http://<windows-pc-ip>:8000/api/v1/readings"`

Leave:

- `TEMP_WINDOWS_SERVER_URL = None`

unless you want `component_test` mode to post somewhere different.

Difference between the two settings:

- `SERVER_URL` is the normal upload target for `summer` and `range_test`
- `TEMP_WINDOWS_SERVER_URL` is only an optional override for `component_test`

If `TEMP_WINDOWS_SERVER_URL` is blank or `None`, `component_test` automatically falls back to `SERVER_URL`.

## 4. Allow the port through Windows Firewall

If another device cannot open the dashboard or post data, allow inbound TCP `8000` on the Windows PC.

## 5. Make Docker Desktop start with Windows

In Docker Desktop settings, enable start-on-login.

The greenhouse container uses:

```yaml
restart: unless-stopped
```

so once Docker Desktop starts, the server container will start automatically with your other containers.

Important limitation:

- Docker Desktop normally starts when your Windows user session starts
- if you need services to come up before user login, a native Windows service or Scheduled Task is more reliable than Docker Desktop alone

## 6. Verify outage recovery

Test one full restart cycle before leaving it unattended:

1. reboot the Windows PC
2. confirm Docker Desktop starts
3. confirm the `greenhouse-server` container comes back automatically
4. power-cycle each ESP32
5. confirm the dashboard repopulates without manual intervention

The ESP32 firmware already auto-runs from `boot.py` and `main.py`, and `main.py` resets the board after unexpected failures. The firmware also keeps a short in-memory backlog so if the PC or Docker takes a bit longer to start, the boards can flush pending readings once the server is reachable again.
