# Recovery from the Google app certification block, 26 October 2026

This is an experiment on one DBY-W09, HarmonyOS 4.2.0.208 (C00), Android 12/API 31, starting at commit `638191a`. It is not evidence that this firmware has become Google-certified. Times below are Europe/Istanbul (UTC+3). Raw logs, account state, identifiers, databases and APKs remain outside this public repository.

## What changed the outcome

The old Google Services Framework (GSF) identity continued to receive `uncertified_status=3` after successful Checkin. Allocating a new identity through the normal Google Checkin exchange, registering that identity at [Google's official uncertified-device page](https://www.google.com/android/uncertified/), and running Checkin again restored the Play Store interface. The owner also reported that the block was gone.

| Observation | Old identity | New identity, after registration |
|---|---|---|
| Checkin | SUCCESS | SUCCESS |
| GSF `uncertified_status` | `3` | `1` |
| GMS compliance service | Apps blocked | `shouldAllowGmsFunctionality=true`, `isProvisional=false` |
| Play Store cold launch | `UncertifiedDeviceActivity` | Store catalog and navigation loaded |

This comparison establishes a working recovery on this unit. It does **not** establish why Google stopped accepting the old identity, or prove that a new identity is necessary on other devices. Changing an identity and registering it are two changes; their individual long-term effects have not been isolated.

## Different mechanisms, different evidence

- **Checkin:** Google's registration/configuration exchange assigns an Android ID and security token and returns settings. A successful exchange does not establish permission to use every Google service. Here it succeeded while apps were blocked.
- **GSF registration:** The account owner registers their own GSF Android ID at Google's page. It is distinct from Android's app-scoped `Settings.Secure.ANDROID_ID`, and distinct from a manufacturer's device certification. The owner confirmed registering the new ID during this run. PC browser automation could not independently inspect the account page because its URL-confidence check blocked the operation.
- **Play Protect device certification:** Google's [certification help](https://support.google.com/googleplay/answer/7165974?hl=en) describes Android compatibility testing and licensed Google apps. The current [supported-device list](https://storage.googleapis.com/play_public/supported_devices.html) had no `DBY-W09`, `HWDBY`, or `MatePad 11` row when fetched during this run. No claim of certification is made.
- **Play Integrity:** This is an app/server API with separate app, account and device verdicts. Its [documented response](https://developer.android.com/google/play/integrity/verdicts) is not the `gmscompliance` response observed here. No Play Integrity verdict was collected, modified, or forged in this run.
- **GMS compliance and application checks:** The affected apps redirected to their bundled `com.google.android.gms.gmscompliance.ui.UncertifiedDeviceActivity`. GMS exposes its current software compliance result through the broker service dump below. [microG implements the corresponding software service separately](https://github.com/microg/GmsCore/blob/master/play-services-gmscompliance/core/src/main/kotlin/org/microg/gms/gmscompliance/GmsDeviceComplianceService.kt), further illustrating that it is not itself hardware key attestation.

Google also distinguishes device certification from its harmful-app scanner. Turning off the scanner is not a solution to this certification error. [Google Play Help](https://support.google.com/googleplay/answer/7165974?hl=en).

## Investigation and failed hypotheses

1. Confirmed current firmware, root, SELinux Enforcing, orange boot state, installed Google packages and systemless module layout. Old local reports from HarmonyOS 3/locked-bootloader and HarmonyOS 2/Android 10 describe earlier configurations and are not current evidence.
2. Confirmed Vector loads `local.dbyw09.imeifix` into GMS, including its persistent process. Its existing source changes only literal `"unknown"` telephony results to `null`, matching this Wi-Fi device's lack of a modem. It does not create an IMEI.
3. Triggered Checkin at 21:50:55: `SUCCESS`. Play Store at 21:51 still opened the block. Thus Checkin success alone was insufficient.
4. Tested the GSF provider's built-in one-key override with `uncertified_status=0`. The underlying main value stayed `3`; the override table contained `0`. Cold-starting Store and restarting GMS did not clear the block. Removed that individual override and verified that it was absent. A targeted GMS override broadcast also did not change the broker's effective value and was reversed. Neither override is part of the recovery.
5. Checked the local hosts file: only normal localhost entries. This rules out a local hosts-file block, not all router/DNS/network interference. Successful Checkin and later Store data loading provide stronger evidence for the endpoints actually exercised.
6. Inspected the installed GSF/GMS APKs locally, using the Android SDK's `dexdump`. Found the GSF override receiver, separate GMS identity-token storage, and the compliance broker's diagnostic fields. No APK was patched.

## Scoped identity reset and rollback

The owner explicitly suggested a new GSF identity. Before applying the reset, five files were backed up on the tablet in a root-only directory and on the PC. Binary transfers were checked with SHA-256; the GSF database passed SQLite integrity checking:

| File | Purpose |
|---|---|
| GSF `databases/gservices.db` | Old GSF Android ID and server settings |
| GSF `shared_prefs/CheckinService.xml` | Backup Checkin security token |
| GSF `files/security_token` | Binary backup token |
| GMS `shared_prefs/Checkin.xml` | Current ID, Checkin metadata and timing |
| GMS `files/checkin_id_token` | Current ID/token pair |

After stopping the affected apps, GMS and GSF, the experiment removed the GMS Checkin preference entries `android_id`, `CheckinService_accountsReceivedByServer`, `CheckinService_deviceDataVersionInfo`, `CheckinService_versionInfo`, and `CheckinTask_bookmark`. It removed the backup token preference from GSF, moved the two token files into the root-only checkpoint, and set the GSF **main** `android_id` value to `0` through the provider's `main_diff` URI. This was a request for fresh allocation; no invented nonzero identity was supplied. A normal Checkin then allocated a different ID and returned SUCCESS at 22:03:46.

The owner registered the new ID at Google's page. Another normal Checkin succeeded at 22:05:19, followed by a successful Store cold launch. Google account databases, app libraries, photos, boot images, firmware and hardware key stores were not reset.

The on-device checkpoint is `/data/adb/gmsdiag-20261026-newid-1/`. Its `rollback.sh` stops the relevant packages, restores the five originals with their metadata, restores file contexts, and requests Checkin. It was syntax-checked; restoring the rejected old identity after recovery was intentionally not tested. A restoration returns the old local state and may also return its original certification block. Do not publish or copy these identity/token backups to another device.

## Preventing another missed-Checkin failure

Keep **both** parts of the recovery:

1. The existing IMEI compatibility fix must remain enabled in Vector for `com.google.android.gms`; NeoZygisk and Vector must stay active. Otherwise the invalid `"unknown"` IMEI can break Checkin again after a GMS update/restart.
2. Keep the new, registered identity and successful Checkin state. Do not routinely clear GSF/GMS data or rotate IDs. The server's own Checkin interval after recovery was 42,185 seconds (about 11.7 hours), with a 10,800-second flex interval.

[`checkin-guard/`](../checkin-guard/) adds an APatch fallback. It reads only the last successful Checkin time once per hour. If no success has been recorded for 18 hours, it requests the same normal Checkin used in the manual test. Failed attempts are separated by at least one hour. It stores a bounded local health log without account names, IDs or tokens. It never resets identity, clears app data, changes certification flags, modifies attestation, or holds a wake lock. A powered-off/suspended/offline device may defer its next attempt until it can run again.

The first native-shell test caught Android mksh's millisecond arithmetic overflow. The released script drops the three decimal millisecond digits before arithmetic; the corrected native test reported a fresh Checkin with the expected age. Development logs were retained separately. Six policy tests cover fresh/stale thresholds, retry spacing, invalid state, clock rollback and real epoch timestamps.

The guard started automatically during the reboot at 22:13:43 and logged a fresh Checkin at 22:13:58. The new
GSF identity survived reboot. Immediate stop/restart and duplicate-start suppression were exercised, and the
deployed scripts were compared with their source hashes. Its local log now also records compliance diagnostic
fields when the broker service is loaded; an idle broker can legitimately produce `unknown` fields.
The final guard's explicit Checkin test at 22:29 advanced the success timestamp; the ID stayed unchanged,
`uncertified_status` stayed `1`, and no `android_id`/`uncertified_status` overrides remained. Final recovery and
guard artifacts were verified against their source before publication. The rollback test concerns stopping the
guard; the identity rollback checkpoint was retained without restoring the rejected old identity.

Health and manual recovery commands:

```sh
adb shell su -c 'sh /data/adb/modules/gms_checkin_guard_dbyw09/guard.sh --status'
adb shell su -c 'sh /data/adb/modules/gms_checkin_guard_dbyw09/guard.sh --once'
adb shell su -c 'sh /data/adb/modules/gms_checkin_guard_dbyw09/guard.sh --checkin-now'
adb shell dumpsys activity service com.google.android.gms/.chimera.PersistentBoundBrokerService
```

To disable the guard immediately, use the saved `rollback-guard.sh` in the checkpoint, or disable its APatch module and run its `uninstall.sh`. This does not undo the identity recovery or the IMEI fix.

The recovered GSF data included a timestamp of **27 October 2026, 23:03:46 UTC+3**. In the inspected local legacy control branch, value `1` is handled separately from value `2` plus expiration and value `3` denial. The compliance API also reported `isProvisional=false`. These are favorable current observations, **not a guarantee** of a future server decision. A real test beyond 25 hours is still required; changing the device clock would not be equivalent.

## Functional tests

After reboot, real application interfaces and content were tested, not merely package presence or Checkin:

| App or feature | Result and exact scope |
|---|---|
| Play Store | PASS: store catalog and the installed VLC app's details, developer, update information and controls loaded. Purchase/install/update transactions were not exercised. |
| Maps | PASS: rendered map tiles and location indicator; an explicit Istanbul query moved to Istanbul and loaded its place card and imagery. Navigation during travel was not tested. |
| Photos | PASS: account photo library, memories/thumbnails and an existing photo viewer with its controls opened. Backup upload, edit, delete and restore operations were not performed. |
| Google app | Main interface opened after clearing the stale activity task. A complete search transaction was not verified; one later attempt encountered the device lock screen. |
| Drive | Main file/navigation interface opened after clearing the stale task. File download/upload and editing were not tested. |
| Translate | Opened to its translation-history account/backup onboarding. Translation itself was not tested, and no backup setting was accepted. |
| IMEI fix | Remained loaded after reboot; original source/APK were not replaced. |
| Checkin guard | Automatic boot start, native timing decisions, fresh-state no-op, immediate stop/restart and single-instance behavior checked. |
| Actual behavior after 25 hours | NOT YET OBSERVED. Guard health logs continue locally; this must not be reported as passed. |

Some apps resumed an old `UncertifiedDeviceActivity` task even after the server response allowed GMS. A fresh
activity task (`am start -S -W -f 0x10008000 -n <launcher-component>`) opened Google/Drive's normal interfaces.
This clears that app's activity task, not its stored data. In UI tests, a successful `am start` was insufficient:
the resumed activity, current screenshot and a fresh hierarchy/content had to be checked. A failed hierarchy
dump can leave an old XML file, so stale dumps were excluded from the final results.

## Other approaches and limits

- **microG Huawei flavor:** Still a viable alternative to investigate, not disproven by an old unsupported firmware. The [maintainer requires Huawei DSC/signature compatibility](https://github.com/microg/GmsCore/issues/3847). The [latest release checked](https://github.com/microg/GmsCore/releases/tag/v0.3.17.252432) provides Huawei artifacts. The [Huawei implementation](https://github.com/microg/GmsCore/blob/master/fake-signature/src/huawei/java/com/huawei/signature/diff/SignatureService.java) is package-signature compatibility, not hardware attestation. Replacing the present GMS packages risks signature/data conflicts and needs its own migration rollback. It was not necessary for this recovery and was not installed.
- **GBox/GSpace or web apps:** Separate compatibility options, not tested in this run and not claimed to solve native GMS certification.
- **Systemless modules:** [Magisk's module documentation](https://topjohnwu.github.io/Magisk/guides.html) describes the systemless layout. This tablet uses APatch, not Magisk; changing root managers was unnecessary.
- **Firmware routes:** The [XDA DBY-W09 rebrand guide](https://xdaforums.com/t/comprehensive-matepad-11-2021-dby-w09-rebrand-update-and-root-guide.4789106/) was retrieved via Jina after a direct fetch failed. It documents firmware/root work, not proof of lasting Google certification. No firmware changes were made here.
- **Compatibility versus provider approval:** [AOSP compatibility requirements](https://source.android.com/docs/compatibility/overview) and Google's GMS licensing/certification are distinct from whether a software workaround executes. This run used the owner's device identity, normal Checkin and Google's registration mechanism. It did not establish licensed/certified OEM status or change Play Integrity.

## Audit of previous project restrictions

No applicable `AGENTS.md` or `CLAUDE.md` was found in the project or checked parent locations. Earlier local reports contain restrictions such as "no certification spoofing," "firmware changes conflict with project constraints," and requiring separate approval for destructive steps. The saved files alone do not establish which historical statements originated with the owner and which were agent conclusions.

For this run the owner's current explicit requirements govern: reversible software tests are authorized; backups precede significant changes; high-risk firmware/data-destructive changes require approval; stolen keys, borrowed device credentials and fabricated hardware attestation are excluded. A previous "no fix" statement was treated as a hypothesis. Missing OEM certification is a real limitation, but it does not prove all software compatibility paths impossible.
