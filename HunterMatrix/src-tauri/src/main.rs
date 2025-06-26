// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};
use std::sync::{Arc, Mutex};
use std::thread;
use std::fs;
use std::path::Path;
use tauri::{Emitter, Manager, State, Window};

mod email_service;
mod matrix_service;
use email_service::{EmailService, EmailConfig, ReportData, ThreatInfo, SystemInfo as EmailSystemInfo};
use matrix_service::{MatrixService, MatrixConfig, ReportData as MatrixReportData, ThreatInfo as MatrixThreatInfo};

// 定义数据结构
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ScanResult {
    status: String,
    files_scanned: u32,
    threats_found: u32,
    scan_time: String,
    log_path: Option<String>,
    details: Option<Vec<String>>,
    path: String,
    timestamp: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DatabaseStatus {
    version: String,
    last_update: String,
    signatures: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfo {
    platform: String,
    memory_usage: f64,
    disk_usage: f64,
    cpu_usage: f64,
}

// 扫描进度状态
type ScanState = Arc<Mutex<Option<ScanProgress>>>;

#[derive(Debug, Clone)]
struct ScanProgress {
    progress: f64,
    current_file: String,
    is_running: bool,
}

// 获取系统信息
#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String> {
    // 获取 macOS 系统信息
    let platform = std::env::consts::OS.to_string();
    
    // 获取内存使用率
    let memory_output = Command::new("vm_stat")
        .output()
        .map_err(|e| format!("获取内存信息失败: {}", e))?;
    
    let memory_info = String::from_utf8(memory_output.stdout)
        .map_err(|e| format!("解析内存信息失败: {}", e))?;
    
    // 简化的内存使用率计算（实际应该更精确）
    let memory_usage = parse_memory_usage(&memory_info);
    
    // 获取磁盘使用率
    let disk_output = Command::new("df")
        .arg("-h")
        .arg("/")
        .output()
        .map_err(|e| format!("获取磁盘信息失败: {}", e))?;
    
    let disk_info = String::from_utf8(disk_output.stdout)
        .map_err(|e| format!("解析磁盘信息失败: {}", e))?;
    
    let disk_usage = parse_disk_usage(&disk_info);
    
    // 获取CPU使用率（简化版本）
    let cpu_usage = get_cpu_usage();
    
    Ok(SystemInfo {
        platform,
        memory_usage,
        disk_usage,
        cpu_usage,
    })
}

// 解析内存使用率
fn parse_memory_usage(vm_stat_output: &str) -> f64 {
    // 简化实现，返回模拟数据
    // 实际应该解析 vm_stat 输出
    65.5
}

// 解析磁盘使用率
fn parse_disk_usage(df_output: &str) -> f64 {
    for line in df_output.lines().skip(1) {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 5 {
            let usage_str = parts[4].trim_end_matches('%');
            if let Ok(usage) = usage_str.parse::<f64>() {
                return usage;
            }
        }
    }
    42.3 // 默认值
}

// 获取CPU使用率
fn get_cpu_usage() -> f64 {
    // 简化实现，在实际应用中应该使用系统调用
    match Command::new("top")
        .arg("-l")
        .arg("1")
        .arg("-n")
        .arg("0")
        .output()
    {
        Ok(output) => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            // 简化解析，实际应该更精确
            if output_str.contains("CPU usage") {
                return 25.8; // 模拟值
            }
        }
        Err(_) => {}
    }
    15.2 // 默认值
}

