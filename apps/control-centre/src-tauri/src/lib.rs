mod ctl;

use ctl::{CtlError, run_arcaliumctl};
use serde_json::Value;
use tauri::Manager;

#[tauri::command]
fn arcaliumctl(args: Vec<String>) -> Result<Value, String> {
    run_arcaliumctl(&args).map_err(|e: CtlError| e.to_string())
}

#[tauri::command]
fn open_desktop(desktop_id: String) -> Result<(), String> {
    // UI chrome only — launch known desktop entries via xdg-open.
    // Not a system-mutation path; argv is fixed after validation.
    const ALLOWED: &[&str] = &[
        "steam.desktop",
        "io.github.kolunmi.Bazaar.desktop",
        "systemsettings.desktop",
        "com.heroicgameslauncher.hgl.desktop",
        "com.brave.Browser.desktop",
    ];
    if !ALLOWED.contains(&desktop_id.as_str()) {
        return Err(format!("desktop entry not allowlisted: {desktop_id}"));
    }
    let path = format!("/usr/share/applications/{desktop_id}");
    std::process::Command::new("xdg-open")
        .arg(&path)
        .spawn()
        .map_err(|e| format!("failed to open {desktop_id}: {e}"))?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![arcaliumctl, open_desktop])
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_title("Arcalium Control Centre");
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Arcalium Control Centre");
}
