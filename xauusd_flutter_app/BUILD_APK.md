# How to Build a Real APK (XAUUSD AI Trader)

## Prerequisites (on your computer)

1. Install **Flutter** (latest stable): https://docs.flutter.dev/get-started/install
2. Install **Android Studio** (includes Android SDK + Gradle)
3. Accept Android licenses: `flutter doctor --android-licenses`
4. Make sure `flutter doctor` shows no critical errors

## Steps to get a downloadable APK

```bash
# 1. Go into the project
cd xauusd_flutter_app

# 2. Get dependencies
flutter pub get

# 3. (Optional but recommended) Generate your own signing key
chmod +x scripts/generate_keystore.sh
./scripts/generate_keystore.sh

# 4. Create android/key.properties (after generating keystore)
# storePassword=your_store_password
# keyPassword=your_key_password
# keyAlias=xauusd
# storeFile=../xauusd-release-key.jks

# 5. Build the release APK
flutter build apk --release

# The APK will be here:
# build/app/outputs/flutter-apk/app-release.apk
```

You can then copy `app-release.apk` to your phone and install it (enable “Install from unknown sources”).

## Important configuration before building

Open `lib/services/auth_service.dart` and change:

```dart
static const String baseUrl = 'http://10.0.2.2:8000';
```

- **Android Emulator** → keep `10.0.2.2`
- **Real phone** → change to your computer’s LAN IP, e.g. `http://192.168.1.25:8000`
- **Production** → use your public domain / HTTPS URL

Also update the WebSocket URL in `lib/screens/home_screen.dart`.

## Debug vs Release

- Debug APK (faster, larger, not for distribution):
  ```bash
  flutter build apk --debug
  ```

- Release APK (optimized, signed):
  ```bash
  flutter build apk --release
  ```

## Disclaimer

This app is for **educational paper-trading research only**.  
It is **not** financial advice. Real trading of XAUUSD involves substantial risk of loss.
