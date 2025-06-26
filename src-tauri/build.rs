/*!
 * HunterMatrix AI Security Platform
 * Build script for Tauri application
 * 
 * This build script sets up the build environment for the HunterMatrix
 * AI security platform, including Tauri configuration and resource setup.
 * 
 * Created: 2025-06-25
 * Author: HunterMatrix Development Team
 */

use std::env;

fn main() {
    // Set up Tauri build
    tauri_build::build();
    
    // Add timestamp to build
    let timestamp = chrono::Utc::now().format("%Y-%m-%d %H:%M:%S UTC");
    println!("cargo:rustc-env=BUILD_TIMESTAMP={}", timestamp);
    
    // Add version info
    let version = env::var("CARGO_PKG_VERSION").unwrap_or_else(|_| "unknown".to_string());
    println!("cargo:rustc-env=APP_VERSION={}", version);
    
    // Add git commit hash if available
    if let Ok(output) = std::process::Command::new("git")
        .args(&["rev-parse", "--short", "HEAD"])
        .output()
    {
        if output.status.success() {
            let git_hash = String::from_utf8_lossy(&output.stdout).trim().to_string();
            println!("cargo:rustc-env=GIT_HASH={}", git_hash);
        }
    }
    
    // Rerun if any config files change
    println!("cargo:rerun-if-changed=tauri.conf.json");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=src/");
} 