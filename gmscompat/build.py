"""Build this separate module with SDK tools; never package the compile-only Xposed stubs."""
import argparse
import os
from pathlib import Path
import subprocess
import zipfile


def build(sdk, output, keystore):
    source = Path(__file__).resolve().parent
    sdk, output, keystore = Path(sdk).resolve(), Path(output).resolve(), Path(keystore).resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in ("stubs", "classes", "dex"):
        (output / name).mkdir()
    bt = sdk / "build-tools" / "36.0.0"
    android = sdk / "platforms" / "android-36" / "android.jar"
    suffix = ".exe" if os.name == "nt" else ""

    def run(*args):
        subprocess.run([str(a) for a in args], check=True)

    stub_files = sorted((source.parent / "imeifix" / "stub").rglob("*.java"))
    run("javac", "-source", "8", "-target", "8", "-nowarn", "-cp", android, "-d", output / "stubs", *stub_files)
    run("javac", "-source", "8", "-target", "8", "-nowarn", "-cp", str(android) + os.pathsep + str(output / "stubs"),
        "-d", output / "classes", *sorted((source / "src").rglob("*.java")))
    run("java", "-cp", bt / "lib" / "d8.jar", "com.android.tools.r8.D8", "--release", "--lib", android,
        "--classpath", output / "stubs", "--min-api", "31", "--output", output / "dex",
        *sorted((output / "classes").rglob("*.class")))
    run(bt / ("aapt2" + suffix), "compile", "--dir", source / "res", "-o", output / "res.zip")
    run(bt / ("aapt2" + suffix), "link", "-I", android, "--manifest", source / "AndroidManifest.xml", "-A", source / "assets",
        "-o", output / "base.apk", output / "res.zip")
    with zipfile.ZipFile(output / "base.apk") as src, zipfile.ZipFile(output / "unsigned.apk", "w") as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item))
        dst.write(output / "dex" / "classes.dex", "classes.dex", compress_type=zipfile.ZIP_DEFLATED)
    run(bt / ("zipalign" + suffix), "-f", "-p", "4", output / "unsigned.apk", output / "aligned.apk")
    if not keystore.exists():
        keystore.parent.mkdir(parents=True, exist_ok=True)
        run("keytool", "-genkeypair", "-keystore", keystore, "-alias", "gmscompat", "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000", "-storepass", "dbyw09-local", "-keypass", "dbyw09-local", "-dname", "CN=dbyw09-gmscompat-local")
    signer = bt / "lib" / "apksigner.jar"
    run("java", "-jar", signer, "sign", "--ks", keystore, "--ks-pass", "pass:dbyw09-local", "--ks-key-alias", "gmscompat",
        "--out", output / "gmscompat.apk", output / "aligned.apk")
    run("java", "-jar", signer, "verify", "--verbose", output / "gmscompat.apk")
    with zipfile.ZipFile(output / "gmscompat.apk") as apk:
        if len([n for n in apk.namelist() if n.endswith(".dex")]) != 1:
            raise RuntimeError("Unexpected dex layout")
    print("Built:", output / "gmscompat.apk")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", required=True)
    parser.add_argument("--out", required=True, help="New output directory; existing directories are rejected")
    parser.add_argument("--keystore", required=True, help="Private local APK signing key, not a device/Google key")
    args = parser.parse_args()
    build(args.sdk, args.out, args.keystore)