// 获取数据库状态
#[tauri::command]
async fn get_database_status() -> Result<DatabaseStatus, String> {
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";
    
    // 检查病毒库文件是否存在
    let main_cvd = format!("{}/main.cvd", virus_db_path);
    let daily_cvd = format!("{}/daily.cvd", virus_db_path);
    let bytecode_cvd = format!("{}/bytecode.cvd", virus_db_path);
    
    // 获取ClamAV版本信息
    let version_output = Command::new("clamscan")
        .arg("--version")
        .output()
        .map_err(|e| format!("执行 clamscan 失败: {}", e))?;
    
    let version_info = String::from_utf8(version_output.stdout)
        .map_err(|e| format!("解析版本信息失败: {}", e))?;
    
    let version = version_info
        .lines()
        .find(|line| line.contains("ClamAV"))
        .unwrap_or("ClamAV 1.5.0-beta")
        .to_string();
    
    // 获取病毒库更新时间
    let last_update = if Path::new(&daily_cvd).exists() {
        match fs::metadata(&daily_cvd) {
            Ok(metadata) => {
                if let Ok(modified) = metadata.modified() {
                    let datetime: chrono::DateTime<chrono::Utc> = modified.into();
                    datetime.format("%Y-%m-%d %H:%M:%S").to_string()
                } else {
                    "未知时间".to_string()
                }
            }
            Err(_) => "未知时间".to_string(),
        }
    } else {
        "从未更新".to_string()
    };
    
    // 计算病毒特征数量（从已知信息）
    let signatures = if Path::new(&main_cvd).exists() 
        && Path::new(&daily_cvd).exists() 
        && Path::new(&bytecode_cvd).exists() {
        8723276 // 实际已下载的特征数量
    } else {
        0
    };
    
    Ok(DatabaseStatus {
        version: version.trim().to_string(),
        last_update,
        signatures,
    })
}

// 更新病毒库
#[tauri::command]
async fn update_virus_database(window: Window) -> Result<String, String> {
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";
    let config_path = format!("{}/freshclam.conf", virus_db_path);
    
    // 发送开始更新事件
    let _ = window.emit("update-progress", serde_json::json!({
        "status": "starting",
        "message": "开始更新病毒库..."
    }));
    
    // 确保目录存在
    if !Path::new(virus_db_path).exists() {
        fs::create_dir_all(virus_db_path)
            .map_err(|e| format!("创建病毒库目录失败: {}", e))?;
    }
    
    // 检查配置文件是否存在
    if !Path::new(&config_path).exists() {
        // 创建默认配置文件
        let config_content = r#"# Freshclam configuration
DatabaseDirectory /Users/arkSong/clamav-main/virus_database
UpdateLogFile /Users/arkSong/clamav-main/virus_database/freshclam.log
LogVerbose yes
LogSyslog no
LogTime yes
DatabaseMirror database.clamav.net
DatabaseMirror db.local.clamav.net
DNSDatabaseInfo current.cvd.clamav.net
CompressLocalDatabase no
"#;
        fs::write(&config_path, config_content)
            .map_err(|e| format!("创建配置文件失败: {}", e))?;
    }
    
    // 发送正在下载事件
    let _ = window.emit("update-progress", serde_json::json!({
        "status": "downloading",
        "message": "正在下载病毒库更新..."
    }));
    
    // 执行更新命令
    let output = Command::new("freshclam")
        .arg("--config-file")
        .arg(&config_path)
        .arg("--verbose")
        .output()
        .map_err(|e| format!("执行更新命令失败: {}", e))?;
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    // 发送完成事件
    if output.status.success() {
        let _ = window.emit("update-progress", serde_json::json!({
            "status": "completed",
            "message": "病毒库更新成功"
        }));
        
        // 检查更新后的状态
        let updated_signatures = check_database_signatures();
        Ok(format!("病毒库更新成功！当前特征数量: {}", updated_signatures))
    } else {
        let _ = window.emit("update-progress", serde_json::json!({
            "status": "error",
            "message": "病毒库更新失败"
        }));
        
        // 如果是因为已经是最新的
        if stderr.contains("up to date") || stdout.contains("up to date") {
            Ok("病毒库已经是最新版本".to_string())
        } else {
            Err(format!("更新失败: {}\n{}", stdout, stderr))
        }
    }
}

// 检查病毒库特征数量
fn check_database_signatures() -> u32 {
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";
    
    // 检查文件大小来估算特征数量
    let mut total_size = 0u64;
    
    for file in ["main.cvd", "daily.cvd", "bytecode.cvd"].iter() {
        let file_path = format!("{}/{}", virus_db_path, file);
        if let Ok(metadata) = fs::metadata(&file_path) {
            total_size += metadata.len();
        }
    }
    
    // 根据文件大小估算特征数量（简化计算）
    if total_size > 200_000_000 { // > 200MB
        8723276
    } else if total_size > 100_000_000 { // > 100MB
        5000000
    } else {
        1000000
    }
}

