# 28 October 2026: application-side compatibility after recurrence

## Measured outcome

Play Store, Maps and Photos became usable on the tested DBY-W09 after installing the separate
`local.dbyw09.gmscompat` Vector module. The final version 0.5 acts only inside these three applications.
The same registered GSF identity remains in use, `uncertified_status` remains **3**, and a fresh normal Checkin
succeeded at 10:47:53 +03:00. No identity rotation or new registration was performed during this recovery.

This supersedes the blocked end state of the [earlier investigation](2026-10-28-recurrence.md), not its evidence
that the Checkin guard failed to prevent the recurrence. Checkin health and application enforcement are distinct.

## Tests on the real device

| Test | Observed result |
|---|---|
| Original block, before module | All three apps redirected to `UncertifiedDeviceActivity` |
| GMS-only response/predicate experiment | Insufficient; Store remained blocked |
| Store response-constructor experiment | Insufficient; Store remained blocked |
| Store's inspected redirect callback adapted | Store opened catalog and VLC details |
| Maps and Photos inspected local gates adapted | Maps search/tiles and Photos gallery opened |
| Negative control: uninstall new module and reboot | Store, Maps and Photos all blocked again, same GSF ID, status 3 |
| Positive control: install minimal v0.5, enable exact three scopes, reboot | All three cold launches stayed in their normal application interfaces |
| Store download with final v0.5 | Fresh Google Calculator install from Store; package manager records `installerPackageName=com.android.vending`, first install 10:47:45 +03:00 |
| Maps | Istanbul search/place card/tiles in first experiment; a different Ankara search and populated map after final reboot |
| Photos | Existing local gallery and full-screen photo viewer opened; existing Google account recognized and backup onboarding reached. Backup was not started; no edits or deletion. |
| Identity/configuration preservation | Registered identity unchanged, status 3, GSF and Vector SQLite integrity checks `ok` |
| Checkin after final reboot | Guard's explicit normal Checkin test reported success |
| Host checks | Seven tests passed; SDK build succeeded; own APK v3 signature verified |
| New observation beyond 25 hours | **Pending**, not claimed as passed |

Screenshots, original APKs, account details and database snapshots are private and are not included here.
The Photos viewer screenshot also captured a GMS uncertified-device notification. The local workaround does not
suppress that separate notification or assert that the device is certified.

## Final implementation and scope

See [source/build/rollback instructions](../gmscompat/README.md). Inspected versions:

- Play Store `85372430`: `sho.lU(Object)` only handles the local compliance result by opening the error activity
  and finishing the main activity. Skip that callback only for Boolean false.
- Maps `1068832648`: `bfef.a()` is the local enforcement predicate for the ENFORCE/DO_NOT_ENFORCE wrapper.
- Photos `52549343`: the merged `agpx.a(cahx)` callback also serves unrelated functions. Skip it only when its
  receiver field is exactly class `akem`, the IpProtectionCheck handler that opens the error activity and closes
  the original activity. Other callback receivers continue normally.

Hooks are installed after Application.attach obtains the actual package/version. Unsupported versions and
other packages install no policy hooks. Version 0.5 removes the earlier GMS response/predicate experiment and
all parcel/response-constructor hooks. The new module is **not scoped to GMS**. The original `imeifix` remains
separately enabled for GMS, and the existing Checkin guard remains installed.

There are no hardware key operations, borrowed credentials, fabricated hardware attestation, property spoofing,
Google APK resigning, GSF status overrides or scheduled identity resets in the final module. It is an unofficial
local compatibility workaround. Google registration, OEM certification, Play Integrity and individual server
operations remain separate mechanisms; this experiment does not establish provider approval or a global
server-side eligibility change.

Final APK SHA-256:
`cd7e92fc85db293def9e9df9ddb32ec9d96d09ca3f9a26c98fba207b57eca0ff`.

## Rollback and recurrence limits

Before enabling the experiment, Vector configuration was backed up on-device and on the PC. The installed
Google apps and their user data were retained. Vector's parasitic manager had an independent class-loading
failure; a limited transaction through Android SQLite modified only this module's record and its scopes.
The final scope query confirms exactly Store, Maps and Photos for this module, and GMS for the existing IMEI fix.

Uninstall `local.dbyw09.gmscompat` and reboot to remove the workaround. That rollback was exercised in the
negative control and the original block returned. The final minimal module was then installed/enabled again
and its reboot behavior tested. The two earlier test-only response hooks are not present in the final APK.

There is no 24-hour expiry in this module; it works while the original denial is already active. This is stronger
immediate evidence than a fresh-ID grace period, but it is not a passed multi-day observation. Future app
updates can change the obfuscated hooks: exact-version guarding intentionally stops adaptation then.
Automatic-update preferences were left unchanged. Google-side changes may also affect operations independently.
Cloud photo backup/synchronization, payments, banking, Play Integrity and all other Google applications have not
been established as passing by these tests. The successful Store download and map search demonstrate useful
network operations; a locally displayed photo alone is not proof of cloud sync.
