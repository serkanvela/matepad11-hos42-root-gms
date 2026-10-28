# Certification block returned, 28 October 2026

Investigation started at about 09:34 Europe/Istanbul (UTC+3), roughly 35.5 hours after the 26 October identity
reset. This supersedes any interpretation of that reset as a durable recovery. Starting code revision: `9cd00f0`.

## Confirmed current state

- HarmonyOS 4.2.0.208/API 31 remains installed. GMS remains 26.41.31; the updated Play Store is 53.7.24.
- The GSF identity is **the same** one obtained and registered on 26 October. Its full value is kept private.
- GSF's server/configuration value is again `uncertified_status=3`; there is no status expiration field or local
  `android_id`/`uncertified_status` override in the baseline database. SQLite integrity checking passed.
- GMS recorded a successful Checkin at **06:23:35** today. Manual Checkins at **09:35:22** and **09:38:46** also
  returned SUCCESS. The first manual retry was followed by a database snapshot still containing status `3`.
- The guard daemon is running. Its retained log shows successful native Checkins on the preceding day, then
  `state=fresh last_success_age_s=617` and `compliance_status=3` at **06:33:52** today. No 18-hour stale-Checkin
  condition was needed to explain the recurrence. Power/suspend deferred some hourly samples, as documented.
- Cold launches and fresh UI evidence reproduce `UncertifiedDeviceActivity` in **Play Store, Photos and Maps**.
  Maps briefly resumed its main activity before redirecting; a one-second launch observation was insufficient.

Thus the Checkin transport fix and the locally retained identity persist, while the app access block has returned. A
successful Checkin is not evidence of continuing authorization/certification. The previous guard could not
prevent this failure mode because its recovery action is another normal Checkin, which currently succeeds
without removing the block.

## Reversible experiments

A private PC snapshot and root-only on-device checkpoint at `/data/adb/gmsdiag-20261028-recurrence-1/` were created
before changes. No identity reset, account removal, app-data wipe, firmware modification, key extraction or
attestation modification was performed.

| Hypothesis/test | Result |
|---|---|
| Checkin stopped working after an update | Not supported: repeated normal Checkins succeed; GMS version is unchanged. |
| Old compliance cache is the only cause | Backed up/moved only GMS's `files/gmscompliance/shared/cache.pb`, restarted GMS and Store. The block persisted. Restored the exact original cache and checked its SHA-256. |
| A stale GSF software status is sufficient to explain the block | Temporarily set only GSF main `uncertified_status=1` through `main_diff`. It did not unblock Store. After also restarting GMS/GSF, the broker dump saw `1`, but Store still blocked. Restored `3` after each control test. |
| Disabling only the error activity allows Store to continue | Store threw `ActivityNotFoundException` and exited. Restored the component to its manifest default, then confirmed the normal certification block instead of that induced crash. This is not a workaround. |

The broker initially printed a cached response with `shouldAllowGmsFunctionality=true` and `isProvisional=false`
even while Store blocked and its diagnostic Gservices value was `3`. After the cache/process refresh, the cached
response was null and the block remained. A cached dump does not prove that a fresh request or the full app
decision permits access. The 26 October `isProvisional=false` observation therefore did not establish permanence.

The legacy status timer initially recorded 27 October at 23:03:46. The owner reported recurrence after more than
24 hours, and denial is now confirmed. The available logs do not prove the exact transition time or why the
server/configuration changed from `1` to `3`. Registration recognition, identity-format/account correspondence,
and server eligibility remain separate hypotheses; none is established by this recurrence alone.

## Registration check still required

The owner previously confirmed registering the new ID on [Google's official page](https://www.google.com/android/uncertified/).
That confirmation is retained; the account's actual registered entry has not been independently read. The same
ID can be represented as decimal or hexadecimal, and the owner was asked which representation and Google account
were used. The next registration test should verify the **existing** ID/account entry rather than create another
identity. No assumption is made here that a specific format was accepted or that registering alone guarantees
access.

Windows Computer Use again refused browser inspection because it could not confidently determine Chrome's URL.
No Windows UI input was issued after that stop. This prevents independently checking the account page through
that interface; it does not prevent the ADB/device investigation.

## End state of this investigation

- Original GSF ID retained; status `3`; tested override entries absent.
- Original compliance cache restored byte-for-byte.
- Store's error activity restored to its manifest default; the deliberate test crash is gone.
- IMEI fix and guard left installed; guard process still active.
- Play Store, Photos and Maps remain blocked. **No lasting fix is claimed.**

Raw databases, tokens, account data, full package dumps and device screenshots are kept outside this public
repository. The checkpoint contains rollback scripts for the cache, status-key and component experiments.

## Subsequent application-side experiment

Later on 28 October, a separate version-limited Vector module restored the three applications, including a
Store download and reboot/control tests, while the same GSF identity remained at status 3. See the
[follow-up report](2026-10-28-app-compatibility.md). The earlier failed experiments above remain valid evidence;
the follow-up does not turn the Checkin guard into a certification solution.