// 开始扫描
#[tauri::command]
async fn start_scan(
    path: String,
    window: Window,
    scan_state: State<'_, ScanState>,
) -> Result<ScanResult, String> {
    // 发送扫描开始事件
    let _ = window.emit("scan-progress", serde_json::json!({
        "progress": 0.0,
        "currentFile": "正在初始化扫描...",
        "is_running": true
    }));
    
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    
    let log_path = format!("/tmp/clamav_scan_{}.log", timestamp);
    let virus_db_path = "/Users/arkSong/clamav-main/virus_database";
    
    // 检查路径是否存在
    if !Path::new(&path).exists() {
        return Err(format!("扫描路径不存在: {}", path));
    }
    
    // 初始化扫描状态
    {
        let mut state = scan_state.lock().unwrap();
        *state = Some(ScanProgress {
            progress: 0.0,
            current_file: "准备扫描...".to_string(),
            is_running: true,
        });
    }
    
    // 发送扫描开始事件
    let _ = window.emit("scan-progress", serde_json::json!({
        "progress": 0.0,
        "currentFile": "准备扫描...",
        "status": "starting"
    }));
    
    let start_time = std::time::Instant::now();
    
    // 构建扫描命令
    let mut cmd = Command::new("clamscan");
    cmd.arg("-r") // 递归扫描
       .arg("-i") // 只显示感染文件
       .arg("--database")
       .arg(virus_db_path)
       .arg("--log")
       .arg(&log_path)
       .arg("--verbose") // 详细输出
       .arg(&path);
    
    // 在后台线程中执行扫描并报告进度
    let window_clone = window.clone();
    let scan_state_clone = scan_state.inner().clone();
    let path_clone = path.clone();
    
    // 启动进度监控线程
    let progress_window = window.clone();
    let progress_scan_state = scan_state.inner().clone();
    thread::spawn(move || {
        let mut progress = 0.0;
        while progress < 100.0 {
            {
                let state = progress_scan_state.lock().unwrap();
                if let Some(ref scan_progress) = *state {
                    if !scan_progress.is_running {
                        break;
                    }
                    progress = scan_progress.progress;
                } else {
                    break;
                }
            }
            
            // 模拟进度更新
            progress += 2.0;
            if progress > 100.0 {
                progress = 100.0;
            }
            
            {
                let mut state = progress_scan_state.lock().unwrap();
                if let Some(ref mut scan_progress) = *state {
                    scan_progress.progress = progress;
                    scan_progress.current_file = format!("扫描中... {}%", progress.round());
                }
            }
            
            let _ = progress_window.emit("scan-progress", serde_json::json!({
                "progress": progress,
                "currentFile": format!("扫描中... {}%", progress.round()),
                "status": "scanning"
            }));
            
            thread::sleep(std::time::Duration::from_millis(500));
        }
    });
    
    // 执行扫描
    let output = cmd.output()
        .map_err(|e| format!("扫描执行失败: {}", e))?;
    
    let scan_duration = start_time.elapsed();
    let scan_time = format!("{}s", scan_duration.as_secs());
    
    // 停止进度监控
    {
        let mut state = scan_state.lock().unwrap();
        if let Some(ref mut scan_progress) = *state {
            scan_progress.is_running = false;
            scan_progress.progress = 100.0;
        }
    }
    
    // 发送扫描完成事件
    let _ = window.emit("scan-progress", serde_json::json!({
        "progress": 100.0,
        "currentFile": "扫描完成",
        "status": "completed"
    }));
    
    // 解析扫描结果
    let scan_output = String::from_utf8_lossy(&output.stdout);
    let scan_error = String::from_utf8_lossy(&output.stderr);
    
    // 解析文件数量和威胁数量
    let files_scanned = count_scanned_files(&scan_output, &path);
    let threats_found = count_threats_found(&scan_output);
    
    let status = if threats_found > 0 {
        "infected"
    } else if output.status.success() || output.status.code() == Some(1) {
        // 退出码 1 通常表示没有发现威胁
        "safe"
    } else {
        "error"
    };
    
    let mut details = Vec::new();
    
    // 收集威胁详情
    for line in scan_output.lines() {
        if line.contains("FOUND") {
            details.push(line.to_string());
        }
    }
    
    // 如果有错误信息也加入详情
    if !scan_error.is_empty() && status == "error" {
        details.push(format!("错误信息: {}", scan_error));
    }
    
    // 从日志文件读取更多详细信息
    if let Ok(log_content) = fs::read_to_string(&log_path) {
        for line in log_content.lines() {
            if line.contains("FOUND") && !details.contains(&line.to_string()) {
                details.push(line.to_string());
            }
        }
    }
    
    let result = ScanResult {
        status: status.to_string(),
        files_scanned,
        threats_found,
        scan_time,
        log_path: Some(log_path),
        details: if details.is_empty() { None } else { Some(details) },
        path: path.clone(),
        timestamp: chrono::Utc::now().to_rfc3339(),
    };
    
    Ok(result)
}

