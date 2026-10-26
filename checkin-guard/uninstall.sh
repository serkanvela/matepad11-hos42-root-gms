#!/system/bin/sh
STATE=/data/adb/gms-checkin-guard
[ -f "$STATE/pid" ] || exit 0
read -r guard_pid < "$STATE/pid"
case "$guard_pid" in ''|*[!0-9]*) exit 0 ;; esac
guard_command=$(ps -p "$guard_pid" -o ARGS= 2>/dev/null)
case "$guard_command" in
    *'/gms_checkin_guard_dbyw09/guard.sh daemon'*) kill "$guard_pid" ;;
    *) exit 0 ;;
esac
# The daemon's TERM trap stops its own sleep child before exiting.
waits=0
while [ "$waits" -lt 10 ]; do
    guard_command=$(ps -p "$guard_pid" -o ARGS= 2>/dev/null)
    case "$guard_command" in *'/gms_checkin_guard_dbyw09/guard.sh daemon'*) ;; *) exit 0 ;; esac
    sleep 1
    waits=$((waits + 1))
done
# This is only our already-verified daemon, never an app or system service.
guard_command=$(ps -p "$guard_pid" -o ARGS= 2>/dev/null)
case "$guard_command" in *'/gms_checkin_guard_dbyw09/guard.sh daemon'*) kill -9 "$guard_pid" ;; esac
# Retain the small health log for diagnosis.
