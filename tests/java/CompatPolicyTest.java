import local.dbyw09.gmscompat.CompatPolicy;

public final class CompatPolicyTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        String[] packages = {"com.android.vending", "com.google.android.apps.maps", "com.google.android.apps.photos"};
        long[] versions = {85372430L, 1068832648L, 52549343L};
        for (int i = 0; i < packages.length; i++) {
            check(CompatPolicy.targetPackage(packages[i]), "expected client scope");
            check(CompatPolicy.supports(packages[i], versions[i]), "inspected client version");
            check(!CompatPolicy.supports(packages[i], versions[i] + 1), "unknown version must fail closed");
            check(!CompatPolicy.supports(packages[i], versions[(i + 1) % 3]), "package-specific versions");
        }
        for (String name : new String[]{null, "android", "com.google.android.gms", "com.example.app"}) {
            check(!CompatPolicy.targetPackage(name), "other processes excluded");
            check(!CompatPolicy.supports(name, 264131029L), "no service/system hooks");
        }
        check(CompatPolicy.skipStoreRedirect(Boolean.FALSE), "known redirect decision");
        for (Object value : new Object[]{null, Boolean.TRUE, "false", Integer.valueOf(0)}) {
            check(!CompatPolicy.skipStoreRedirect(value), "unrelated callback values must pass through");
        }
        check(CompatPolicy.skipPhotosRedirect("akem"), "inspected compliance receiver");
        check(!CompatPolicy.skipPhotosRedirect(null), "null receiver");
        check(!CompatPolicy.skipPhotosRedirect("aksw"), "backup callback must remain active");
        check(!CompatPolicy.skipPhotosRedirect("akem$1"), "no prefix matching");
        System.out.println("PASS: package/version boundary and selective local UI callbacks");
    }
}
