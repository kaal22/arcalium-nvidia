//! Allowlisted exec of `/usr/bin/arcaliumctl` — no shell, fixed argv only.

use serde_json::Value;
use std::io::Read;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};
use thiserror::Error;

const ARCALIUMCTL: &str = "/usr/bin/arcaliumctl";
const TIMEOUT_DEFAULT_SECS: u64 = 60;
const TIMEOUT_PROTON_INSTALL_SECS: u64 = 1800;
const TIMEOUT_FLATPAK_SECS: u64 = 1800;
const TIMEOUT_DIAGNOSTICS_SECS: u64 = 120;
const TIMEOUT_AI_INSTALL_SECS: u64 = 1800;
const TIMEOUT_AI_ENSURE_SECS: u64 = 3600;

/// Flatpak source IDs permitted for apps install/uninstall (must match catalogue).
const ALLOWED_FLATPAK_IDS: &[&str] = &[
    "com.heroicgameslauncher.hgl",
    "com.usebottles.bottles",
    "org.prismlauncher.PrismLauncher",
    "com.brave.Browser",
    "com.spotify.Client",
    "com.vysp3r.ProtonPlus",
    "com.github.Matoking.protontricks",
    "com.github.tchx84.Flatseal",
    "com.discordapp.Discord",
    "com.obsproject.Studio",
    "dev.lizardbyte.app.Sunshine",
    "com.moonlight_stream.Moonlight",
    "com.protonvpn.www",
];

/// Catalogue ids also accepted as apps install/uninstall targets.
const ALLOWED_CATALOGUE_IDS: &[&str] = &[
    "heroic",
    "bottles",
    "prism",
    "brave",
    "spotify",
    "protonplus",
    "protontricks",
    "flatseal",
    "discord",
    "obs",
    "sunshine",
    "moonlight",
    "protonvpn",
];

const ALLOWED_EXACT: &[&[&str]] = &[
    &["system", "summary", "--json"],
    &["gpu", "status", "--json"],
    &["gpu", "validate", "--json"],
    &["vulkan", "test", "--json"],
    &["proton", "list", "--json"],
    &["proton", "install-recommended", "--json"],
    &["apps", "catalogue", "--json"],
    &["apps", "list", "--json"],
    &["storage", "scan", "--json"],
    &["network", "status", "--json"],
    &["controllers", "list", "--json"],
    &["updates", "status", "--json"],
    &["updates", "check", "--json"],
    &["updates", "apply", "--json"],
    &["updates", "rollback", "--json"],
    &["updates", "reboot", "--json"],
    &["diagnostics", "run", "--json"],
    &["diagnostics", "bundle", "--json"],
    &["ai", "status", "--json"],
    &["ai", "install-ollama", "--json"],
    &["ai", "install-ollama", "--visible", "--json"],
    &["ai", "ensure", "--json"],
    &["ai", "ensure", "--visible", "--json"],
    &["ai", "launch", "--json"],
    &["ai", "stop", "--json"],
    &["setup", "status", "--json"],
    &["setup", "complete", "--json"],
    &["setup", "reset", "--json"],
];

const SETUP_STEPS: &[&str] = &[
    "welcome",
    "hardware",
    "nvidia",
    "display",
    "updates",
    "applications",
    "protonGe",
    "steam",
    "storage",
    "vpn",
    "streaming",
    "validation",
    "localAi",
    "completion",
];

const SETUP_STATES: &[&str] = &["complete", "skipped", "pending", "in_progress"];

#[derive(Debug, Error)]
pub enum CtlError {
    #[error("command not allowlisted: {0:?}")]
    NotAllowlisted(Vec<String>),
    #[error("arcaliumctl missing at {ARCALIUMCTL}")]
    MissingBinary,
    #[error("failed to spawn arcaliumctl: {0}")]
    Spawn(String),
    #[error("arcaliumctl timed out after {0}s")]
    Timeout(u64),
    #[error("arcaliumctl exited {code}: {stderr}")]
    Exit { code: i32, stderr: String },
    #[error("invalid JSON from arcaliumctl: {0}")]
    Json(String),
}

