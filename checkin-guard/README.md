# DBY-W09 Checkin Guard

Optional APatch module used after the [26 October recovery](../reports/2026-10-26-gsf-recovery.md).
Keep the existing IMEI fix, NeoZygisk and Vector enabled. This guard does not replace them.

It checks the last successful Google Checkin once per hour. If that success is at least 18 hours old, it requests
a normal Checkin. It retries at most hourly. Recent successful Checkins are left alone. It also records the
already-running compliance broker's status when available; `unknown` means that diagnostic service was not
loaded, not a denial. The guard never launches apps, rotates identities, clears data, changes certification flags,
or modifies Play Integrity/attestation. It does not hold a wake lock; offline or suspended devices can defer work.

The root-only log is `/data/adb/gms-checkin-guard/health.log`, rotated at about 32 KiB. It contains times and
health outcomes, not account names, device IDs or tokens. Google can still change its own server decision.

## Build and install

Zip the files inside this directory with `module.prop` at the archive root. Shell scripts must retain LF endings.
Install the ZIP with APatch Modules or `apd module install`, then reboot. APatch stages a newly installed module
under `modules_update` until the next boot.

Example using Python to build the ZIP from the repository root:

```python
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
source = Path('checkin-guard')
with ZipFile('checkin-guard.zip', 'w', ZIP_DEFLATED) as archive:
    for name in ('module.prop', 'skip_mount', 'service.sh', 'guard.sh', 'uninstall.sh'):
        archive.write(source / name, name)
```

## Check or stop it

Run these through `adb shell su -c`, or a root shell:

```sh
sh /data/adb/modules/gms_checkin_guard_dbyw09/guard.sh --status
sh /data/adb/modules/gms_checkin_guard_dbyw09/guard.sh --once
```

`--checkin-now` explicitly requests Checkin immediately, then checks whether the success timestamp advances.
It is a manual diagnostic command; the daemon uses the 18-hour threshold.

To stop it immediately and prevent startup at next boot:

```sh
touch /data/adb/modules/gms_checkin_guard_dbyw09/disable
sh /data/adb/modules/gms_checkin_guard_dbyw09/uninstall.sh
```

To restore it, enable the module in APatch and reboot, or run `apd module enable gms_checkin_guard_dbyw09` and
then its `service.sh`. Uninstalling it leaves the small diagnostic log and does not undo the GSF recovery.

## Validation

Six host policy tests: `python -m unittest discover -s tests -v` (Git Bash on Windows, or Bash on Linux).
The timing policy was also exercised with the device's actual mksh; epoch milliseconds are truncated as decimal
text before arithmetic to avoid Android's integer overflow. Device checks covered fresh-state no-op, a normal
Checkin, automatic startup after reboot, source/deployment hashes, duplicate-start suppression and immediate
stop/restart. A real observation beyond 25 hours remains outstanding.