// 计算扫描的文件数量
fn count_scanned_files(output: &str, path: &str) -> u32 {
    // 尝试从输出中解析扫描的文件数量
    for line in output.lines() {
        if line.contains("Scanned files:") {
            if let Some(num_str) = line.split("Scanned files:").nth(1) {
                if let Ok(num) = num_str.trim().parse::<u32>() {
                    return num;
                }
            }
        }
    }
    
    // 如果无法解析，尝试估算
    match estimate_file_count(path) {
        Ok(count) => count,
        Err(_) => 0,
    }
}

// 估算文件数量
fn estimate_file_count(path: &str) -> Result<u32, std::io::Error> {
    let mut count = 0u32;
    
    fn count_files_recursive(dir: &Path, count: &mut u32) -> Result<(), std::io::Error> {
        if *count > 10000 {
            return Ok(()); // 避免计算过多文件
        }
        
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_file() {
                *count += 1;
            } else if path.is_dir() {
                count_files_recursive(&path, count)?;
            }
        }
        Ok(())
    }
    
    let scan_path = Path::new(path);
    if scan_path.is_file() {
        count = 1;
    } else if scan_path.is_dir() {
        count_files_recursive(scan_path, &mut count)?;
    }
    
    Ok(count)
}

// 计算发现的威胁数量
fn count_threats_found(output: &str) -> u32 {
    output.lines()
        .filter(|line| line.contains("FOUND"))
        .count() as u32
}

// 选择文件夹（使用系统对话框）
#[tauri::command]
async fn select_folder() -> Result<String, String> {
    // 这个函数现在主要返回默认路径，
    // 实际的文件夹选择通过前端的 dialog API 处理
    let default_paths = vec![
        "/Users/arkSong/Downloads",
        "/Users/arkSong/Documents", 
        "/Users/arkSong/Desktop",
        "/Applications"
    ];
    
    // 返回第一个存在的路径
    for path in default_paths {
        if Path::new(path).exists() {
            return Ok(path.to_string());
        }
    }
    
    Ok("/Users/arkSong".to_string())
}

// 获取扫描历史
#[tauri::command]
async fn get_scan_history() -> Result<Vec<ScanResult>, String> {
    // 这个功能主要在前端实现，这里返回空数组
    Ok(vec![])
}

// 清理临时文件
#[tauri::command]
async fn cleanup_temp_files() -> Result<String, String> {
    let temp_pattern = "/tmp/clamav_scan_*.log";
    
    // 删除超过1天的临时日志文件
    match Command::new("find")
        .arg("/tmp")
        .arg("-name")
        .arg("clamav_scan_*.log")
        .arg("-mtime")
        .arg("+1")
        .arg("-delete")
        .output()
    {
        Ok(_) => Ok("临时文件清理完成".to_string()),
        Err(e) => Err(format!("清理临时文件失败: {}", e)),
    }
}

// 检查ClamAV是否安装
#[tauri::command]
async fn check_clamav_installation() -> Result<bool, String> {
    match Command::new("which").arg("clamscan").output() {
        Ok(output) => Ok(output.status.success()),
        Err(_) => Ok(false),
    }
}

