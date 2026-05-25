# 📱 JUST App v5.0 — APK Build Guide

Complete step-by-step guide to build and deploy the JUST Smart Attendance app as an Android APK.

---

## ✅ Prerequisites (Install These First)

### 1. **Python 3.10 or Higher**
- Download: https://www.python.org/downloads/
- Add Python to PATH during installation
- Verify: `python --version`

### 2. **Java Development Kit (JDK 11+)**
- Download: https://www.oracle.com/java/technologies/downloads/
- Set JAVA_HOME environment variable
- Verify: `java -version`

### 3. **Android SDK & NDK**
- Install Android Studio: https://developer.android.com/studio
- Open Android Studio → SDK Manager (bottom right icon)
- Install:
  - Android SDK Platform 33
  - Android NDK 25b (required!)
  - Android Build Tools 33.0.0+

### 4. **Git (Optional but Recommended)**
- Download: https://git-scm.com/downloads
- Verify: `git --version`

---

## 🚀 Step 1: Install Buildozer

Open Terminal/Command Prompt and run:

```bash
pip install --upgrade pip
pip install buildozer cython
```

Verify installation:
```bash
buildozer --version
```

---

## 📂 Step 2: Prepare Project Structure

Your project folder should look like this:

```
JUST-App/
├── main.py              ✓ (already in repo)
├── buildozer.spec       ✓ (already in repo)
├── requirements.txt     ✓ (already in repo)
├── .buildozer/          (auto-created)
└── bin/                 (auto-created - APK output)
```

Clone or navigate to the repo:
```bash
git clone https://github.com/anbuarasan7450-maker/JUST-App.git
cd JUST-App
```

---

## ⚙️ Step 3: Configure buildozer.spec (if needed)

The `buildozer.spec` file is already configured, but you can customize:

```bash
# Edit buildozer.spec with your text editor
# Key settings to check:

[app]
title = JUST - Smart Attendance
package.name = justapp
package.domain = org.justapp
version = 5.0.0

[buildozer]
android.api = 33              # Target API
android.minapi = 21           # Minimum API  
android.ndk = 25b             # NDK version
```

If you have Android SDK/NDK installed in non-standard location, set:
```ini
android.sdk_path = /path/to/android/sdk
android.ndk_path = /path/to/android/ndk
```

---

## 🔨 Step 4: Build the APK

### **Option A: Debug Build (Fastest - 15-20 minutes)**

```bash
buildozer android debug
```

Output location:
```
bin/justapp-5.0.0-debug.apk
```

### **Option B: Release Build (Slower - 25-40 minutes, optimized)**

```bash
buildozer android release
```

Output location:
```
bin/justapp-5.0.0-release.apk
```

---

## 📱 Step 5: Install on Device

### **Prerequisites:**
- Android phone with USB debugging enabled
- USB cable connected to computer

### **Enable USB Debugging on Phone:**
1. Go to **Settings → About Phone**
2. Tap **Build Number** 7 times
3. Back to Settings → **Developer Options** → Enable **USB Debugging**

### **Install Command:**

```bash
# This builds, installs, AND runs the app in one command
buildozer android debug install run
```

Or install a pre-built APK:
```bash
adb install bin/justapp-5.0.0-debug.apk
```

---

## 🧪 Testing the App

**Demo Credentials:**
```
Role: Faculty/Teacher
Email: teacher@just.edu
PIN: 1234
```

**Parent Portal:**
```
Student ID: (add a student first from teacher portal)
```

---

## ⚠️ Common Build Issues & Fixes

### Issue 1: `ndk not found`
**Error:** `Exception: NDK not found`

**Fix:**
```bash
# Option A: Let Buildozer download NDK automatically
buildozer android debug -- --ndk=25b

# Option B: Manual path in buildozer.spec
# Edit and add:
android.ndk_path = /path/to/ndk/25b
```

---

### Issue 2: `java not found`
**Error:** `java.exe not found`

**Fix:**
```bash
# Install JDK 11+
# Add JAVA_HOME to environment variables

# Windows:
setx JAVA_HOME "C:\Program Files\Java\jdk-11.0.x"

# macOS/Linux:
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-11.0.x.jdk/Contents/Home
```

