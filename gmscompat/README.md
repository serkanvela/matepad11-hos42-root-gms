# DBY-W09 local Google-app UI compatibility

Version 0.5 is a separate legacy Xposed APK for Vector 2.2 on the tested DBY-W09 / Android 12 installation.
It prevents three inspected application-side compliance decisions from redirecting to
`UncertifiedDeviceActivity` and closing the usable application. It does not certify the device.

| Package | Required version code | Local hook |
|---|---:|---|
| `com.android.vending` | 85372430 | `sho.lU(Object)`: skip the redirect-only callback when its input is Boolean false |
| `com.google.android.apps.maps` | 1068832648 | `bfef.a()`: return false for the local enforcement predicate |
| `com.google.android.apps.photos` | 52549343 | `agpx.a(cahx)`: skip only when receiver field `a` is exactly class `akem`, the IpProtectionCheck handler |

The versions and callback bodies were inspected in the installed APKs. Unknown versions install no policy hooks.
Photos shares its callback class with unrelated functions; receiver matching deliberately excludes those functions.
The module has no Internet permission, background service, scheduled task or data-reset logic.

The final module is scoped to **these three apps only**. It contains no GMS service hooks, parcel/response rewriting,
GSF database writes, device-property overrides, signing-identity changes or hardware/Play Integrity hooks.
Keep the existing IMEI fix separately scoped to `com.google.android.gms`; it solves a different Checkin failure.
Google APKs retain their original signatures. This is an unofficial local workaround, not a Google-approved
certification procedure, and it cannot guarantee that Google servers will accept every operation.

## Build and activate

Requires JDK 17 and Android SDK platform 36 / build-tools 36.0.0. Run from this repository:

```sh
python -m unittest discover -s tests
python gmscompat/build.py --sdk /absolute/android-sdk --out /absolute/private/new-build-dir --keystore /absolute/private/gmscompat-local.jks
adb install -r /absolute/private/new-build-dir/gmscompat.apk
```

The output directory must not already exist. Preserve the private local APK-signing keystore outside Git for
future updates. It is solely this module's signing key, unrelated to device or Google credentials. Xposed stubs
from `imeifix/stub` are compile-only and are excluded from the APK. The installed IMEI module is not rebuilt.

In Vector, enable `local.dbyw09.gmscompat` for Play Store, Maps and Photos, user 0, and restart those apps/reboot.
Do not include the Android framework or arbitrary apps. On the tested unit, Vector's parasitic manager failed
with a class-loading error; a narrowly targeted Android SQLite transaction configured only this module after
backing up Vector's database. Do not overwrite a live Vector database with a PC-edited copy.

## Verification and rollback

See [the device experiment](../reports/2026-10-28-app-compatibility.md). Test application content and an actual
Store download; the absence of the warning alone is insufficient. Reboot and cold-launch all three apps.

Remove the module with Android Settings or:

```sh
adb shell su -c 'pm uninstall local.dbyw09.gmscompat'
adb reboot
```

Uninstalling only this APK and restarting the affected processes removes its hooks. It does not clear Google
accounts, photo libraries or application data. On this device, uninstall/reboot brought the original block back;
reinstalling/enabling the module and rebooting restored application access.

## Persistence limits

The final code has no 24-hour expiry and does not depend on allocating a fresh GSF ID. It works in the tested
state while `uncertified_status=3` is already present. A new observation lasting more than 25 hours is still pending.
Future app updates can change the inspected methods; the version guard then leaves the app untouched and the
block may return. Automatic update settings were not changed. Reinspect and rebuild for new versions; do not
remove the version guard or claim universal compatibility. Cloud backup, banking, payments and Play Integrity
are outside the passing tests.
