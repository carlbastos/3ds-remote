# Power, crashes and recovery

## Reboot and shutdown

- `3ds reboot` (v0.3.2+) uses `APT_HardwareResetAsync`, the same path as Rosalina's menu and the
  HOME Menu. The console leaves the network within ~2 s and answers ping again after ~23 s.
  Older builds used `PTMSYSM_RebootAsync(0)`, which force-kills every process and then waits forever.
- `3ds shutdown` sends the POWER-button notification (0x203). The console stays off; only the user
  can turn it back on.
- After either, **everything is off**: 3DS Remote, NTR-HR and InputRedirection all need the user
  again (see the table in SKILL.md). Tell the user what to reopen.
- To confirm a reboot from the computer: watch `ping` drop and come back. If it never comes back
  within ~60 s, the console is probably on a crash screen.

## Crash screens

- Luma's red "An exception occurred" screen (seen once, in `rosalina`, during a reboot) shows
  registers and a stack dump. Ask the user to press **A** to save the dump to
  `/luma/dumps/arm11/` (any other button powers off). With ftpd or 3DS Remote running later, fetch
  the `.dmp` for analysis.
- While a crash screen is up nothing on the network answers; NTR's port may still accept TCP
  connections without sending frames.

## What only the user can do

- Anything when the console is frozen or off: hold POWER ~10 s to force it off, then turn it on.
- Starting NTR-HR, enabling InputRedirection, opening 3DS Remote after a boot.
- Physical buttons InputRedirection cannot reach (POWER, the 3D slider, the volume slider).
