package local.dbyw09.gmscompat;

public final class CompatPolicy {
    private CompatPolicy() {}
    public static boolean targetPackage(String name) {
        return "com.android.vending".equals(name) || "com.google.android.apps.maps".equals(name)
            || "com.google.android.apps.photos".equals(name);
    }
    public static boolean supports(String name, long version) {
        return ("com.android.vending".equals(name) && version == 85372430L)
            || ("com.google.android.apps.maps".equals(name) && version == 1068832648L)
            || ("com.google.android.apps.photos".equals(name) && version == 52549343L);
    }
    public static boolean skipStoreRedirect(Object decision) { return Boolean.FALSE.equals(decision); }
    public static boolean skipPhotosRedirect(String receiverClass) { return "akem".equals(receiverClass); }
}
