package local.dbyw09.gmscompat;

import android.content.Context;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import java.util.concurrent.atomic.AtomicBoolean;

// Local application UI compatibility only. No service, identity, attestation or parcel hooks.
public final class Hook implements IXposedHookLoadPackage {
    private final AtomicBoolean installed = new AtomicBoolean(false);
    @Override
    public void handleLoadPackage(final XC_LoadPackage.LoadPackageParam pkg) {
        if (!CompatPolicy.targetPackage(pkg.packageName)) return;
        XposedHelpers.findAndHookMethod("android.app.Application", pkg.classLoader, "attach", Context.class,
            new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    Context context = (Context) param.args[0];
                    long version = context.getPackageManager().getPackageInfo(context.getPackageName(), 0).getLongVersionCode();
                    if (!pkg.packageName.equals(context.getPackageName()) || !CompatPolicy.supports(pkg.packageName, version)) {
                        XposedBridge.log("dbyw09-gmscompat: unsupported package/version; no policy hooks installed");
                        return;
                    }
                    if (!installed.compareAndSet(false, true)) return;
                    install(pkg.classLoader, pkg.packageName);
                }
            });
    }
    private void install(ClassLoader loader, String packageName) {
        try {
            if ("com.android.vending".equals(packageName)) {
                // 85372430: callback only redirects to UncertifiedDeviceActivity and finishes MainActivity.
                XposedHelpers.findAndHookMethod("sho", loader, "lU", Object.class, new XC_MethodHook() {
                    @Override
                    protected void beforeHookedMethod(MethodHookParam param) {
                        if (CompatPolicy.skipStoreRedirect(param.args[0])) {
                            param.setResult(null);
                            XposedBridge.log("dbyw09-gmscompat: skipped Store local compliance redirect");
                        }
                    }
                });
            } else if ("com.google.android.apps.maps".equals(packageName)) {
                // 1068832648: inspected ENFORCE/DO_NOT_ENFORCE wrapper used by the local UI gate.
                XposedHelpers.findAndHookMethod("bfef", loader, "a", new XC_MethodHook() {
                    @Override
                    protected void beforeHookedMethod(MethodHookParam param) { param.setResult(Boolean.FALSE); }
                });
            } else {
                // 52549343: merged callback has many uses. Only the IpProtectionCheck receiver is skipped.
                XposedHelpers.findAndHookMethod("agpx", loader, "a", "cahx", new XC_MethodHook() {
                    @Override
                    protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                        java.lang.reflect.Field field = param.thisObject.getClass().getDeclaredField("a");
                        field.setAccessible(true);
                        Object receiver = field.get(param.thisObject);
                        if (receiver != null && CompatPolicy.skipPhotosRedirect(receiver.getClass().getName())) {
                            param.setResult(null);
                            XposedBridge.log("dbyw09-gmscompat: skipped Photos local compliance redirect");
                        }
                    }
                });
            }
            XposedBridge.log("dbyw09-gmscompat: local UI gate hook installed in " + packageName);
        } catch (Throwable error) {
            XposedBridge.log("dbyw09-gmscompat: local UI gate hook unavailable: " + error);
        }
    }
}