---

### Issue 3: `Permission denied`
**Error:** `Permission denied: 'buildozer'`

**Fix:**
```bash
# Use Python module directly
python -m buildozer android debug

# Or run with elevated permissions
sudo buildozer android debug  # (not recommended)
```

---

### Issue 4: `pyrebase4 compilation error`
**Error:** `ModuleNotFoundError: No module named 'pyrebase4'`

**Fix:**
```bash
pip install pyrebase4 --no-binary :all:
buildozer android debug -- --requirements=python3,kivy,pyrebase4,requests
```

---

### Issue 5: `Low disk space`
**Error:** `No space left on device`

**Fix:** Buildozer needs 5-10GB free space. Clear:
```bash
# Clean build cache
buildozer android clean

# Or remove old builds
rm -rf .buildozer/ bin/
```

---

### Issue 6: `Gradle build failed`
**Error:** `Gradle build failed`

**Fix:**
```bash
# Update Gradle cache
buildozer android clean

# Rebuild with verbose output
buildozer android debug -- --verbose
```

---

## 📦 Distributing Your APK

### **Option 1: Direct APK Distribution**
```bash
# Share the APK file directly (file is ~100-150MB)
bin/justapp-5.0.0-release.apk
```

### **Option 2: Google Play Store**
1. Create Google Play Developer account ($25 one-time)
2. Create signing key (do NOT share this!)
   ```bash
   buildozer android release
   # Follow prompts for key generation
   ```
3. Upload APK to Play Store Console
4. Fill app details, screenshots, description
5. Wait for Google Play review (24-48 hours)

### **Option 3: GitHub Releases**
Upload APK to your repo's Releases tab:
```bash
# GitHub → Releases → Draft New Release → Upload binary
```

---

## 🔐 Security Notes

⚠️ **IMPORTANT FOR PRODUCTION:**

1. **Move Firebase credentials to `.env` file:**
   ```bash
   # Create .env file (DO NOT COMMIT TO GIT)
   FIREBASE_API_KEY=your_key_here
   FIREBASE_DB_URL=your_url_here
   ```

2. **Generate signing key for release APK:**
   ```bash
   buildozer android release
   # Keep the keystore file (.jks) SECURE
   # DO NOT SHARE or COMMIT to Git
   ```

3. **Obfuscate code (ProGuard/R8):**
   Add to buildozer.spec:
   ```ini
   android.gradle_dependencies = com.android.tools:desugar_jdk_libs:1.1.5
   android.enable_proguard = 1
   ```

---

## 📊 Build Performance Tips

| Task | Time | Tip |
|------|------|-----|
| First build | 20-30 min | Download & compile dependencies |
| Incremental build | 5-10 min | Only changed files |
| Clean rebuild | 20-30 min | `buildozer android clean` then build |

**Speed up builds:**
```bash
# Skip dependency re-download
buildozer android debug -- --no-update

# Use pre-compiled wheels (if available)
buildozer android debug -- --use-prebuilt-dist
```

---

## 🐛 Debugging

### View App Logs
```bash
# Real-time logs from device
adb logcat | grep python

# Filter just errors
adb logcat | grep -i error
```

### Connect to Device
```bash
# Check if device is connected
adb devices

# Restart ADB server if needed
adb kill-server
adb start-server
```

---

## 📚 Useful Resources

- **Kivy Docs:** https://kivy.org/doc/stable/
- **Buildozer Docs:** https://buildozer.readthedocs.io/
- **Android Developer:** https://developer.android.com/
- **Firebase Docs:** https://firebase.google.com/docs

---

## ✨ Next Steps

After building:

1. ✅ Test on real Android device
2. ✅ Gather user feedback
3. ✅ Fix bugs (update main.py)
4. ✅ Rebuild and test again
5. ✅ Prepare for Play Store submission

---

## 🆘 Need Help?

If build fails:
1. Check error message carefully
2. Search GitHub Issues: https://github.com/anbuarasan7450-maker/JUST-App/issues
3. Post detailed error log (include full buildozer output)

---

**Happy Building! 🎉**

---

*Last Updated: 2026-05-25*  
*JUST App v5.0 - Smart Campus Attendance System*
