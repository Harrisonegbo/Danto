#!/bin/bash
# Generate a release keystore for signing the APK
# Run this ONCE on your own machine

echo "Generating release keystore for XAUUSD AI Trader..."
echo "You will be asked for passwords and certificate details."
echo ""

keytool -genkey -v \
  -keystore xauusd-release-key.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias xauusd \
  -storetype JKS

echo ""
echo "Keystore created: xauusd-release-key.jks"
echo "Keep this file and the passwords SAFE. You need them for every future update."
echo ""
echo "Next steps:"
echo "1. Create android/key.properties with:"
echo "   storePassword=YOUR_STORE_PASSWORD"
echo "   keyPassword=YOUR_KEY_PASSWORD"
echo "   keyAlias=xauusd"
echo "   storeFile=../xauusd-release-key.jks"
echo ""
echo "2. Then build with: flutter build apk --release"
