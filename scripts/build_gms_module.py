# Builds the minimal systemless GMS module from the official MindTheGapps 12.1 arm64 zip.
# Nothing is downloaded or modified: the listed files are copied byte for byte (stored, not recompressed).
# Usage: python build_gms_module.py MindTheGapps-12.1.0-arm64-20231025_200924.zip gms12_systemless.zip
import sys, zipfile, hashlib

MTG_SHA256 = '8df6bc0b19660ca1586f0a65d3c0eb21554d6bf65d78fd1cd94a30df457cdc70'
FILES = [
    'system/product/app/GoogleCalendarSyncAdapter/GoogleCalendarSyncAdapter.apk',
    'system/product/app/GoogleContactsSyncAdapter/GoogleContactsSyncAdapter.apk',
    'system/product/etc/default-permissions/default-permissions-google.xml',
    'system/product/etc/permissions/privapp-permissions-google-product.xml',
    'system/product/etc/sysconfig/google-hiddenapi-package-allowlist.xml',
    'system/product/etc/sysconfig/google.xml',
    'system/product/etc/sysconfig/google_build.xml',
    'system/product/priv-app/GmsCore/GmsCore.apk',
    'system/product/priv-app/GooglePartnerSetup/GooglePartnerSetup.apk',
    'system/product/priv-app/Phonesky/Phonesky.apk',
    'system/system_ext/etc/permissions/privapp-permissions-google-system-ext.xml',
    'system/system_ext/priv-app/GoogleServicesFramework/GoogleServicesFramework.apk',
]
# On HOS 4.2 /product and /system_ext are symlinks into /system, so system/product/... is the right module path.
PROP = '''id=gms12_systemless_dbyw09
name=Google Mobile Services (MindTheGapps 12.1.0 arm64, systemless)
version=12.1.0-20231025
versionCode=1
author=matepad11-hos42-root-gms (files: MindTheGapps, signed by Google)
description=GmsCore, GSF, Play Store, PartnerSetup, contacts/calendar sync, priv-app permissions. Does not modify the system partition.
'''

src, dst = sys.argv[1], sys.argv[2]
h = hashlib.sha256()
with open(src, 'rb') as f:
    for c in iter(lambda: f.read(8 << 20), b''):
        h.update(c)
if h.hexdigest() != MTG_SHA256:
    sys.exit(f'ERROR: {src} sha256 {h.hexdigest()} is not the expected MindTheGapps 12.1.0 20231025 zip')
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w', zipfile.ZIP_STORED) as zo:
    zo.writestr('module.prop', PROP)
    for name in FILES:
        data = zi.read(name)
        zo.writestr(name, data)
        print(f'{hashlib.sha256(data).hexdigest()}  {name}')
print('written:', dst)
