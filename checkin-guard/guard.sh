#!/system/bin/sh
# A fallback for missed checkins, not a certification bypass or an ID reset.

checkin_decision() {
    case "$1:$2:$3" in *[!0-9:]*|:*|*::*|*:) echo unknown; return ;; esac
    [ "$1" -gt 0 ] || { echo unknown; return; }
    # Android mksh arithmetic can wrap epoch milliseconds at 32 bits.
    # Drop the three decimal millisecond digits before doing arithmetic.
    last_sec=${2%???}
    case "$last_sec" in ''|0) echo unknown; return ;; esac
    [ "$last_sec" -le $(($1 + 300)) ] || { echo clock_skew; return; }
    [ $(($1 - last_sec)) -ge 64800 ] || { echo fresh; return; }
    [ "$3" -eq 0 ] || [ $(($1 - $3)) -ge 3600 ] || { echo backoff; return; }
    echo stale
}

read_success_ms() {
    sed -n 's/.*name="CheckinService_lastCheckinSuccessTime" value="\([0-9]*\)".*/\1/p' \
        /data/user/0/com.google.android.gms/shared_prefs/Checkin.xml 2>/dev/null | head -n 1
}

guard_pause() {
    sleep "$1" &
    guard_sleep_pid=$!
    wait "$guard_sleep_pid"
    guard_sleep_pid=
}

guard_stop() {
    trap - TERM INT
    [ -z "${guard_sleep_pid:-}" ] || kill "$guard_sleep_pid" 2>/dev/null
    guard_log 'guard_stopped'
    exit 0
}

guard_log() {
    # Only times and health outcomes; never account names, IDs, or tokens.
    if [ -f "$STATE/health.log" ] && [ "$(wc -c < "$STATE/health.log")" -gt 32768 ]; then
        mv -f "$STATE/health.log" "$STATE/health.previous.log"
    fi
    printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >> "$STATE/health.log"
}

guard_tick() {
    now=$(date +%s)
    last_ms=$(read_success_ms)
    attempt=0
    [ ! -f "$STATE/last_attempt" ] || read -r attempt < "$STATE/last_attempt"
    decision=$(checkin_decision "$now" "$last_ms" "$attempt")
    age=unknown
    case "$last_ms" in ''|*[!0-9]*) ;; *) success_sec=${last_ms%???}; age=$((now - success_sec)) ;; esac
    guard_log "state=$decision last_success_age_s=$age"
    # Record the already-running broker's verdict without launching any app.
    # If it has not loaded this service, the fields remain unknown.
    broker=$(dumpsys activity service com.google.android.gms/.chimera.PersistentBoundBrokerService 2>/dev/null)
    compliance=$(printf '%s\n' "$broker" | sed -n 's/.*Gservices uncertified_status: \([0-9][0-9]*\).*/\1/p' | head -n 1)
    allow=$(printf '%s\n' "$broker" | sed -n 's/.*shouldAllowGmsFunctionality=\(true\|false\).*/\1/p' | head -n 1)
    guard_log "compliance_status=${compliance:-unknown} api_allow=${allow:-unknown}"
    [ "$decision" = stale ] || [ "${1:-}" = --checkin-now ] || return 0
    printf '%s\n' "$now" > "$STATE/last_attempt"
    if am broadcast -a android.provider.Telephony.SECRET_CODE \
        -d android_secret_code://2432546 -p com.google.android.gms >/dev/null 2>&1; then
        guard_log 'checkin_requested'
        guard_pause 15
        after_ms=$(read_success_ms)
        case "$after_ms" in
            ''|*[!0-9]*) guard_log 'checkin_result=unknown' ;;
            *) after_sec=${after_ms%???}
               before_sec=${last_ms%???}
               if [ "$after_sec" -gt "${before_sec:-0}" ]; then
                   guard_log 'checkin_result=success'
               else
                   guard_log 'checkin_result=pending_or_failed'
               fi ;;
        esac
    else
        guard_log 'checkin_request=failed'
    fi
}

guard_main() {
    MODDIR=${0%/*}
    STATE=/data/adb/gms-checkin-guard
    umask 077
    mkdir -p "$STATE"
    case "${1:-}" in
        --once|--checkin-now) guard_tick "${1:-}"; return ;;
        --status) tail -n 24 "$STATE/health.log" 2>/dev/null; return ;;
        daemon) ;;
        *) echo 'Usage: guard.sh daemon|--once|--status|--checkin-now'; return 2 ;;
    esac
    if [ -f "$STATE/pid" ]; then
        read -r old_pid < "$STATE/pid"
        case "$old_pid" in
            ''|*[!0-9]*) ;;
            *) old_command=$(ps -p "$old_pid" -o ARGS= 2>/dev/null)
               case "$old_command" in *"$MODDIR/guard.sh daemon"*) return 0 ;; esac ;;
        esac
    fi
    printf '%s\n' "$$" > "$STATE/pid"
    trap guard_stop TERM INT
    guard_log 'guard_started interval_s=3600 stale_after_s=64800'
    while [ "$(getprop sys.boot_completed)" != 1 ]; do guard_pause 15; done
    while [ ! -e "$MODDIR/disable" ] && [ ! -e "$MODDIR/remove" ]; do
        guard_tick
        guard_pause 3600
    done
    guard_log 'guard_disabled'
}

case "$0" in */guard.sh) guard_main "$@" ;; esac
