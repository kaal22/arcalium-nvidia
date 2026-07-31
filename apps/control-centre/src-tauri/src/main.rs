// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// WebKitGTK and the proprietary NVIDIA driver disagree over buffer handling.
// On Wayland the process dies before a window appears; on X11 the window opens
// blank. Both have documented environment-variable workarounds, but they must be
// set before WebKit initialises, so they go here rather than in the Tauri setup
// hook. See https://v2.tauri.app/develop/debug/linux-graphics/
//
// The desktop entry also exports __NV_DISABLE_EXPLICIT_SYNC, which is confirmed
// working on the RTX 3060. That covers the launcher without depending on this
// setenv landing before the driver reads it; this function keeps every other
// launch path (terminal, scripts) working and handles the X11 case.
#[cfg(target_os = "linux")]
fn apply_webkit_nvidia_workaround() {
    if std::env::var_os("ARCALIUM_CC_NO_GPU_WORKAROUND").is_some() {
        return;
    }
    let nvidia_loaded = std::path::Path::new("/sys/module/nvidia").exists()
        || std::path::Path::new("/proc/driver/nvidia").exists();
    if !nvidia_loaded {
        return;
    }

    let wayland = std::env::var_os("WAYLAND_DISPLAY").is_some()
        || std::env::var("XDG_SESSION_TYPE").map(|v| v == "wayland").unwrap_or(false);

    let (key, value) = if wayland {
        ("__NV_DISABLE_EXPLICIT_SYNC", "1")
    } else {
        ("WEBKIT_DISABLE_DMABUF_RENDERER", "1")
    };

    if std::env::var_os(key).is_none() {
        std::env::set_var(key, value);
    }
}

fn main() {
    #[cfg(target_os = "linux")]
    apply_webkit_nvidia_workaround();

    arcalium_control_centre_lib::run()
}
