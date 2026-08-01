mod ctl;

use ctl::{CtlError, run_arcaliumctl};
use serde_json::Value;
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::Manager;

struct LaunchMode(Mutex<String>);

fn detect_launch_mode() -> String {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.iter().any(|a| a == "--setup" || a == "setup") {
        return "setup".into();
    }
    if std::env::var_os("ARCALIUM_SETUP").is_some() {
        return "setup".into();
    }
    "control-centre".into()
}

#[tauri::command]
fn arcaliumctl(args: Vec<String>) -> Result<Value, String> {
    run_arcaliumctl(&args).map_err(|e: CtlError| e.to_string())
}

#[tauri::command]
fn launch_mode(state: tauri::State<'_, LaunchMode>) -> String {
    state.0.lock().map(|g| g.clone()).unwrap_or_else(|_| "control-centre".into())
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
        "io.arcalium.ControlCentre.desktop",
        "io.arcalium.Setup.desktop",
    ];
    if !ALLOWED.contains(&desktop_id.as_str()) {
        return Err(format!("desktop entry not allowlisted: {desktop_id}"));
    }
    let path = resolve_desktop_path(&desktop_id).ok_or_else(|| {
        format!("desktop entry not found for {desktop_id} (is the Flatpak installed?)")
    })?;

    if try_spawn("gio", &["launch", path.to_str().unwrap_or_default()]) {
        return Ok(());
    }
    if try_spawn("gtk-launch", &[desktop_id.as_str()]) {
        return Ok(());
    }
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
    let mode = detect_launch_mode();
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(LaunchMode(Mutex::new(mode.clone())))
        .invoke_handler(tauri::generate_handler![arcaliumctl, open_desktop, launch_mode])
        .setup(move |app| {
            if let Some(window) = app.get_webview_window("main") {
                let title = if mode == "setup" {
                    "Arcalium Setup"
                } else {
                    "Arcalium Control Centre"
                };
                let _ = window.set_title(title);
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
