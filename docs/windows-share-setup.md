# Windows Archive Share Setup

The Raspberry Pi writes a weekly CSV into a shared folder on your second Windows PC.

## 1. Create the folder

- Create a folder such as `D:\GreenhouseArchive`.
- Make sure the drive has enough free space for the full season of CSV files.

## 2. Share it

- Right-click the folder.
- Open `Properties` -> `Sharing` -> `Advanced Sharing`.
- Share the folder as `GreenhouseArchive`.
- Grant a user account read/write access.

## 3. Find the network path

The Pi mount target will look like:

```text
\\WINDOWS-PC-NAME\GreenhouseArchive
```

## 4. Test from another machine

- Confirm the folder is reachable on the local network.
- Confirm the shared user can create and delete a test file.

## 5. Keep the PC awake during the scheduled dump

The default weekly export timing is Monday at `00:00` America/Toronto. The Windows archive PC must be awake and reachable at that time or the Pi will keep its local data and retry next week.
