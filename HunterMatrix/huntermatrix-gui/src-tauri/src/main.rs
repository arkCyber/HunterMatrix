// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};
use std::io::{BufRead, BufReader};
use std::sync::{Arc, Mutex};
use std::thread;
use tauri::{Manager, Window};
use std::fs;
use std::path::Path;

// 定义数据结构
#[derive(Debug, Serialize, Deserialize)]
pub struct ScanResult {
    status: String,
    files_scanned: u32,
    threats_found: u32,
    scan_time: String,
    log_path: Option<String>,
    details: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DatabaseStatus {
    version: String,
    last_update: String,
    signatures: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ScanProgress {
    current_file: String,
    files_scanned: u32,
    total_files: u32,
    progress_percent: f32,
    threats_found: u32,
    scan_speed: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfo {
    cpu_usage: f32,
    memory_usage: f32,
    disk_usage: f32,
    platform: String,
}

// 获取系统信息
#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String> {
    let cpu_usage = get_cpu_usage();
    let memory_usage = get_memory_usage();
    let disk_usage = get_disk_usage();
    let platform = std::env::consts::OS.to_string();

    Ok(SystemInfo {
        cpu_usage,
        memory_usage,
        disk_usage,
        platform,
    })
}

// 获取CPU使用率 (简化实现)
fn get_cpu_usage() -> f32 {
    // 在实际应用中，这里应该使用系统API获取真实的CPU使用率
    // 这里使用模拟数据
    use std::time::{SystemTime, UNIX_EPOCH};
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    ((timestamp % 100) as f32) * 0.8 // 模拟0-80%的CPU使用率
}

// 获取内存使用率
fn get_memory_usage() -> f32 {
    // 尝试从系统获取内存信息
    if let Ok(output) = Command::new("vm_stat").output() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        // 简化解析，实际应用中需要更复杂的解析逻辑
        65.0 // 返回模拟值
    } else {
        50.0 // 默认值
    }
}

// 获取磁盘使用率
fn get_disk_usage() -> f32 {
    // 获取根目录磁盘使用情况
    if let Ok(output) = Command::new("df").arg("-h").arg("/").output() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        // 简化解析
        for line in output_str.lines().skip(1) {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 5 {
                let usage_str = parts[4].trim_end_matches('%');
                if let Ok(usage) = usage_str.parse::<f32>() {
                    return usage;
                }
            }
        }
    }
    45.0 // 默认值
}

// 获取数据库状态
#[tauri::command]
async fn get_database_status() -> Result<DatabaseStatus, String> {
    // 执行 clamscan --version 获取版本信息
    let output = Command::new("clamscan")
        .arg("--version")
        .output()
        .map_err(|e| format!("执行 clamscan 失败: {}", e))?;
    
    let version_info = String::from_utf8(output.stdout)
        .map_err(|e| format!("解析版本信息失败: {}", e))?;
    
    // 简单解析版本信息
    let version = version_info
        .lines()
        .find(|line| line.contains("ClamAV"))
        .unwrap_or("未知版本")
        .to_string();
    
    // 创建响应
    Ok(DatabaseStatus {
        version: version.trim().to_string(),
        last_update: "今天".to_string(), // 简化实现
        signatures: 8723276, // 从之前的下载信息得到的数字
    })
}

// 更新病毒库
#[tauri::command]
async fn update_virus_database() -> Result<String, String> {
    // 获取应用配置目录
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";
    let config_path = format!("{}/freshclam.conf", virus_db_path);
    
    // 执行更新命令
    let output = Command::new("freshclam")
        .arg("--config-file")
        .arg(&config_path)
        .output()
        .map_err(|e| format!("更新病毒库失败: {}", e))?;
    
    if output.status.success() {
        Ok("病毒库更新成功".to_string())
    } else {
        let error = String::from_utf8(output.stderr).unwrap_or_default();
        Err(format!("更新失败: {}", error))
    }
}

// 选择文件夹
#[tauri::command]
async fn select_folder() -> Result<String, String> {
    // 简化实现：直接返回用户主目录的子文件夹选项
    // 在实际应用中，这里应该使用系统文件对话框
    let default_paths = vec![
        "/Users/arkSong/Downloads",
        "/Users/arkSong/Documents", 
        "/Applications",
        "/Users/arkSong/Desktop"
    ];
    
    // 返回第一个存在的路径
    for path in default_paths {
        if std::path::Path::new(path).exists() {
            return Ok(path.to_string());
        }
    }
    
    Ok("/Users/arkSong".to_string())
}

// 计算目录中的文件数量
fn count_files_in_directory(path: &str) -> u32 {
    let mut count = 0;
    if let Ok(entries) = fs::read_dir(path) {
        for entry in entries.flatten() {
            if entry.file_type().map(|ft| ft.is_file()).unwrap_or(false) {
                count += 1;
            } else if entry.file_type().map(|ft| ft.is_dir()).unwrap_or(false) {
                count += count_files_in_directory(&entry.path().to_string_lossy());
            }
        }
    }
    count
}

