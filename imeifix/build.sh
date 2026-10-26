#!/bin/sh
# Builds imeifix.apk with the Android SDK command-line tools (build-tools 36, platform android-36) and a JDK 17.
# The stub/ classes are compile-only: the real Xposed API comes from the framework (Vector/LSPosed) at run time.
# Usage: SDK=/path/to/Android/Sdk sh build.sh      (Git Bash on Windows works too)
set -e
SDK=${SDK:-$LOCALAPPDATA/Android/Sdk}
BT=$SDK/build-tools/36.0.0
AJ=$SDK/platforms/android-36/android.jar
EXE=; [ -f "$BT/aapt2.exe" ] && EXE=.exe
D8=$BT/d8; [ -f "$BT/d8.bat" ] && D8=$BT/d8.bat
SIGN=$BT/apksigner; [ -f "$BT/apksigner.bat" ] && SIGN=$BT/apksigner.bat
SEP=:; [ -n "$EXE" ] && SEP=';'
rm -rf build && mkdir -p build/stubc build/c build/dex
javac -source 8 -target 8 -nowarn -cp "$AJ" -d build/stubc $(find stub -name '*.java')
javac -source 8 -target 8 -nowarn -cp "$AJ${SEP}build/stubc" -d build/c $(find src -name '*.java')
"$D8" --release --lib "$AJ" --classpath build/stubc --min-api 31 --output build/dex $(find build/c -name '*.class')
"$BT/aapt2$EXE" compile --dir res -o build/res.zip
"$BT/aapt2$EXE" link -I "$AJ" --manifest AndroidManifest.xml -A assets -o build/base.apk build/res.zip
# add classes.dex without recompressing resources.arsc (must stay stored for targetSdk 30+)
PY="python3"; python3 -c 1 2>/dev/null || PY="py -3"
$PY - <<'PY'
import zipfile
src = zipfile.ZipFile('build/base.apk'); out = zipfile.ZipFile('build/unsigned.apk', 'w')
for i in src.infolist(): out.writestr(i, src.read(i))
out.write('build/dex/classes.dex', 'classes.dex', compress_type=zipfile.ZIP_DEFLATED); out.close()
PY
"$BT/zipalign$EXE" -f -p 4 build/unsigned.apk build/aligned.apk
[ -f key.jks ] || keytool -genkeypair -keystore key.jks -alias imeifix -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass imeifix-local -keypass imeifix-local -dname "CN=imeifix-local"
"$SIGN" sign --ks key.jks --ks-pass pass:imeifix-local --ks-key-alias imeifix --out imeifix.apk build/aligned.apk
echo "built: imeifix.apk"