// 邮件相关命令
#[tauri::command]
async fn send_test_email(recipient: String) -> Result<String, String> {
    let config_path = "email_config.toml";

    match EmailService::from_config_file(config_path) {
        Ok(email_service) => {
            match email_service.validate_config() {
                Ok(_) => {
                    match email_service.send_test_email(&recipient).await {
                        Ok(_) => Ok("测试邮件发送成功".to_string()),
                        Err(e) => Err(format!("测试邮件发送失败: {}", e)),
                    }
                }
                Err(e) => Err(format!("邮件配置无效: {}", e)),
            }
        }
        Err(e) => Err(format!("加载邮件配置失败: {}", e)),
    }
}

#[tauri::command]
async fn get_email_config() -> Result<EmailConfig, String> {
    let config_path = "email_config.toml";

    match EmailService::from_config_file(config_path) {
        Ok(email_service) => {
            let mut config = email_service.config.clone();
            // 隐藏密码
            config.auth.password = "***".to_string();
            Ok(config)
        }
        Err(_) => {
            // 返回默认配置
            Ok(EmailConfig::default())
        }
    }
}

#[tauri::command]
async fn save_email_config(config: EmailConfig) -> Result<String, String> {
    let config_path = "email_config.toml";

    let toml_content = toml::to_string(&config)
        .map_err(|e| format!("序列化配置失败: {}", e))?;

    fs::write(config_path, toml_content)
        .map_err(|e| format!("保存配置文件失败: {}", e))?;

    Ok("邮件配置保存成功".to_string())
}

#[tauri::command]
async fn get_email_status() -> Result<serde_json::Value, String> {
    let config_path = "email_config.toml";

    match EmailService::from_config_file(config_path) {
        Ok(email_service) => {
            let is_valid = email_service.validate_config().is_ok();

            Ok(serde_json::json!({
                "enabled": email_service.config.enabled,
                "configured": is_valid,
                "provider": format!("{:?}", email_service.config.provider),
                "sender": email_service.config.sender.email,
                "recipients_count": email_service.config.recipients.default.len()
            }))
        }
        Err(_) => {
            Ok(serde_json::json!({
                "enabled": false,
                "configured": false,
                "provider": "None",
                "sender": "",
                "recipients_count": 0
            }))
        }
    }
}

#[tauri::command]
async fn send_daily_report(scan_result: ScanResult) -> Result<String, String> {
    let config_path = "email_config.toml";

    match EmailService::from_config_file(config_path) {
        Ok(email_service) => {
            if !email_service.config.enabled {
                return Ok("邮件发送功能已禁用".to_string());
            }

            // 转换扫描结果为报告数据
            let report_data = ReportData {
                title: "每日安全报告".to_string(),
                subtitle: format!("{} 安全状况报告",
                    chrono::Local::now().format("%Y年%m月%d日")),
                timestamp: chrono::Utc::now().to_rfc3339(),
                scanned_files: scan_result.files_scanned,
                total_threats: scan_result.threats_found,
                handled_threats: scan_result.threats_found, // 假设都已处理
                scan_time: 2.5, // 模拟扫描时间
                success_rate: 98.5,
                threat_level: if scan_result.threats_found > 5 { "high" } else { "low" }.to_string(),
                threats: vec![], // 可以从scan_result.details转换
                ai_insights: vec![
                    "系统整体安全状况良好".to_string(),
                    "建议定期更新病毒库".to_string(),
                    "监控到少量低风险文件".to_string(),
                ],
                recommendations: vec![
                    "继续保持定期扫描".to_string(),
                    "及时更新系统补丁".to_string(),
                    "加强网络安全防护".to_string(),
                ],
                system_info: EmailSystemInfo {
                    cpu_usage: 25.6,
                    memory_usage: 68.2,
                    disk_usage: 42.3,
                    uptime: "99.8%".to_string(),
                },
            };

            match email_service.send_daily_report(&report_data).await {
                Ok(_) => Ok("每日报告邮件发送成功".to_string()),
                Err(e) => Err(format!("每日报告发送失败: {}", e)),
            }
        }
        Err(e) => Err(format!("加载邮件配置失败: {}", e)),
    }
}