fn is_allowed(args: &[String]) -> bool {
    if ALLOWED_EXACT.iter().any(|seq| {
        seq.len() == args.len() && seq.iter().zip(args.iter()).all(|(a, b)| *a == b.as_str())
    }) {
        return true;
    }
    // apps install|uninstall <id> --json
    if args.len() == 4
        && args[0] == "apps"
        && (args[1] == "install" || args[1] == "uninstall")
        && args[3] == "--json"
    {
        let id = args[2].as_str();
        return ALLOWED_FLATPAK_IDS.contains(&id) || ALLOWED_CATALOGUE_IDS.contains(&id);
    }
    // apps install <id> --visible --json
    if args.len() == 5
        && args[0] == "apps"
        && args[1] == "install"
        && args[3] == "--visible"
        && args[4] == "--json"
    {
        let id = args[2].as_str();
        return ALLOWED_FLATPAK_IDS.contains(&id) || ALLOWED_CATALOGUE_IDS.contains(&id);
    }
    // setup save <step> --json
    if args.len() == 4 && args[0] == "setup" && args[1] == "save" && args[3] == "--json" {
        return SETUP_STEPS.contains(&args[2].as_str());
    }
    // setup mark <step> <state> --json
    if args.len() == 5 && args[0] == "setup" && args[1] == "mark" && args[4] == "--json" {
        return SETUP_STEPS.contains(&args[2].as_str()) && SETUP_STATES.contains(&args[3].as_str());
    }
    // setup set-autostart on|off|true|false|1|0 --json
    if args.len() == 4 && args[0] == "setup" && args[1] == "set-autostart" && args[3] == "--json" {
        return matches!(args[2].as_str(), "on" | "off" | "true" | "false" | "1" | "0");
    }
    false
}

fn timeout_for(args: &[String]) -> u64 {
    if args.len() >= 2 && args[0] == "proton" && args[1] == "install-recommended" {
        return TIMEOUT_PROTON_INSTALL_SECS;
    }
    if args.len() >= 2 && args[0] == "apps" && (args[1] == "install" || args[1] == "uninstall") {
        // Visible mode only spawns a terminal and returns immediately.
        return if args.iter().any(|a| a == "--visible") {
            TIMEOUT_DEFAULT_SECS
        } else {
            TIMEOUT_FLATPAK_SECS
        };
    }
    if args.len() >= 2 && args[0] == "diagnostics" {
        return TIMEOUT_DIAGNOSTICS_SECS;
    }
    if args.len() >= 2 && args[0] == "ai" {
        let visible = args.iter().any(|a| a == "--visible");
        if args[1] == "install-ollama" {
            // Visible mode only spawns a terminal and returns immediately.
            return if visible {
                TIMEOUT_DEFAULT_SECS
            } else {
                TIMEOUT_AI_INSTALL_SECS
            };
        }
        if args[1] == "ensure" {
            return if visible {
                TIMEOUT_DEFAULT_SECS
            } else {
                TIMEOUT_AI_ENSURE_SECS
            };
        }
    }
    TIMEOUT_DEFAULT_SECS
}

/// Failing commands still print their `arcalium.error/v1` payload on stdout, so
/// reporting stderr alone left the UI with a bare "exited 1" and no reason.
fn failure_detail(stdout: &[u8], stderr: &[u8]) -> String {
    if let Ok(value) = serde_json::from_slice::<Value>(stdout) {
        let code = value.get("code").and_then(Value::as_str);
        let detail = value
            .get("detail")
            .and_then(Value::as_str)
            .filter(|s| !s.trim().is_empty())
            .or_else(|| value.get("message").and_then(Value::as_str));
        match (code, detail) {
            (Some(code), Some(detail)) => return format!("{code}: {detail}"),
            (None, Some(detail)) => return detail.to_string(),
            (Some(code), None) => return code.to_string(),
            (None, None) => {}
        }
    }
    let stderr = String::from_utf8_lossy(stderr).trim().to_string();
    if !stderr.is_empty() {
        return stderr;
    }
    String::from_utf8_lossy(stdout).trim().to_string()
}

pub fn run_arcaliumctl(args: &[String]) -> Result<Value, CtlError> {
    if !is_allowed(args) {
        return Err(CtlError::NotAllowlisted(args.to_vec()));
    }
    if !std::path::Path::new(ARCALIUMCTL).is_file() {
        return Err(CtlError::MissingBinary);
    }

    let timeout_secs = timeout_for(args);

    let mut child = Command::new(ARCALIUMCTL)
        .args(args)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| CtlError::Spawn(e.to_string()))?;

    let deadline = Instant::now() + Duration::from_secs(timeout_secs);
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                let mut stdout = Vec::new();
                let mut stderr = Vec::new();
                if let Some(mut out) = child.stdout.take() {
                    let _ = out.read_to_end(&mut stdout);
                }
                if let Some(mut err) = child.stderr.take() {
                    let _ = err.read_to_end(&mut stderr);
                }
                if !status.success() {
                    return Err(CtlError::Exit {
                        code: status.code().unwrap_or(-1),
                        stderr: failure_detail(&stdout, &stderr),
                    });
                }
                return serde_json::from_slice(&stdout).map_err(|e| CtlError::Json(e.to_string()));
            }
            Ok(None) => {
                if Instant::now() > deadline {
                    let _ = child.kill();
                    let _ = child.wait();
                    return Err(CtlError::Timeout(timeout_secs));
                }
                std::thread::sleep(Duration::from_millis(50));
            }
            Err(e) => return Err(CtlError::Spawn(e.to_string())),
        }
    }
}
