package local.dbyw09.imeifix;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

// HarmonyOS routes TelephonyManager.getImei()/getDeviceId() to HwInnerTelephonyManager.getUniqueDeviceId(),
// which returns the literal "unknown" on this Wi-Fi-only tablet. AOSP returns null when there is no modem.
// Newer Play services reject "unknown" as an IMEI and checkin fails. This restores the AOSP null, nothing else.
public class Hook implements IXposedHookLoadPackage {
    private static final String[] METHODS = {"getImei", "getDeviceId", "getMeid"};

    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam lpparam) {
        if (!"com.google.android.gms".equals(lpparam.packageName)) return;
        for (String m : METHODS) {
            try {
                XposedHelpers.findAndHookMethod("android.telephony.TelephonyManager", lpparam.classLoader, m, new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) {
                        if ("unknown".equals(param.getResult())) param.setResult(null);
                    }
                });
            } catch (Throwable t) {
                XposedBridge.log("dbyw09-imeifix: " + m + ": " + t);
            }
        }
        XposedBridge.log("dbyw09-imeifix: hooked in " + lpparam.processName);
    }
}
