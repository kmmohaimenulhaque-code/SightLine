#!/bin/sh
# Build the SIGHTLINE probe APK with the Android SDK build-tools only (no Gradle, no third-party libraries).
# Needs: JDK 17+, and an Android SDK with "platforms;android-34" and "build-tools;34.0.0".
#   ANDROID_SDK_ROOT=/path/to/sdk ./build_apk.sh
# Output: build/sightline-probe-debug.apk (signed with a throw-away debug key generated on first run).
set -eu
: "${ANDROID_SDK_ROOT:?set ANDROID_SDK_ROOT to your Android SDK}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BT="$ANDROID_SDK_ROOT/build-tools/34.0.0"
JAR="$ANDROID_SDK_ROOT/platforms/android-34/android.jar"
OUT="$HERE/build"
rm -rf "$OUT" && mkdir -p "$OUT/classes" "$OUT/dex"
"$BT/aapt2" link -o "$OUT/base.apk" --manifest "$HERE/AndroidManifest.xml" -I "$JAR" \
    --min-sdk-version 21 --target-sdk-version 34 --version-code 1 --version-name 0.1.0
javac -source 8 -target 8 -Xlint:-options -bootclasspath "$JAR" -d "$OUT/classes" \
    "$HERE"/src/org/sightline/probe/*.java
"$BT/d8" --min-api 21 --lib "$JAR" --output "$OUT/dex" $(find "$OUT/classes" -name '*.class')
cp "$OUT/base.apk" "$OUT/unsigned.apk"
(cd "$OUT/dex" && zip -q -j "$OUT/unsigned.apk" classes.dex)
"$BT/zipalign" -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
KS="$OUT/debug.keystore"
keytool -genkeypair -keystore "$KS" -storepass android -keypass android -alias debug -keyalg RSA -keysize 2048 \
    -validity 3650 -dname "CN=SIGHTLINE probe debug" >/dev/null 2>&1
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
    --out "$OUT/sightline-probe-debug.apk" "$OUT/aligned.apk"
"$BT/apksigner" verify "$OUT/sightline-probe-debug.apk"
echo "built $OUT/sightline-probe-debug.apk"
