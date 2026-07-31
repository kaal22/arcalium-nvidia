//! Allowlisted exec of `/usr/bin/arcaliumctl` — no shell, fixed argv only.

use serde_json::Value;
use std::io::Read;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};
use thiserror::Error;

const ARCALIUMCTL: &str = "/usr/bin/arcaliumctl";
const TIMEOUT_DEFAULT_SECS: u64 = 60;
/// GE-Proton downloads are large; matches arcaliumctl's DOWNLOAD_TIMEOUT.
const TIMEOUT_PROTON_INSTALL_SECS: u64 = 1800;

/// Exact argv sequences the UI may request (without the binary name).
const ALLOWED: &[&[&str]] = &[
    &["system", "summary", "--json"],
    &["gpu", "status", "--json"],
    &["gpu", "validate", "--json"],
    &["vulkan", "test", "--json"],
    &["proton", "list", "--json"],
    &["proton", "install-recommended", "--json"],
];

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

fn timeout_for(args: &[String]) -> u64 {
    if args.len() >= 2 && args[0] == "proton" && args[1] == "install-recommended" {
        TIMEOUT_PROTON_INSTALL_SECS
    } else {
        TIMEOUT_DEFAULT_SECS
    }
}

pub fn run_arcaliumctl(args: &[String]) -> Result<Value, CtlError> {
    let allowed = ALLOWED.iter().any(|seq| {
        seq.len() == args.len() && seq.iter().zip(args.iter()).all(|(a, b)| *a == b.as_str())
    });
    if !allowed {
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
                        stderr: String::from_utf8_lossy(&stderr).trim().to_string(),
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
