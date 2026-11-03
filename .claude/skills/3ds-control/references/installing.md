# Installing, updating and downgrading

## Versions

- AM refuses a CIA whose version is the **same as or older than** the installed one
  (`0xC8E083FC`). `3ds install` checks the TMD version first and skips such CIAs unless `--force`.
- 3DS Remote is title `000400000FE3D500` (`CTR-P-RMTE`). Its version is in `./VERSION`; releases are
  built by CI from tags (`tools/release.sh X.Y.Z`).
- `3ds update` downloads the latest GitHub release CIA and installs it over the running app; then
  `3ds launch 000400000FE3D500` jumps into the new version.
- A build installed for testing must get a version number higher than the installed one, and every
  later release must be higher still. Prefer testing with the `.3dsx` instead: Homebrew Launcher →
  `Y`, then `/opt/devkitpro/tools/bin/3dslink -a <3DS IP> 3ds-remote.3dsx` (no version involved).

## Downgrading (or reinstalling an older CIA) with FBI

AM will not go backwards, so remove the title first, then install the old CIA. Doing both in FBI
keeps the HOME Menu icon in its folder slot.

1. Open FBI (it lives in the user's Homebrew folder). Main menu → `Titles` (6 × DOWN, A).
2. The list is sorted by name; RIGHT/LEFT page through it. The top screen shows the selected
   title's ID, version and product code: confirm it before acting.
3. A → `Delete Title And Ticket` (2 × DOWN, A) → A to confirm → any button on "Title deleted".
4. B back to the main menu → `Remote Install` → `Receive URLs over the network`. FBI waits on
   TCP port 5000 (ftpd uses the same port, so it must not be running).
5. Send the URL(s) from the computer. The payload is a 4-byte big-endian length, then the URLs
   separated by newlines:

   ```python
   import socket, struct
   urls = b"https://github.com/carlbastos/3ds-remote/releases/download/v0.3.1/3ds-remote.cia"
   with socket.create_connection(("<3DS IP>", 5000), timeout=10) as s:
       s.sendall(struct.pack("!L", len(urls)) + urls)
   ```

6. FBI asks "Install from the received URL(s)?" → A. GitHub release URLs (with redirects) work.
   Wait for "Install finished", any button, then B, B, START to leave FBI.
