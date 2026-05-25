[app]

# (str) Title of your application
title = JUST - Smart Attendance

# (str) Package name
package.name = justapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.justapp

# (source.dir) Source code directory where the main.py live
source.dir = .

# (source.include_exts) Source include extensions (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (source.include_patterns) Source include patterns, e.g. images/* could mean you want to use the images
# directory, in this case, you must make:
# source.include_patterns = images/*

# (source.exclude_exts) Source exclude extensions, e.g. spec
source.exclude_exts = spec

# (source.exclude_patterns) Source exclude directory/file patterns, e.g. exclude=tests/*
source.exclude_patterns = tests, bin, build, .git, .gitignore, README.md

# (version) Application versioning (method 1)
version = 5.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pyrebase4,requests

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application (image or drawable xml)
# presplash.filename = %(source.dir)s/data/presplash.png

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android app theme, default is ok for Kivy-based app
# android.theme = "@android:style/Theme.NoTitleBar"

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) Pattern to whitelist for the whole project
#android.whitelist = lib-dynload/termios.so

# (str) Path to a Java file for the Android app class.
# If you have the file at java/src/org/test/myapp/MyApp.java
# android.java_classes = java/src/org/test/myapp/MyApp.java

# (list) files in the assets folder to be added to the APK explicitly.
# Let empty to let apk auto add those files:
# android.add_assets =

# (list) Gradle dependencies (for new android toolchain)
# Pass any gradle dependency using the strings package.gradle_dependencies = [domain:package:version]
# Here are the domain, the 'org.gstreamermedia' depends on gradle version and could be 'com.google.android' or 'org.gstreamer' for example.
# NB the scope have to be 'release' for kivy, of course 'com.android.support:appcompat-v7:28.0.0'
# android.gradle_dependencies = com.google.android.material:material:1.1.0

# (list) Java classes to add as services to perform background
# android.services = org.kivy.android.PythonService

# (bool) Presplash support
android.presplash = 1

# (int) Presplash duration in ms
android.presplash_duration = 2000

# (bool) Android logcat filtering will only show python logs by default
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Enable AndroidX support
android.enable_androidx = True

# (int) Android API to compile against
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin
