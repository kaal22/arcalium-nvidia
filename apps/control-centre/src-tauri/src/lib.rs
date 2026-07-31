mod ctl;

use ctl::{CtlError, run_arcaliumctl};
use serde_json::Value;
use std::path::PathBuf;
use tauri::Manager;

#[tauri::command]
fn arcaliumctl(args: Vec<String>) -> Result<Value, String> {
    run_arcaliumctl(&args).map_err(|e: CtlError| e.to_string())
}

fn resolve_desktop_path(desktop_id: &str) -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    candidates.push(PathBuf::from(format!(
        "/usr/share/applications/{desktop_id}"
    )));
    candidates.push(PathBuf::from(format!(
        "/var/lib/flatpak/exports/share/applications/{desktop_id}"
    )));

    if let Ok(home) = std::env::var("HOME") {
        candidates.push(PathBuf::from(format!(
            "{home}/.local/share/applications/{desktop_id}"
        )));
        candidates.push(PathBuf::from(format!(
            "{home}/.local/share/flatpak/exports/share/applications/{desktop_id}"
        )));
    }

    candidates.into_iter().find(|p| p.is_file())
}

#[tauri::command]
fn open_desktop(desktop_id: String) -> Result<(), String> {
    // Launch the application described by the .desktop file.
    // Do NOT use xdg-open on the path — that opens the file in a text editor
    // (Kate on Plasma) instead of running Exec=.
    const ALLOWED: &[&str] = &[
        "steam.desktop",
        "io.github.kolunmi.Bazaar.desktop",
        "systemsettings.desktop",
        "org.kde.dolphin.desktop",
        "org.kde.plasma.systemmonitor.desktop",
        "org.kde.partitionmanager.desktop",
        "org.kde.kinfocenter.desktop",
        "bluedevil-wizard.desktop",
        "bluetooth.desktop",
        "kcm_bluetooth.desktop",
        "com.heroicgameslauncher.hgl.desktop",
        "com.brave.Browser.desktop",
        "com.vysp3r.ProtonPlus.desktop",
        "com.usebottles.bottles.desktop",
        "org.prismlauncher.PrismLauncher.desktop",
        "com.spotify.Client.desktop",
        "com.github.Matoking.protontricks.desktop",
        "com.github.tchx84.Flatseal.desktop",
        "com.discordapp.Discord.desktop",
        "com.obsproject.Studio.desktop",
        "dev.lizardbyte.app.Sunshine.desktop",
        "com.moonlight_stream.Moonlight.desktop",
        "com.protonvpn.www.desktop",
        "nvidia-settings.desktop",
        "org.nvidia.Settings.desktop",
    ];
    if !ALLOWED.contains(&desktop_id.as_str()) {
        return Err(format!("desktop entry not allowlisted: {desktop_id}"));
    }
    let path = resolve_desktop_path(&desktop_id).ok_or_else(|| {
        format!("desktop entry not found for {desktop_id} (is the Flatpak installed?)")
    })?;

    // Prefer gio launch (GLib) — treats .desktop as an app, not a document.
    if try_spawn("gio", &["launch", path.to_str().unwrap_or_default()]) {
        return Ok(());
    }
    // gtk-launch takes the desktop file id (with or without .desktop).
    if try_spawn("gtk-launch", &[desktop_id.as_str()]) {
        return Ok(());
    }
    // Plasma fallback.
    if try_spawn("kioclient", &["exec", path.to_str().unwrap_or_default()])
        || try_spawn("kioclient5", &["exec", path.to_str().unwrap_or_default()])
        || try_spawn("kioclient6", &["exec", path.to_str().unwrap_or_default()])
    {
        return Ok(());
    }

    Err(format!(
        "could not launch {desktop_id}: gio launch, gtk-launch, and kioclient all unavailable"
    ))
}

fn try_spawn(bin: &str, args: &[&str]) -> bool {
    match std::process::Command::new(bin).args(args).spawn() {
        Ok(_) => true,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => false,
        Err(_) => false,
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![arcaliumctl, open_desktop])
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_title("Arcalium Control Centre");
                // We build with --no-bundle, so bundle.icon is never applied and
                // the window falls back to the toolkit's default mark. Icons are
                // generated from assets/arccleanSVG.svg by build.sh before cargo
                // runs, so this include is resolvable at compile time.
                //
                // This sets _NET_WM_ICON, which covers X11. On Wayland the
                // compositor takes the icon from the .desktop file it matches by
                // app_id, which is why the desktop entry also sets
                // StartupWMClass=arcalium-control-centre.
                if let Ok(icon) = tauri::image::Image::from_bytes(include_bytes!(
                    "../icons/256x256.png"
                )) {
                    let _ = window.set_icon(icon);
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Arcalium Control Centre");
}
