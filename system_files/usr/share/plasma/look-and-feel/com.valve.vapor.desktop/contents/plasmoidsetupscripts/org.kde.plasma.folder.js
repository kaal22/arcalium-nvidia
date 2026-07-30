// Applied by Plasma when the Bazzite Vapor look-and-feel creates a new desktop
// containment. Existing users already have a containment and keep their wallpaper.
applet.wallpaperPlugin = "org.kde.image";
applet.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
applet.writeConfig("Image", "/usr/share/wallpapers/arcalium-wallpaper.png");
applet.reloadConfig();
