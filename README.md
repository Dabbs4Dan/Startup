# Daily Bread 📖
Christian devotional planner — Expo / React Native app.

**Open on iPhone (Expo Go):**
https://snack.expo.dev/?name=Daily%20Bread&sourceUrl=https%3A%2F%2Fraw.githubusercontent.com%2FDabbs4Dan%2FStartup%2Fdaily-bread%2FApp.js&dependencies=%40react-native-async-storage%2Fasync-storage%2Creact-native-safe-area-context&platform=mydevice

## Claude's test loop (no phone needed)
```bash
npm install
EXPO_OFFLINE=1 npx expo export --platform ios --output-dir dist-ios   # proves the iPhone bundle compiles
EXPO_OFFLINE=1 npx expo export --platform web --output-dir dist-web
python3 test/phone-test.py dist-web test/shots                        # taps through the app at iPhone size
```
Screenshots land in `test/shots/`.