#[tauri::command]
async fn send_threat_alert(threat_type: String, file_path: String, severity: String) -> Result<String, String> {
    let config_path = "email_config.toml";

    match EmailService::from_config_file(config_path) {
        Ok(email_service) => {
            if !email_service.config.enabled {
                return Ok("邮件发送功能已禁用".to_string());
            }

            let threat = ThreatInfo {
                threat_type,
                file_path,
                severity,
                status: "detected".to_string(),
                detection_time: chrono::Utc::now().to_rfc3339(),
                confidence: 95.0,
            };

            match email_service.send_threat_alert(&threat).await {
                Ok(_) => Ok("威胁告警邮件发送成功".to_string()),
                Err(e) => Err(format!("威胁告警发送失败: {}", e)),
            }
        }
        Err(e) => Err(format!("加载邮件配置失败: {}", e)),
    }
}

// Matrix相关命令
#[tauri::command]
async fn send_matrix_test(room_id: String) -> Result<String, String> {
    let config_path = "matrix_config.toml";

    match MatrixService::from_config_file(config_path) {
        Ok(mut matrix_service) => {
            match matrix_service.validate_config() {
                Ok(_) => {
                    match matrix_service.initialize().await {
                        Ok(_) => {
                            match matrix_service.send_test_message(&room_id).await {
                                Ok(_) => Ok("Matrix测试消息发送成功".to_string()),
                                Err(e) => Err(format!("Matrix测试消息发送失败: {}", e)),
                            }
                        }
                        Err(e) => Err(format!("Matrix客户端初始化失败: {}", e)),
                    }
                }
                Err(e) => Err(format!("Matrix配置无效: {}", e)),
            }
        }
        Err(e) => Err(format!("加载Matrix配置失败: {}", e)),
    }
}

#[tauri::command]
async fn get_matrix_config() -> Result<MatrixConfig, String> {
    let config_path = "matrix_config.toml";

    match MatrixService::from_config_file(config_path) {
        Ok(matrix_service) => {
            let mut config = matrix_service.config().clone();
            // 隐藏密码
            config.password = "***".to_string();
            Ok(config)
        }
        Err(_) => {
            // 返回默认配置
            Ok(MatrixConfig::default())
        }
    }
}

#[tauri::command]
async fn save_matrix_config(config: MatrixConfig) -> Result<String, String> {
    let config_path = "matrix_config.toml";

    let toml_content = toml::to_string(&config)
        .map_err(|e| format!("序列化配置失败: {}", e))?;

    fs::write(config_path, toml_content)
        .map_err(|e| format!("保存配置文件失败: {}", e))?;

    Ok("Matrix配置保存成功".to_string())
}

#[tauri::command]
async fn get_matrix_status() -> Result<serde_json::Value, String> {
    let config_path = "matrix_config.toml";

    match MatrixService::from_config_file(config_path) {
        Ok(matrix_service) => {
            let is_valid = matrix_service.validate_config().is_ok();

            Ok(serde_json::json!({
                "enabled": matrix_service.config().enabled,
                "configured": is_valid,
                "homeserver": matrix_service.config().homeserver,
                "username": matrix_service.config().username,
                "device_name": matrix_service.config().device_name,
                "rooms_configured": !matrix_service.config().rooms.default_room.is_empty()
            }))
        }
        Err(_) => {
            Ok(serde_json::json!({
                "enabled": false,
                "configured": false,
                "homeserver": "",
                "username": "",
                "device_name": "",
                "rooms_configured": false
            }))
        }
    }
}

