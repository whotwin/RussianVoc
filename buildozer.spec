[app]

title = Russian Flashcards
package.name = russianflashcards
package.domain = org.russianflashcards

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,mp3,wav,ttf
source.include_patterns = assets/*,images/*.png

version = 0.1.0

requirements = python3,kivy==2.3.0,kivymd==2.0.0,pymorphy2,pymorphy2-dicts-ru,plyer,schedule,aiosqlite,sqlalchemy,httpx,audio,pyjnius,android

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,RECEIVE_BOOT_COMPLETED,POST_NOTIFICATIONS,SCHEDULE_EXACT_ALARM,USE_EXACT_ALARM,VIBRATE
android.archs = arm64-v8a,armeabi-v7a

android.meta_data = com.google.android.gms.version=@integer/google_play_services_version

# iOS settings (Mac required)
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
