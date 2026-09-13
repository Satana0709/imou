[app]

title = Imou Recorder
package.name = imourecorder
package.domain = org.imou
source.include_exts = py,png,jpg,kv,atlas
source.dir = .
version = 0.1
requirements = python3,kivy,opencv,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE
android.api = 31
android.min_api = 21
android.sdk = 31
android.ndk = 23b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
