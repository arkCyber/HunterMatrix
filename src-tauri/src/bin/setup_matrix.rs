use std::io::{self, Write};
use std::fs;
use huntermatrix::matrix_service::{MatrixConfig, RoomConfig, MessageFormat, RetryConfig};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("╔══════════════════════════════════════════════════════════════╗");
    println!("║                    🔗 Matrix服务配置工具                     ║");
    println!("║                                                              ║");
    println!("║  快速配置AI安全报告的Matrix消息发送功能                       ║");
    println!("╚══════════════════════════════════════════════════════════════╝");
    println!();

    let config = interactive_setup()?;
    save_config(&config)?;
    
    println!("✅ Matrix配置完成！");
    println!("📋 后续步骤:");
    println!("  1. 启动Tauri应用");
    println!("  2. 在设置页面测试Matrix发送");
    println!("  3. 检查Matrix房间中的消息");

    Ok(())
}

fn interactive_setup() -> Result<MatrixConfig, Box<dyn std::error::Error>> {
    println!("🚀 开始配置Matrix服务...");
    
    // 获取服务器信息
    let homeserver = get_homeserver()?;
    
    // 获取认证信息
    let (username, password) = get_auth_info()?;
    
    // 获取设备名称
    let device_name = get_device_name()?;
    
    // 获取房间配置
    let rooms = get_room_config()?;
    
    // 获取消息格式配置
    let message_format = get_message_format()?;
    
    // 创建配置
    let config = MatrixConfig {
        enabled: true,
        homeserver,
        username,
        password,
        device_name,
        rooms,
        message_format,
        retry: RetryConfig {
            max_attempts: 3,
            delay_seconds: 5,
        },
    };
    
    Ok(config)
}

fn get_homeserver() -> Result<String, Box<dyn std::error::Error>> {
    println!("\n🏠 配置Matrix服务器:");
    println!("  1. matrix.org (官方服务器)");
    println!("  2. element.io");
    println!("  3. 自定义服务器");
    
    loop {
        print!("\n请选择 (1-3): ");
        io::stdout().flush()?;
        
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        
        match input.trim() {
            "1" => return Ok("https://matrix.org".to_string()),
            "2" => return Ok("https://matrix-client.matrix.org".to_string()),
            "3" => {
                print!("请输入自定义服务器地址 (例如: https://matrix.example.com): ");
                io::stdout().flush()?;
                let mut server = String::new();
                io::stdin().read_line(&mut server)?;
                return Ok(server.trim().to_string());
            }
            _ => println!("❌ 无效选择，请重新输入"),
        }
    }
}

fn get_auth_info() -> Result<(String, String), Box<dyn std::error::Error>> {
    println!("\n🔐 配置Matrix认证信息:");
    
    print!("Matrix用户名 (例如: @security-bot:matrix.org): ");
    io::stdout().flush()?;
    let mut username = String::new();
    io::stdin().read_line(&mut username)?;
    
    print!("Matrix密码或访问令牌: ");
    io::stdout().flush()?;
    let password = rpassword::read_password()?;
    
    Ok((username.trim().to_string(), password))
}

fn get_device_name() -> Result<String, Box<dyn std::error::Error>> {
    println!("\n📱 配置设备信息:");
    
    print!("设备名称 (默认: AI-Security-Bot): ");
    io::stdout().flush()?;
    let mut device_name = String::new();
    io::stdin().read_line(&mut device_name)?;
    
    let device_name = if device_name.trim().is_empty() {
        "AI-Security-Bot".to_string()
    } else {
        device_name.trim().to_string()
    };
    
    Ok(device_name)
}

