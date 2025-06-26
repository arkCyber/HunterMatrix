use anyhow::{anyhow, Result};
use chrono::{DateTime, Utc};
use handlebars::Handlebars;
use lettre::message::{header, MultiPart, SinglePart};
use lettre::transport::smtp::authentication::Credentials;
use lettre::{Message, SmtpTransport, Transport};
use log::{error, info, warn};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

/// 邮件配置结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailConfig {
    pub enabled: bool,
    pub provider: EmailProvider,
    pub smtp: SmtpConfig,
    pub auth: AuthConfig,
    pub sender: SenderConfig,
    pub recipients: RecipientsConfig,
    pub templates: TemplateConfig,
    pub retry: RetryConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EmailProvider {
    Gmail,
    Outlook,
    Yahoo,
    QQ,
    #[serde(rename = "163")]
    NetEase163,
    Custom,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmtpConfig {
    pub server: String,
    pub port: u16,
    pub use_tls: bool,
    pub use_ssl: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthConfig {
    pub username: String,
    pub password: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SenderConfig {
    pub name: String,
    pub email: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecipientsConfig {
    pub default: Vec<String>,
    pub emergency: Vec<String>,
    pub reports: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateConfig {
    pub daily_report: String,
    pub weekly_report: String,
    pub threat_alert: String,
    pub emergency_alert: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryConfig {
    pub max_attempts: u32,
    pub delay_seconds: u64,
}

/// 报告数据结构
#[derive(Debug, Serialize, Deserialize)]
pub struct ReportData {
    pub title: String,
    pub subtitle: String,
    pub timestamp: String,
    pub scanned_files: u32,
    pub total_threats: u32,
    pub handled_threats: u32,
    pub scan_time: f64,
    pub success_rate: f64,
    pub threat_level: String,
    pub threats: Vec<ThreatInfo>,
    pub ai_insights: Vec<String>,
    pub recommendations: Vec<String>,
    pub system_info: SystemInfo,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ThreatInfo {
    pub threat_type: String,
    pub file_path: String,
    pub severity: String,
    pub status: String,
    pub detection_time: String,
    pub confidence: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfo {
    pub cpu_usage: f64,
    pub memory_usage: f64,
    pub disk_usage: f64,
    pub uptime: String,
}

/// 邮件服务主结构
pub struct EmailService {
    pub config: EmailConfig,
    handlebars: Handlebars<'static>,
}

impl EmailService {
    /// 创建新的邮件服务实例
    pub fn new(config: EmailConfig) -> Result<Self> {
        let mut handlebars = Handlebars::new();
        
        // 注册邮件模板
        Self::register_templates(&mut handlebars)?;
        
        Ok(EmailService {
            config,
            handlebars,
        })
    }

    /// 从配置文件加载邮件服务
    pub fn from_config_file<P: AsRef<Path>>(config_path: P) -> Result<Self> {
        let config_content = fs::read_to_string(config_path)?;
        let config: EmailConfig = toml::from_str(&config_content)?;
        Self::new(config)
    }

    /// 注册邮件模板
    fn register_templates(handlebars: &mut Handlebars) -> Result<()> {
        // 注册Handlebars助手函数
        handlebars.register_helper("eq", Box::new(|h: &handlebars::Helper, _: &Handlebars, _: &handlebars::Context, _: &mut handlebars::RenderContext, out: &mut dyn handlebars::Output| -> handlebars::HelperResult {
            let param1 = h.param(0).and_then(|v| v.value().as_str()).unwrap_or("");
            let param2 = h.param(1).and_then(|v| v.value().as_str()).unwrap_or("");

            if param1 == param2 {
                out.write("true")?;
            } else {
                out.write("false")?;
            }
            Ok(())
        }));

        // 每日报告模板 - 直接在代码中定义
        let daily_template = include_str!("../templates/daily_report.hbs");
        handlebars.register_template_string("daily_report", daily_template)?;

        // 威胁告警模板
        let threat_template = include_str!("../templates/threat_alert.hbs");
        handlebars.register_template_string("threat_alert", threat_template)?;

        // 紧急告警模板
        let emergency_template = include_str!("../templates/emergency_alert.hbs");
        handlebars.register_template_string("emergency_alert", emergency_template)?;

        Ok(())
    }

    /// 获取SMTP配置
    fn get_smtp_config(&self) -> SmtpConfig {
        match self.config.provider {
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
            EmailProvider::Custom => self.config.smtp.clone(),
        }
    }

    /// 创建SMTP传输
    fn create_smtp_transport(&self) -> Result<SmtpTransport> {
        let smtp_config = self.get_smtp_config();
        
        let credentials = Credentials::new(
            self.config.auth.username.clone(),
            self.config.auth.password.clone(),
        );

        let transport = if smtp_config.use_ssl {
            SmtpTransport::relay(&smtp_config.server)?
                .port(smtp_config.port)
                .credentials(credentials)
                .build()
        } else if smtp_config.use_tls {
            SmtpTransport::starttls_relay(&smtp_config.server)?
                .port(smtp_config.port)
                .credentials(credentials)
                .build()
        } else {
            SmtpTransport::builder_dangerous(&smtp_config.server)
                .port(smtp_config.port)
                .credentials(credentials)
                .build()
        };

        Ok(transport)
    }

    /// 发送每日报告
    pub async fn send_daily_report(&self, report_data: &ReportData) -> Result<()> {
        if !self.config.enabled {
            warn!("邮件发送功能已禁用");
            return Ok(());
        }

        let subject = format!("📊 每日安全报告 - {}", 
            chrono::Local::now().format("%Y-%m-%d"));

        let html_content = self.handlebars.render("daily_report", report_data)?;
        
        self.send_email(
            &subject,
            &html_content,
            &self.config.recipients.reports,
        ).await
    }

    /// 发送威胁告警
    pub async fn send_threat_alert(&self, threat: &ThreatInfo) -> Result<()> {
        if !self.config.enabled {
            warn!("邮件发送功能已禁用");
            return Ok(());
        }

        let subject = format!("🚨 威胁告警 - {} ({})", 
            threat.threat_type, threat.severity);

        let template_data = serde_json::json!({
            "threat": threat,
            "timestamp": Utc::now().to_rfc3339(),
            "dashboard_url": "http://localhost:8080"
        });

        let html_content = self.handlebars.render("threat_alert", &template_data)?;
        
        let recipients = if threat.severity == "high" || threat.severity == "critical" {
            &self.config.recipients.emergency
        } else {
            &self.config.recipients.default
        };

        self.send_email(&subject, &html_content, recipients).await
    }

    /// 发送紧急告警
    pub async fn send_emergency_alert(&self, threats: &[ThreatInfo]) -> Result<()> {
        if !self.config.enabled {
            warn!("邮件发送功能已禁用");
            return Ok(());
        }

        let subject = format!("🚨🚨 紧急安全告警 - {}个严重威胁", threats.len());

        let template_data = serde_json::json!({
            "threats": threats,
            "critical_count": threats.len(),
            "timestamp": Utc::now().to_rfc3339(),
            "emergency_dashboard": "http://localhost:8080#emergency"
        });

        let html_content = self.handlebars.render("emergency_alert", &template_data)?;
        
        self.send_email(
            &subject,
            &html_content,
            &self.config.recipients.emergency,
        ).await
    }

    /// 发送测试邮件
    pub async fn send_test_email(&self, recipient: &str) -> Result<()> {
        let subject = "🧪 AI安全助手邮件配置测试";
        
        let template_data = serde_json::json!({
            "title": "邮件配置测试",
            "subtitle": "AI安全助手邮件服务测试",
            "test_time": Utc::now().to_rfc3339(),
            "provider": format!("{:?}", self.config.provider),
            "sender": self.config.sender.email
        });

        let test_template = r#"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { background: white; padding: 30px; border-radius: 8px; }
        .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; }
        .alert-success { background: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 {{title}}</h1>
            <p>{{subtitle}}</p>
        </div>
        
        <div class="alert-success">
            <strong>✅ 邮件配置测试成功！</strong><br>
            如果您收到这封邮件，说明邮件服务配置正确。
        </div>

        <h3>📋 配置信息</h3>
        <ul>
            <li>邮件服务商: {{provider}}</li>
            <li>发件人: {{sender}}</li>
            <li>测试时间: {{test_time}}</li>
        </ul>

        <p><strong>🤖 AI安全助手</strong><br>
        邮件服务已准备就绪，可以正常发送安全报告和告警。</p>
    </div>
</body>
</html>
        "#;

        let mut handlebars = Handlebars::new();
        handlebars.register_template_string("test", test_template)?;
        let html_content = handlebars.render("test", &template_data)?;
        
        self.send_email(&subject, &html_content, &[recipient.to_string()]).await
    }

    /// 核心邮件发送方法
    async fn send_email(
        &self,
        subject: &str,
        html_content: &str,
        recipients: &[String],
    ) -> Result<()> {
        let transport = self.create_smtp_transport()?;

        for recipient in recipients {
            let email = Message::builder()
                .from(format!("{} <{}>", self.config.sender.name, self.config.sender.email).parse()?)
                .to(recipient.parse()?)
                .subject(subject)
                .multipart(
                    MultiPart::alternative()
                        .singlepart(
                            SinglePart::builder()
                                .header(header::ContentType::TEXT_HTML)
                                .body(html_content.to_string()),
                        )
                )?;

            // 重试机制
            let mut attempts = 0;
            let max_attempts = self.config.retry.max_attempts;
            
            while attempts < max_attempts {
                match transport.send(&email) {
                    Ok(_) => {
                        info!("邮件发送成功: {} -> {}", subject, recipient);
                        break;
                    }
                    Err(e) => {
                        attempts += 1;
                        error!("邮件发送失败 (尝试 {}/{}): {}", attempts, max_attempts, e);
                        
                        if attempts < max_attempts {
                            tokio::time::sleep(
                                tokio::time::Duration::from_secs(self.config.retry.delay_seconds)
                            ).await;
                        } else {
                            return Err(anyhow!("邮件发送失败，已达到最大重试次数: {}", e));
                        }
                    }
                }
            }
        }

        Ok(())
    }

    /// 验证邮件配置
    pub fn validate_config(&self) -> Result<()> {
        if self.config.auth.username.is_empty() {
            return Err(anyhow!("邮箱用户名不能为空"));
        }

        if self.config.auth.password.is_empty() {
            return Err(anyhow!("邮箱密码不能为空"));
        }

        if self.config.sender.email.is_empty() {
            return Err(anyhow!("发件人邮箱不能为空"));
        }

        if self.config.recipients.default.is_empty() {
            return Err(anyhow!("至少需要一个默认收件人"));
        }

        Ok(())
    }
}

impl Default for EmailConfig {
    fn default() -> Self {
        EmailConfig {
            enabled: false,
            provider: EmailProvider::Gmail,
            smtp: SmtpConfig {
                server: "smtp.gmail.com".to_string(),
                port: 587,
                use_tls: true,
                use_ssl: false,
            },
            auth: AuthConfig {
                username: String::new(),
                password: String::new(),
            },
            sender: SenderConfig {
                name: "AI安全助手".to_string(),
                email: String::new(),
            },
            recipients: RecipientsConfig {
                default: vec![],
                emergency: vec![],
                reports: vec![],
            },
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
        }
    }
}
