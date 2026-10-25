#!/system/bin/sh
# Grants the runtime permissions the Google sync adapters and GMS need on a fresh install.
# Without them contacts and calendar do not sync. Run as root: su -c sh grant-runtime-permissions.sh
g(){ p=$1; shift; for x in "$@"; do pm grant $p android.permission.$x 2>&1 | sed "s/^/$p $x: /"; done; }
g com.google.android.syncadapters.contacts GET_ACCOUNTS READ_CONTACTS WRITE_CONTACTS
g com.google.android.syncadapters.calendar READ_CALENDAR WRITE_CALENDAR READ_CONTACTS
g com.google.android.gms GET_ACCOUNTS READ_CONTACTS WRITE_CONTACTS ACCESS_FINE_LOCATION ACCESS_COARSE_LOCATION ACCESS_BACKGROUND_LOCATION READ_PHONE_STATE READ_EXTERNAL_STORAGE WRITE_EXTERNAL_STORAGE ACTIVITY_RECOGNITION
g com.google.android.gsf GET_ACCOUNTS READ_CONTACTS WRITE_CONTACTS READ_PHONE_STATE
g com.android.vending READ_PHONE_STATE
