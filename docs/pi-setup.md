# Raspberry Pi Zero 2 W Setup

This stack is designed to run unchanged on Windows for testing and on the Raspberry Pi for deployment.

## 1. Flash the Pi

- Use Raspberry Pi OS Lite.
- During imaging:
  - set the hostname to `greenhouse-pi`
  - configure WiFi
  - enable SSH
  - set the locale and timezone

## 2. First boot over SSH

```bash
ssh pi@greenhouse-pi.local
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip cifs-utils
```

## 3. Copy the project to the Pi

Clone the repository or copy the project folder into `/opt/greenhouse-project`.

```bash
sudo mkdir -p /opt/greenhouse-project
sudo chown "$USER":"$USER" /opt/greenhouse-project
cd /opt/greenhouse-project
git clone https://github.com/astrog1324V2/GreenHouse_Project.git .
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Configure environment variables

Create `/opt/greenhouse-project/.env`:

```bash
GREENHOUSE_HOST=0.0.0.0
GREENHOUSE_PORT=8000
GREENHOUSE_DB_PATH=/opt/greenhouse-project/data/greenhouse.db
GREENHOUSE_EXPORT_DIR=/opt/greenhouse-project/data/exports
GREENHOUSE_ARCHIVE_TEMP_DIR=/opt/greenhouse-project/data/exports/pending
GREENHOUSE_ARCHIVE_SHARE_DIR=/mnt/greenhouse-archive
GREENHOUSE_TIMEZONE=America/Toronto
GREENHOUSE_STALE_MINUTES=3
GREENHOUSE_UI_HISTORY_LIMIT=10
GREENHOUSE_ARCHIVE_PREFIX=greenhouse-weekly
```

## 5. Mount the Windows archive share

Follow [windows-share-setup.md](windows-share-setup.md), then mount the share on the Pi:

```bash
sudo mkdir -p /mnt/greenhouse-archive
sudo nano /etc/greenhouse-smb-credentials
```

Credentials file:

```text
username=YOUR_WINDOWS_USERNAME
password=YOUR_WINDOWS_PASSWORD
```

Lock it down:

```bash
sudo chmod 600 /etc/greenhouse-smb-credentials
```

Add to `/etc/fstab`:

```text
//WINDOWS-PC-NAME/GreenhouseArchive /mnt/greenhouse-archive cifs credentials=/etc/greenhouse-smb-credentials,uid=1000,gid=1000,iocharset=utf8,file_mode=0664,dir_mode=0775,nofail,x-systemd.automount 0 0
```

Mount now:

```bash
sudo systemctl daemon-reload
sudo mount -a
```

## 6. Install the systemd units

Copy the provided service and timer files:

```bash
sudo cp deploy/systemd/greenhouse-server.service /etc/systemd/system/
sudo cp deploy/systemd/greenhouse-archive.service /etc/systemd/system/
sudo cp deploy/systemd/greenhouse-archive.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now greenhouse-server.service
sudo systemctl enable --now greenhouse-archive.timer
```

## 7. Verify

```bash
systemctl status greenhouse-server.service
systemctl status greenhouse-archive.timer
curl http://127.0.0.1:8000/health
```

## 8. Manual archive test

```bash
cd /opt/greenhouse-project
source .venv/bin/activate
set -a
source .env
set +a
python scripts/archive_weekly.py
```

The CSV should appear on the Windows shared folder. The Pi database should purge only after the copy succeeds.