// 实时扫描功能
#[tauri::command]
async fn start_realtime_scan(window: Window, path: String) -> Result<ScanResult, String> {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();

    let log_path = format!("/tmp/clamav_scan_{}.log", timestamp);
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";

    // 计算总文件数
    let total_files = count_files_in_directory(&path);

    let start_time = std::time::Instant::now();

    // 使用clamscan的详细输出模式
    let mut child = Command::new("clamscan")
        .arg("-r") // 递归扫描
        .arg("-v") // 详细输出
        .arg("--database")
        .arg(virus_db_path)
        .arg("--log")
        .arg(&log_path)
        .arg(&path)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("启动扫描失败: {}", e))?;

    let stdout = child.stdout.take().unwrap();
    let reader = BufReader::new(stdout);

    let mut files_scanned = 0u32;
    let mut threats_found = 0u32;
    let mut current_file = String::new();

    // 实时读取扫描输出
    for line in reader.lines() {
        if let Ok(line) = line {
            // 更新当前扫描的文件
            if line.contains(": OK") || line.contains(": FOUND") {
                if let Some(file_path) = line.split(':').next() {
                    current_file = file_path.trim().to_string();
                    files_scanned += 1;

                    if line.contains("FOUND") {
                        threats_found += 1;
                    }

                    // 计算进度
                    let progress_percent = if total_files > 0 {
                        (files_scanned as f32 / total_files as f32) * 100.0
                    } else {
                        0.0
                    };

                    // 计算扫描速度
                    let elapsed = start_time.elapsed().as_secs();
                    let scan_speed = if elapsed > 0 {
                        format!("{} 文件/秒", files_scanned / elapsed as u32)
                    } else {
                        "计算中...".to_string()
                    };

                    // 发送进度更新事件
                    let progress = ScanProgress {
                        current_file: current_file.clone(),
                        files_scanned,
                        total_files,
                        progress_percent,
                        threats_found,
                        scan_speed,
                    };

                    // 发送事件到前端
                    let _ = window.emit("scan-progress", &progress);
                }
            }
        }
    }

    // 等待进程完成
    let output = child.wait_with_output()
        .map_err(|e| format!("等待扫描完成失败: {}", e))?;

    let scan_duration = start_time.elapsed();
    let scan_time = format!("{}s", scan_duration.as_secs());

    let status = if threats_found > 0 {
        "infected"
    } else if output.status.success() {
        "safe"
    } else {
        "error"
    };

    let mut details = Vec::new();

    // 从日志文件读取详细信息
    if let Ok(log_content) = std::fs::read_to_string(&log_path) {
        for line in log_content.lines() {
            if line.contains("FOUND") {
                details.push(line.to_string());
            }
        }
    }

    Ok(ScanResult {
        status: status.to_string(),
        files_scanned,
        threats_found,
        scan_time,
        log_path: Some(log_path),
        details: if details.is_empty() { None } else { Some(details) },
    })
}

// 开始扫描 (保留原有功能)
#[tauri::command]
async fn start_scan(path: String) -> Result<ScanResult, String> {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    
    let log_path = format!("/tmp/clamav_scan_{}.log", timestamp);
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";
    
    // 执行 ClamAV 扫描
    let start_time = std::time::Instant::now();
    
    let output = Command::new("clamscan")
        .arg("-r") // 递归扫描
        .arg("-i") // 只显示感染文件
        .arg("--database")
        .arg(virus_db_path)
        .arg("--log")
        .arg(&log_path)
        .arg(&path)
        .output()
        .map_err(|e| format!("扫描失败: {}", e))?;
    
    let scan_duration = start_time.elapsed();
    let scan_time = format!("{}s", scan_duration.as_secs());
    
    // 解析扫描结果
    let scan_output = String::from_utf8(output.stdout).unwrap_or_default();
    let scan_error = String::from_utf8(output.stderr).unwrap_or_default();
    
    // 简单解析扫描结果
    let files_scanned = scan_output
        .lines()
        .filter(|line| line.contains("scanned"))
        .count() as u32;
    
    let threats_found = scan_output
        .lines()
        .filter(|line| line.contains("FOUND"))
        .count() as u32;
    
    let status = if threats_found > 0 {
        "infected"
    } else if output.status.success() {
        "safe"
    } else {
        "error"
    };
    
    let mut details = Vec::new();
    if !scan_error.is_empty() {
        details.push(scan_error);
    }
    
    // 从日志文件读取详细信息
    if let Ok(log_content) = std::fs::read_to_string(&log_path) {
        for line in log_content.lines() {
            if line.contains("FOUND") {
                details.push(line.to_string());
            }
        }
    }
    
    Ok(ScanResult {
        status: status.to_string(),
        files_scanned,
        threats_found,
        scan_time,
        log_path: Some(log_path),
        details: if details.is_empty() { None } else { Some(details) },
    })
}

// 旧的示例命令，保留用于兼容
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            greet,
            get_database_status,
            get_system_info,
            update_virus_database,
            select_folder,
            start_scan,
            start_realtime_scan
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn main() {
    run()
}
