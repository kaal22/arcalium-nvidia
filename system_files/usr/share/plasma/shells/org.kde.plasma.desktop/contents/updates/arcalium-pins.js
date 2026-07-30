// Default Icon Tasks pins for new Arcalium users.
// Filename sorts before bazzite-pins.js, so this runs first on a fresh Plasma
// session; Bazzite's script then sees a non-empty launchers list and skips.
// Only writes when launchers is empty — PRODUCT_SPEC §11.2 forbids reapplying
// the desktop layout on every boot or overwriting user changes.
const allPanels = panels();

for (let i = 0; i < allPanels.length; ++i) {
    const panel = allPanels[i];
    const widgets = panel.widgets();

    for (let j = 0; j < widgets.length; ++j) {
        const widget = widgets[j];

        if (widget.type === "org.kde.plasma.icontasks") {
            widget.currentConfigGroup = ["General"];

            const currentLaunchers = widget.readConfig("launchers", "");

            if (!currentLaunchers || currentLaunchers.trim() === "") {
                widget.writeConfig("launchers", [
                    "applications:com.brave.Browser.desktop",
                    "applications:arcalium-chatgpt.desktop",
                    "applications:com.spotify.Client.desktop",
                    "applications:com.vysp3r.ProtonPlus.desktop",
                    "applications:steam.desktop",
                    "applications:io.github.kolunmi.Bazaar.desktop",
                    "preferred://filemanager"
                ]);
                widget.reloadConfig();
            }
        }
    }
}
