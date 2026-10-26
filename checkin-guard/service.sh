#!/system/bin/sh
MODDIR=${0%/*}
[ -e "$MODDIR/disable" ] && exit 0
sh "$MODDIR/guard.sh" daemon >/dev/null 2>&1 &
