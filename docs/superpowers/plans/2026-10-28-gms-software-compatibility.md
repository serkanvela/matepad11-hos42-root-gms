# Google-app software compatibility experiment

The owner authorized reversible local compatibility work without repeated approval. Preserve accounts, the
registered GSF identity, the existing IMEI fix and the bootable firmware. Hardware credentials, fabricated
attestation and firmware changes are excluded. Back up Vector configuration before changing this module.

1. Record failing cold launches, current GSF identity/status and successful Checkin.
2. Inspect the installed APKs and test exact package/version boundaries before loading hooks.
3. Compare a GMS-only software-response experiment with client-side enforcement hooks. The GMS-only experiment
   failed; client hooks restored the requested applications.
4. Remove ineffective service/parcel hooks from the final design. Version 0.5 contains only the three inspected
   client UI hooks, scoped to Play Store, Maps and Photos. Keep the existing IMEI fix unchanged.
5. Verify Store content/download, Maps search/tiles and Photos library/viewer. Keep private diagnostic artifacts
   outside the public repository.
6. Uninstall the new module and reboot for a negative control; reinstall the minimal module and reboot for the
   positive control. Verify the same registered identity, status 3, a successful new Checkin and exact scopes.
7. Publish the implementation and measured results with a simple APK-uninstall rollback. Distinguish immediate
   and reboot success from a still-pending observation beyond 25 hours and from OEM/Play Integrity certification.
