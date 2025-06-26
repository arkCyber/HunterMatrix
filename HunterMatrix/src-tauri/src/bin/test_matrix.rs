use huntermatrix::matrix_service::{MatrixService, MatrixConfig, ThreatInfo, ReportData};
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    
    println!("🔗 Matrix服务测试工具");
    println!("====================");
    
    // 检查配置文件
    let config_path = "matrix_config.toml";
    if !std::path::Path::new(config_path).exists() {
        println!("❌ Matrix配置文件不存在: {}", config_path);
        println!("请先运行: cargo run --bin setup_matrix");
        return Ok(());
    }
    
    // 加载配置
    println!("📋 加载Matrix配置...");
    let mut matrix_service = match MatrixService::from_config_file(config_path) {
        Ok(service) => service,
        Err(e) => {
            println!("❌ 加载配置失败: {}", e);
            return Ok(());
        }
    };
    
    // 验证配置
    println!("🔍 验证配置...");
    if let Err(e) = matrix_service.validate_config() {
        println!("❌ 配置验证失败: {}", e);
        return Ok(());
    }
    println!("✅ 配置验证通过");
    
    if !matrix_service.config.enabled {
        println!("⚠️  Matrix服务已禁用");
        return Ok(());
    }
    
    // 初始化Matrix客户端
    println!("🔌 初始化Matrix客户端...");
    if let Err(e) = matrix_service.initialize().await {
        println!("❌ Matrix客户端初始化失败: {}", e);
        return Ok(());
    }
    println!("✅ Matrix客户端初始化成功");
    
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    let test_type = args.get(1).map(|s| s.as_str()).unwrap_or("test");
    
    match test_type {
        "test" => {
            println!("🧪 发送测试消息...");
            test_message(&matrix_service).await?;
        }
        "threat" => {
            println!("🚨 发送威胁告警测试...");
            test_threat_alert(&matrix_service).await?;
        }
        "report" => {
            println!("📊 发送报告测试...");
            test_daily_report(&matrix_service).await?;
        }
        "rooms" => {
            println!("🏠 获取房间列表...");
            test_rooms(&matrix_service).await?;
        }
        _ => {
            println!("用法: cargo run --bin test_matrix [test|threat|report|rooms]");
            println!("  test   - 发送测试消息");
            println!("  threat - 发送威胁告警");
            println!("  report - 发送每日报告");
            println!("  rooms  - 获取房间列表");
        }
    }
    
    Ok(())
}

async fn test_message(matrix_service: &MatrixService) -> Result<(), Box<dyn std::error::Error>> {
    let room_id = &matrix_service.config.rooms.default_room;
    
    if room_id.is_empty() {
        println!("❌ 默认房间ID未配置");
        return Ok(());
    }
    
    match matrix_service.send_test_message(room_id).await {
        Ok(_) => println!("✅ 测试消息发送成功"),
        Err(e) => println!("❌ 测试消息发送失败: {}", e),
    }
    
    Ok(())
}

async fn test_threat_alert(matrix_service: &MatrixService) -> Result<(), Box<dyn std::error::Error>> {
    let threat = ThreatInfo {
        threat_type: "测试木马".to_string(),
        file_path: "/tmp/test_malware.exe".to_string(),
        severity: "high".to_string(),
        status: "detected".to_string(),
        detection_time: chrono::Utc::now().to_rfc3339(),
        confidence: 95.5,
        description: Some("这是一个测试威胁告警".to_string()),
    };
    
    match matrix_service.send_threat_alert(&threat).await {
        Ok(_) => println!("✅ 威胁告警发送成功"),
        Err(e) => println!("❌ 威胁告警发送失败: {}", e),
    }
    
    Ok(())
}

async fn test_daily_report(matrix_service: &MatrixService) -> Result<(), Box<dyn std::error::Error>> {
    let report_data = ReportData {
        title: "每日安全报告".to_string(),
        subtitle: "测试报告".to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        scanned_files: 1234,
        total_threats: 5,
        handled_threats: 5,
        scan_time: 2.5,
        success_rate: 98.5,
        threat_level: "low".to_string(),
        threats: vec![
            ThreatInfo {
                threat_type: "广告软件".to_string(),
                file_path: "/tmp/adware.exe".to_string(),
                severity: "low".to_string(),
                status: "quarantined".to_string(),
                detection_time: chrono::Utc::now().to_rfc3339(),
                confidence: 85.0,
                description: None,
            }
        ],
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
        Ok(_) => println!("✅ 每日报告发送成功"),
        Err(e) => println!("❌ 每日报告发送失败: {}", e),
    }
    
    Ok(())
}

async fn test_rooms(matrix_service: &MatrixService) -> Result<(), Box<dyn std::error::Error>> {
    match matrix_service.get_joined_rooms().await {
        Ok(rooms) => {
            println!("✅ 获取房间列表成功:");
            if rooms.is_empty() {
                println!("  (无已加入的房间)");
            } else {
                for (i, room) in rooms.iter().enumerate() {
                    println!("  {}. {}", i + 1, room);
                }
            }
        }
        Err(e) => println!("❌ 获取房间列表失败: {}", e),
    }
    
    Ok(())
}
