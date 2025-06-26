use anyhow::{anyhow, Result};
use chrono::{DateTime, Utc};
use log::{error, info, warn};
use matrix_sdk::{
    config::SyncSettings,
    room::Room,
    ruma::{
        events::room::message::{
            MessageType, OriginalSyncRoomMessageEvent, RoomMessageEventContent,
            TextMessageEventContent,
        },
        RoomId, UserId,
    },
    Client, ClientBuilder,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use url::Url;

/// Matrix配置结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatrixConfig {
    pub enabled: bool,
    pub homeserver: String,
    pub username: String,
    pub password: String,
    pub device_name: String,
    pub rooms: RoomConfig,
    pub message_format: MessageFormat,
    pub retry: RetryConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoomConfig {
    pub default_room: String,        // 默认房间ID
    pub emergency_room: String,      // 紧急告警房间ID
    pub reports_room: String,        // 报告房间ID
    pub admin_room: String,          // 管理员房间ID
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageFormat {
    pub use_markdown: bool,
    pub use_html: bool,
    pub include_timestamp: bool,
    pub include_severity_emoji: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryConfig {
    pub max_attempts: u32,
    pub delay_seconds: u64,
}

/// 威胁信息结构
#[derive(Debug, Serialize, Deserialize)]
pub struct ThreatInfo {
    pub threat_type: String,
    pub file_path: String,
    pub severity: String,
    pub status: String,
    pub detection_time: String,
    pub confidence: f64,
    pub description: Option<String>,
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
}

/// Matrix服务主结构
pub struct MatrixService {
    config: MatrixConfig,
    client: Option<Client>,
}

impl MatrixService {
    /// 创建新的Matrix服务实例
    pub fn new(config: MatrixConfig) -> Self {
        MatrixService {
            config,
            client: None,
        }
    }

    /// 获取配置引用
    pub fn config(&self) -> &MatrixConfig {
        &self.config
    }

    /// 获取可变配置引用
    pub fn config_mut(&mut self) -> &mut MatrixConfig {
        &mut self.config
    }

    /// 从配置文件加载Matrix服务
    pub fn from_config_file<P: AsRef<Path>>(config_path: P) -> Result<Self> {
        let config_content = fs::read_to_string(config_path)?;
        let config: MatrixConfig = toml::from_str(&config_content)?;
        Ok(Self::new(config))
    }

    /// 初始化Matrix客户端并登录
    pub async fn initialize(&mut self) -> Result<()> {
        if !self.config.enabled {
            warn!("Matrix服务已禁用");
            return Ok(());
        }

        let homeserver_url = Url::parse(&self.config.homeserver)?;
        
        // TODO: Fix matrix-sdk version compatibility
        // let client = ClientBuilder::new()
        //     .homeserver_url(homeserver_url)
        //     .build()
        //     .await?;

        // // 登录
        // client
        //     .login_username(&self.config.username, &self.config.password)
        //     .device_id(&self.config.device_name)
        //     .send()
        //     .await?;

        // info!("Matrix客户端登录成功: {}", self.config.username);

        // // 启动同步
        // let sync_settings = SyncSettings::default().token(client.sync_token().await);
        
        warn!("Matrix service temporarily disabled due to SDK version incompatibility");
        return Err(anyhow!("Matrix SDK version incompatibility"));
        
        // tokio::spawn({
        //     let client = client.clone();
        //     async move {
        //         client.sync(sync_settings).await;
        //     }
        // });

        // self.client = Some(client);
        // Ok(())
    }

    /// 发送每日报告
    pub async fn send_daily_report(&self, report_data: &ReportData) -> Result<()> {
        if !self.config.enabled {
            warn!("Matrix服务已禁用");
            return Ok(());
        }

        let room_id = &self.config.rooms.reports_room;
        let message = self.format_daily_report(report_data);
        
        self.send_message(room_id, &message).await
    }

    /// 发送威胁告警
    pub async fn send_threat_alert(&self, threat: &ThreatInfo) -> Result<()> {
        if !self.config.enabled {
            warn!("Matrix服务已禁用");
            return Ok(());
        }

        let room_id = if threat.severity == "high" || threat.severity == "critical" {
            &self.config.rooms.emergency_room
        } else {
            &self.config.rooms.default_room
        };

        let message = self.format_threat_alert(threat);
        
        self.send_message(room_id, &message).await
    }

    /// 发送紧急告警
    pub async fn send_emergency_alert(&self, threats: &[ThreatInfo]) -> Result<()> {
        if !self.config.enabled {
            warn!("Matrix服务已禁用");
            return Ok(());
        }

        let room_id = &self.config.rooms.emergency_room;
        let message = self.format_emergency_alert(threats);
        
        self.send_message(room_id, &message).await
    }

    /// 发送测试消息
    pub async fn send_test_message(&self, room_id: &str) -> Result<()> {
        if !self.config.enabled {
            return Err(anyhow!("Matrix服务已禁用"));
        }

        let message = self.format_test_message();
        self.send_message(room_id, &message).await
    }

    /// 发送自定义消息
    pub async fn send_custom_message(&self, room_id: &str, content: &str) -> Result<()> {
        if !self.config.enabled {
            warn!("Matrix服务已禁用");
            return Ok(());
        }

        self.send_message(room_id, content).await
    }

    /// 核心消息发送方法
    async fn send_message(&self, room_id: &str, content: &str) -> Result<()> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Matrix客户端未初始化"))?;

        let room_id = RoomId::parse(room_id)?;
        let room = client.get_room(&room_id)
            .ok_or_else(|| anyhow!("找不到房间: {}", room_id))?;

        let message_content = if self.config.message_format.use_html {
            RoomMessageEventContent::text_html(content, content)
        } else if self.config.message_format.use_markdown {
            RoomMessageEventContent::text_markdown(content)
        } else {
            RoomMessageEventContent::text_plain(content)
        };

        // 重试机制
        let mut attempts = 0;
        let max_attempts = self.config.retry.max_attempts;
        
        while attempts < max_attempts {
            match room.send(message_content.clone()).await {
                Ok(_) => {
                    info!("Matrix消息发送成功: {}", room_id);
                    return Ok(());
                }
                Err(e) => {
                    attempts += 1;
                    error!("Matrix消息发送失败 (尝试 {}/{}): {}", attempts, max_attempts, e);
                    
                    if attempts < max_attempts {
                        tokio::time::sleep(
                            tokio::time::Duration::from_secs(self.config.retry.delay_seconds)
                        ).await;
                    } else {
                        return Err(anyhow!("Matrix消息发送失败，已达到最大重试次数: {}", e));
                    }
                }
            }
        }

        Ok(())
    }

    /// 格式化每日报告消息
    fn format_daily_report(&self, report_data: &ReportData) -> String {
        let timestamp = if self.config.message_format.include_timestamp {
            format!("\n🕐 生成时间: {}", report_data.timestamp)
        } else {
            String::new()
        };

        let threat_emoji = if self.config.message_format.include_severity_emoji {
            match report_data.threat_level.as_str() {
                "high" => "🔴",
                "medium" => "🟡",
                "low" => "🟢",
                _ => "⚪",
            }
        } else {
            ""
        };

        if self.config.message_format.use_markdown {
            format!(
                r#"# 📊 每日安全报告 {}

## 📈 统计概览
- **扫描文件**: {} 个
- **检测威胁**: {} 个
- **已处理威胁**: {} 个
- **扫描时间**: {:.1}s
- **成功率**: {:.1}%
- **威胁等级**: {} {}

## 🧠 AI洞察
{}

## 💡 安全建议
{}

## 🔗 快速链接
[查看详细报告](http://localhost:8080) | [系统设置](http://localhost:8080#settings)
{}
"#,
                threat_emoji,
                report_data.scanned_files,
                report_data.total_threats,
                report_data.handled_threats,
                report_data.scan_time,
                report_data.success_rate,
                report_data.threat_level,
                threat_emoji,
                report_data.ai_insights.iter()
                    .map(|insight| format!("• {}", insight))
                    .collect::<Vec<_>>()
                    .join("\n"),
                report_data.recommendations.iter()
                    .map(|rec| format!("• {}", rec))
                    .collect::<Vec<_>>()
                    .join("\n"),
                timestamp
            )
        } else {
            format!(
                "📊 每日安全报告 {}\n\n📈 统计概览:\n• 扫描文件: {} 个\n• 检测威胁: {} 个\n• 已处理威胁: {} 个\n• 扫描时间: {:.1}s\n• 成功率: {:.1}%\n• 威胁等级: {} {}\n\n🧠 AI洞察:\n{}\n\n💡 安全建议:\n{}\n\n🔗 查看详细: http://localhost:8080{}",
                threat_emoji,
                report_data.scanned_files,
                report_data.total_threats,
                report_data.handled_threats,
                report_data.scan_time,
                report_data.success_rate,
                report_data.threat_level,
                threat_emoji,
                report_data.ai_insights.iter()
                    .map(|insight| format!("• {}", insight))
                    .collect::<Vec<_>>()
                    .join("\n"),
                report_data.recommendations.iter()
                    .map(|rec| format!("• {}", rec))
                    .collect::<Vec<_>>()
                    .join("\n"),
                timestamp
            )
        }
    }

    /// 格式化威胁告警消息
    fn format_threat_alert(&self, threat: &ThreatInfo) -> String {
        let severity_emoji = if self.config.message_format.include_severity_emoji {
            match threat.severity.as_str() {
                "critical" => "🔴",
                "high" => "🟠",
                "medium" => "🟡",
                "low" => "🟢",
                _ => "⚪",
            }
        } else {
            ""
        };

        let timestamp = if self.config.message_format.include_timestamp {
            format!("\n🕐 检测时间: {}", threat.detection_time)
        } else {
            String::new()
        };

        if self.config.message_format.use_markdown {
            format!(
                r#"# 🚨 威胁告警 {}

## 🔍 威胁详情
- **类型**: {}
- **文件**: `{}`
- **严重程度**: {} {}
- **置信度**: {:.1}%
- **状态**: {}

## ⚡ 建议措施
• 立即隔离可疑文件
• 进行深度系统扫描
• 检查相关系统文件
• 更新病毒库到最新版本

## 🔗 快速响应
[查看详情](http://localhost:8080#incident) | [启动响应](http://localhost:8080#response)
{}
"#,
                severity_emoji,
                threat.threat_type,
                threat.file_path,
                threat.severity,
                severity_emoji,
                threat.confidence,
                threat.status,
                timestamp
            )
        } else {
            format!(
                "🚨 威胁告警 {}\n\n🔍 威胁详情:\n• 类型: {}\n• 文件: {}\n• 严重程度: {} {}\n• 置信度: {:.1}%\n• 状态: {}\n\n⚡ 建议措施:\n• 立即隔离可疑文件\n• 进行深度系统扫描\n• 检查相关系统文件\n• 更新病毒库到最新版本\n\n🔗 查看详情: http://localhost:8080#incident{}",
                severity_emoji,
                threat.threat_type,
                threat.file_path,
                threat.severity,
                severity_emoji,
                threat.confidence,
                threat.status,
                timestamp
            )
        }
    }

    /// 格式化紧急告警消息
    fn format_emergency_alert(&self, threats: &[ThreatInfo]) -> String {
        let critical_count = threats.iter()
            .filter(|t| t.severity == "critical" || t.severity == "high")
            .count();

        let timestamp = if self.config.message_format.include_timestamp {
            format!("\n🕐 告警时间: {}", Utc::now().to_rfc3339())
        } else {
            String::new()
        };

        if self.config.message_format.use_markdown {
            format!(
                r#"# 🚨🚨 紧急安全告警 🚨🚨

## ⚠️ 威胁概况
- **严重威胁数量**: {} 个
- **总威胁数量**: {} 个
- **受影响系统**: 1 个
- **响应状态**: 🔄 自动响应已启动

## 🔥 威胁列表
{}

## ⚡ 已执行措施
• ✅ 自动隔离可疑文件
• ✅ 阻断恶意网络连接
• ✅ 启动深度系统扫描

## 🎯 立即行动
• **立即检查所有受影响系统**
• **验证自动响应措施的有效性**
• **通知相关技术团队**
• **准备详细的事件报告**

## 🚨 紧急联系
📞 安全热线: +1-800-SECURITY
📧 安全团队: security@company.com

## 🔗 紧急响应
[进入应急中心](http://localhost:8080#emergency)
{}
"#,
                critical_count,
                threats.len(),
                threats.iter()
                    .take(5)
                    .map(|t| format!("• **{}**: {} (置信度: {:.1}%)", t.threat_type, t.file_path, t.confidence))
                    .collect::<Vec<_>>()
                    .join("\n"),
                timestamp
            )
        } else {
            format!(
                "🚨🚨 紧急安全告警 🚨🚨\n\n⚠️ 威胁概况:\n• 严重威胁数量: {} 个\n• 总威胁数量: {} 个\n• 受影响系统: 1 个\n• 响应状态: 🔄 自动响应已启动\n\n🔥 威胁列表:\n{}\n\n⚡ 已执行措施:\n• ✅ 自动隔离可疑文件\n• ✅ 阻断恶意网络连接\n• ✅ 启动深度系统扫描\n\n🎯 立即行动:\n• 立即检查所有受影响系统\n• 验证自动响应措施的有效性\n• 通知相关技术团队\n• 准备详细的事件报告\n\n🚨 紧急联系:\n📞 安全热线: +1-800-SECURITY\n📧 安全团队: security@company.com\n\n🔗 紧急响应: http://localhost:8080#emergency{}",
                critical_count,
                threats.len(),
                threats.iter()
                    .take(5)
                    .map(|t| format!("• {}: {} (置信度: {:.1}%)", t.threat_type, t.file_path, t.confidence))
                    .collect::<Vec<_>>()
                    .join("\n"),
                timestamp
            )
        }
    }

    /// 格式化测试消息
    fn format_test_message(&self) -> String {
        let timestamp = if self.config.message_format.include_timestamp {
            format!("\n🕐 测试时间: {}", Utc::now().to_rfc3339())
        } else {
            String::new()
        };

        if self.config.message_format.use_markdown {
            format!(
                r#"# 🧪 Matrix服务测试

## ✅ 连接状态
Matrix服务配置正确，消息发送功能正常！

## 📋 配置信息
- **服务器**: {}
- **用户**: {}
- **设备**: {}

## 🤖 AI安全助手
Matrix集成已准备就绪，可以正常发送安全报告和告警。
{}
"#,
                self.config.homeserver,
                self.config.username,
                self.config.device_name,
                timestamp
            )
        } else {
            format!(
                "🧪 Matrix服务测试\n\n✅ 连接状态:\nMatrix服务配置正确，消息发送功能正常！\n\n📋 配置信息:\n• 服务器: {}\n• 用户: {}\n• 设备: {}\n\n🤖 AI安全助手:\nMatrix集成已准备就绪，可以正常发送安全报告和告警。{}",
                self.config.homeserver,
                self.config.username,
                self.config.device_name,
                timestamp
            )
        }
    }

    /// 验证Matrix配置
    pub fn validate_config(&self) -> Result<()> {
        if self.config.homeserver.is_empty() {
            return Err(anyhow!("Matrix服务器地址不能为空"));
        }

        if self.config.username.is_empty() {
            return Err(anyhow!("Matrix用户名不能为空"));
        }

        if self.config.password.is_empty() {
            return Err(anyhow!("Matrix密码不能为空"));
        }

        if self.config.rooms.default_room.is_empty() {
            return Err(anyhow!("至少需要配置一个默认房间"));
        }

        // 验证房间ID格式
        for room_id in [
            &self.config.rooms.default_room,
            &self.config.rooms.emergency_room,
            &self.config.rooms.reports_room,
            &self.config.rooms.admin_room,
        ] {
            if !room_id.is_empty() && !room_id.starts_with('!') {
                return Err(anyhow!("无效的房间ID格式: {}", room_id));
            }
        }

        Ok(())
    }

    /// 获取房间列表
    pub async fn get_joined_rooms(&self) -> Result<Vec<String>> {
        let client = self.client.as_ref()
            .ok_or_else(|| anyhow!("Matrix客户端未初始化"))?;

        let rooms = client.joined_rooms();
        let room_ids: Vec<String> = rooms.iter()
            .map(|room| room.room_id().to_string())
            .collect();

        Ok(room_ids)
    }
}

impl Default for MatrixConfig {
    fn default() -> Self {
        MatrixConfig {
            enabled: false,
            homeserver: "https://matrix.org".to_string(),
            username: String::new(),
            password: String::new(),
            device_name: "AI-Security-Bot".to_string(),
            rooms: RoomConfig {
                default_room: String::new(),
                emergency_room: String::new(),
                reports_room: String::new(),
                admin_room: String::new(),
            },
            message_format: MessageFormat {
                use_markdown: true,
                use_html: false,
                include_timestamp: true,
                include_severity_emoji: true,
            },
            retry: RetryConfig {
                max_attempts: 3,
                delay_seconds: 5,
            },
        }
    }
}
