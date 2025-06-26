use std::io::{self, Write};
use std::fs;
use clamav_ai_security::email_service::{EmailConfig, EmailProvider, SmtpConfig, AuthConfig, SenderConfig, RecipientsConfig, TemplateConfig, RetryConfig};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("╔══════════════════════════════════════════════════════════════╗");
    println!("║                    📧 邮件服务配置工具                       ║");
    println!("║                                                              ║");
    println!("║  快速配置AI安全报告的邮件发送功能                             ║");
    println!("╚══════════════════════════════════════════════════════════════╝");
    println!();

    let config = interactive_setup()?;
    save_config(&config)?;
    
    println!("✅ 邮件配置完成！");
    println!("📋 后续步骤:");
    println!("  1. 启动Tauri应用");
    println!("  2. 在设置页面测试邮件发送");
    println!("  3. 检查邮件接收情况");

    Ok(())
}

fn interactive_setup() -> Result<EmailConfig, Box<dyn std::error::Error>> {
    println!("🚀 开始配置邮件服务...");
    
    // 选择邮件服务提供商
    let provider = select_email_provider()?;
    
    // 获取认证信息
    let auth = get_auth_info()?;
    
    // 获取发件人信息
    let sender = get_sender_info()?;
    
    // 获取收件人配置
    let recipients = get_recipients()?;
    
    // 创建配置
    let config = EmailConfig {
        enabled: true,
        provider,
        smtp: get_default_smtp_config(&provider),
        auth,
        sender,
        recipients,
        templates: TemplateConfig {
            daily_report: "daily_report".to_string(),
            weekly_report: "weekly_report".to_string(),
            threat_alert: "threat_alert".to_string(),
            emergency_alert: "emergency_alert".to_string(),
        },
        retry: RetryConfig {
            max_attempts: 3,
            delay_seconds: 5,
        },
    };
    
    Ok(config)
}

fn select_email_provider() -> Result<EmailProvider, Box<dyn std::error::Error>> {
    println!("\n📮 选择邮件服务提供商:");
    println!("  1. Gmail (推荐)");
    println!("  2. Outlook/Hotmail");
    println!("  3. Yahoo Mail");
    println!("  4. QQ邮箱");
    println!("  5. 163邮箱");
    println!("  6. 自定义SMTP服务器");
    
    loop {
        print!("\n请选择 (1-6): ");
        io::stdout().flush()?;
        
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        
        match input.trim() {
            "1" => return Ok(EmailProvider::Gmail),
            "2" => return Ok(EmailProvider::Outlook),
            "3" => return Ok(EmailProvider::Yahoo),
            "4" => return Ok(EmailProvider::QQ),
            "5" => return Ok(EmailProvider::NetEase163),
            "6" => return Ok(EmailProvider::Custom),
            _ => println!("❌ 无效选择，请重新输入"),
        }
    }
}

fn get_default_smtp_config(provider: &EmailProvider) -> SmtpConfig {
    match provider {
        EmailProvider::Gmail => SmtpConfig {
            server: "smtp.gmail.com".to_string(),
            port: 587,
            use_tls: true,
            use_ssl: false,
        },
        EmailProvider::Outlook => SmtpConfig {
            server: "smtp-mail.outlook.com".to_string(),
            port: 587,
            use_tls: true,
            use_ssl: false,
        },
        EmailProvider::Yahoo => SmtpConfig {
            server: "smtp.mail.yahoo.com".to_string(),
            port: 587,
            use_tls: true,
            use_ssl: false,
        },
        EmailProvider::QQ => SmtpConfig {
            server: "smtp.qq.com".to_string(),
            port: 587,
            use_tls: true,
            use_ssl: false,
        },
        EmailProvider::NetEase163 => SmtpConfig {
            server: "smtp.163.com".to_string(),
            port: 25,
            use_tls: true,
            use_ssl: false,
        },
        EmailProvider::Custom => {
            println!("\n🔧 配置自定义SMTP服务器:");
            
            print!("SMTP服务器地址: ");
            io::stdout().flush().unwrap();
            let mut server = String::new();
            io::stdin().read_line(&mut server).unwrap();
            
            print!("SMTP端口 (默认587): ");
            io::stdout().flush().unwrap();
            let mut port_input = String::new();
            io::stdin().read_line(&mut port_input).unwrap();
            let port = port_input.trim().parse().unwrap_or(587);
            
            print!("使用TLS加密? (Y/n): ");
            io::stdout().flush().unwrap();
            let mut tls_input = String::new();
            io::stdin().read_line(&mut tls_input).unwrap();
            let use_tls = tls_input.trim().to_lowercase() != "n";
            
            SmtpConfig {
                server: server.trim().to_string(),
                port,
                use_tls,
                use_ssl: false,
            }
        }
    }
}

fn get_auth_info() -> Result<AuthConfig, Box<dyn std::error::Error>> {
    println!("\n🔐 配置邮箱认证信息:");
    
    print!("邮箱地址: ");
    io::stdout().flush()?;
    let mut username = String::new();
    io::stdin().read_line(&mut username)?;
    
    print!("邮箱密码或应用专用密码: ");
    io::stdout().flush()?;
    let password = rpassword::read_password()?;
    
    Ok(AuthConfig {
        username: username.trim().to_string(),
        password,
    })
}

fn get_sender_info() -> Result<SenderConfig, Box<dyn std::error::Error>> {
    println!("\n📤 配置发件人信息:");
    
    print!("发件人名称 (默认: AI安全助手): ");
    io::stdout().flush()?;
    let mut name = String::new();
    io::stdin().read_line(&mut name)?;
    let name = if name.trim().is_empty() {
        "AI安全助手".to_string()
    } else {
        name.trim().to_string()
    };
    
    print!("发件人邮箱地址: ");
    io::stdout().flush()?;
    let mut email = String::new();
    io::stdin().read_line(&mut email)?;
    
    Ok(SenderConfig {
        name,
        email: email.trim().to_string(),
    })
}

fn get_recipients() -> Result<RecipientsConfig, Box<dyn std::error::Error>> {
    println!("\n👥 配置收件人:");
    
    println!("默认收件人 (用于一般报告):");
    let mut default_recipients = Vec::new();
    loop {
        print!("  收件人 {} (回车结束): ", default_recipients.len() + 1);
        io::stdout().flush()?;
        let mut email = String::new();
        io::stdin().read_line(&mut email)?;
        let email = email.trim();
        if email.is_empty() {
            break;
        }
        default_recipients.push(email.to_string());
    }
    
    println!("\n紧急联系人 (用于高危威胁告警):");
    let mut emergency_recipients = Vec::new();
    loop {
        print!("  紧急联系人 {} (回车结束): ", emergency_recipients.len() + 1);
        io::stdout().flush()?;
        let mut email = String::new();
        io::stdin().read_line(&mut email)?;
        let email = email.trim();
        if email.is_empty() {
            break;
        }
        emergency_recipients.push(email.to_string());
    }
    
    // 如果没有设置紧急联系人，使用默认收件人
    if emergency_recipients.is_empty() {
        emergency_recipients = default_recipients.clone();
    }
    
    Ok(RecipientsConfig {
        default: default_recipients.clone(),
        emergency: emergency_recipients,
        reports: default_recipients,
    })
}

fn save_config(config: &EmailConfig) -> Result<(), Box<dyn std::error::Error>> {
    let config_path = "email_config.toml";
    
    let toml_content = toml::to_string_pretty(config)?;
    fs::write(config_path, toml_content)?;
    
    println!("✅ 配置已保存到: {}", config_path);
    Ok(())
}