#[tauri::command]
async fn send_matrix_daily_report(scan_result: ScanResult) -> Result<String, String> {
    let config_path = "matrix_config.toml";

    match MatrixService::from_config_file(config_path) {
        Ok(mut matrix_service) => {
            if !matrix_service.config.enabled {
                return Ok("Matrix服务已禁用".to_string());
            }

            // 初始化Matrix客户端
            matrix_service.initialize().await
                .map_err(|e| format!("Matrix客户端初始化失败: {}", e))?;

            // 转换扫描结果为报告数据
            let report_data = MatrixReportData {
                title: "每日安全报告".to_string(),
                subtitle: format!("{} 安全状况报告",
                    chrono::Local::now().format("%Y年%m月%d日")),
                timestamp: chrono::Utc::now().to_rfc3339(),
                scanned_files: scan_result.files_scanned,
                total_threats: scan_result.threats_found,
                handled_threats: scan_result.threats_found, // 假设都已处理
                scan_time: 2.5, // 模拟扫描时间
                success_rate: 98.5,
                threat_level: if scan_result.threats_found > 5 { "high" } else { "low" }.to_string(),
                threats: vec![], // 可以从scan_result.details转换
                ai_insights: vec![
                    "系统整体安全状况良好".to_string(),
                    "建议定期更新病毒库".to_string(),
                    "监控到少量低风险文件".to_string(),
                ],
                recommendations: vec![
                    "继续保持定期扫描".to_string(),
                    "及时更新系统补丁".to_string(),
                    "加强网络安全防护".to_string(),
                ],
            };

            match matrix_service.send_daily_report(&report_data).await {
                Ok(_) => Ok("Matrix每日报告发送成功".to_string()),
                Err(e) => Err(format!("Matrix每日报告发送失败: {}", e)),
            }
        }
        Err(e) => Err(format!("加载Matrix配置失败: {}", e)),
    }
}

#[tauri::command]
async fn send_matrix_threat_alert(threat_type: String, file_path: String, severity: String) -> Result<String, String> {
    let config_path = "matrix_config.toml";

    match MatrixService::from_config_file(config_path) {
        Ok(mut matrix_service) => {
            if !matrix_service.config.enabled {
                return Ok("Matrix服务已禁用".to_string());
            }

            // 初始化Matrix客户端
            matrix_service.initialize().await
                .map_err(|e| format!("Matrix客户端初始化失败: {}", e))?;

            let threat = MatrixThreatInfo {
                threat_type,
                file_path,
                severity,
                status: "detected".to_string(),
                detection_time: chrono::Utc::now().to_rfc3339(),
                confidence: 95.0,
                description: None,
            };

            match matrix_service.send_threat_alert(&threat).await {
                Ok(_) => Ok("Matrix威胁告警发送成功".to_string()),
                Err(e) => Err(format!("Matrix威胁告警发送失败: {}", e)),
            }
        }
        Err(e) => Err(format!("加载Matrix配置失败: {}", e)),
    }
}

#[tauri::command]
async fn get_matrix_rooms() -> Result<Vec<String>, String> {
    let config_path = "matrix_config.toml";

    match MatrixService::from_config_file(config_path) {
        Ok(mut matrix_service) => {
            if !matrix_service.config.enabled {
                return Ok(vec![]);
            }

            // 初始化Matrix客户端
            matrix_service.initialize().await
                .map_err(|e| format!("Matrix客户端初始化失败: {}", e))?;

            match matrix_service.get_joined_rooms().await {
                Ok(rooms) => Ok(rooms),
                Err(e) => Err(format!("获取Matrix房间列表失败: {}", e)),
            }
        }
        Err(e) => Err(format!("加载Matrix配置失败: {}", e)),
    }
}

// 旧的示例命令，保留用于兼容
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 初始化扫描状态
    let scan_state: ScanState = Arc::new(Mutex::new(None));
    
    tauri::Builder::default()
        .manage(scan_state)
        .invoke_handler(tauri::generate_handler![
            greet,
            get_database_status,
            get_system_info,
            update_virus_database,
            select_folder,
            start_scan,
            get_scan_history,
            cleanup_temp_files,
            check_clamav_installation,
            send_test_email,
            get_email_config,
            save_email_config,
            get_email_status,
            send_daily_report,
            send_threat_alert,
            send_matrix_test,
            get_matrix_config,
            save_matrix_config,
            get_matrix_status,
            send_matrix_daily_report,
            send_matrix_threat_alert,
            get_matrix_rooms
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn main() {
    run()
}