fn get_room_config() -> Result<RoomConfig, Box<dyn std::error::Error>> {
    println!("\n🏠 配置Matrix房间:");
    println!("提示: 房间ID格式为 !roomid:server.com");
    
    print!("默认房间ID (用于一般消息): ");
    io::stdout().flush()?;
    let mut default_room = String::new();
    io::stdin().read_line(&mut default_room)?;
    
    print!("紧急告警房间ID (可选，回车跳过): ");
    io::stdout().flush()?;
    let mut emergency_room = String::new();
    io::stdin().read_line(&mut emergency_room)?;
    let emergency_room = if emergency_room.trim().is_empty() {
        default_room.trim().to_string()
    } else {
        emergency_room.trim().to_string()
    };
    
    print!("报告房间ID (可选，回车跳过): ");
    io::stdout().flush()?;
    let mut reports_room = String::new();
    io::stdin().read_line(&mut reports_room)?;
    let reports_room = if reports_room.trim().is_empty() {
        default_room.trim().to_string()
    } else {
        reports_room.trim().to_string()
    };
    
    print!("管理员房间ID (可选，回车跳过): ");
    io::stdout().flush()?;
    let mut admin_room = String::new();
    io::stdin().read_line(&mut admin_room)?;
    let admin_room = if admin_room.trim().is_empty() {
        default_room.trim().to_string()
    } else {
        admin_room.trim().to_string()
    };
    
    Ok(RoomConfig {
        default_room: default_room.trim().to_string(),
        emergency_room,
        reports_room,
        admin_room,
    })
}

fn get_message_format() -> Result<MessageFormat, Box<dyn std::error::Error>> {
    println!("\n📝 配置消息格式:");
    
    print!("使用Markdown格式? (Y/n): ");
    io::stdout().flush()?;
    let mut markdown_input = String::new();
    io::stdin().read_line(&mut markdown_input)?;
    let use_markdown = markdown_input.trim().to_lowercase() != "n";
    
    print!("包含时间戳? (Y/n): ");
    io::stdout().flush()?;
    let mut timestamp_input = String::new();
    io::stdin().read_line(&mut timestamp_input)?;
    let include_timestamp = timestamp_input.trim().to_lowercase() != "n";
    
    print!("包含严重程度表情符号? (Y/n): ");
    io::stdout().flush()?;
    let mut emoji_input = String::new();
    io::stdin().read_line(&mut emoji_input)?;
    let include_severity_emoji = emoji_input.trim().to_lowercase() != "n";
    
    Ok(MessageFormat {
        use_markdown,
        use_html: false,
        include_timestamp,
        include_severity_emoji,
    })
}

fn save_config(config: &MatrixConfig) -> Result<(), Box<dyn std::error::Error>> {
    let config_path = "matrix_config.toml";
    
    let toml_content = toml::to_string_pretty(config)?;
    fs::write(config_path, toml_content)?;
    
    println!("✅ 配置已保存到: {}", config_path);
    
    // 显示配置摘要
    println!("\n📋 配置摘要:");
    println!("  服务器: {}", config.homeserver);
    println!("  用户名: {}", config.username);
    println!("  设备名: {}", config.device_name);
    println!("  默认房间: {}", config.rooms.default_room);
    println!("  Markdown格式: {}", if config.message_format.use_markdown { "是" } else { "否" });
    
    println!("\n💡 使用提示:");
    println!("  1. 确保机器人用户已加入配置的房间");
    println!("  2. 检查房间权限设置");
    println!("  3. 测试消息发送功能");
    println!("  4. 配置通知设置");
    
    Ok(())
}

fn show_help() {
    println!("📖 Matrix服务配置工具使用说明");
    println!();
    println!("🎯 功能:");
    println!("  - 交互式配置Matrix服务");
    println!("  - 支持多种Matrix服务器");
    println!("  - 自动验证配置格式");
    println!("  - 生成完整的配置文件");
    println!();
    println!("🏠 支持的Matrix服务器:");
    println!("  - matrix.org (官方服务器)");
    println!("  - element.io");
    println!("  - 自建Matrix服务器");
    println!();
    println!("🔐 安全提示:");
    println!("  - 使用强密码或访问令牌");
    println!("  - 定期轮换密码");
    println!("  - 启用两步验证");
    println!("  - 限制机器人权限");
    println!();
    println!("🏠 房间设置建议:");
    println!("  1. 创建专门的安全频道");
    println!("  2. 设置适当的权限级别");
    println!("  3. 邀请相关安全团队成员");
    println!("  4. 配置通知设置");
    println!();
    println!("🚀 快速开始:");
    println!("  cargo run --bin setup_matrix");
}
