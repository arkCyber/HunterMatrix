#!/usr/bin/env python3
"""
AISecurityReport邮件Service
支持多种邮件Service提供商和丰富的邮件Template
"""

import smtplib
import ssl
import logging
import mimetypes
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml
import jinja2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """邮件ServiceClass"""

    def __init__(self, config_path: str = "email_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()

        # 邮件Service提供商Configuration
        self.providers = {
            'gmail': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            'outlook': {
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            'yahoo': {
                'smtp_server': 'smtp.mail.yahoo.com',
                'smtp_port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            'qq': {
                'smtp_server': 'smtp.qq.com',
                'smtp_port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            '163': {
                'smtp_server': 'smtp.163.com',
                'smtp_port': 25,
                'use_tls': True,
                'use_ssl': False
            },
            'custom': {
                'smtp_server': self.config.get('smtp', {}).get('server', 'localhost'),
                'smtp_port': self.config.get('smtp', {}).get('port', 587),
                'use_tls': self.config.get('smtp', {}).get('use_tls', True),
                'use_ssl': self.config.get('smtp', {}).get('use_ssl', False)
            }
        }

        # InitializeTemplate引擎
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('email_templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

        # CreateTemplateDirectory
        Path('email_templates').mkdir(exist_ok=True)
        self.create_default_templates()

    def load_config(self) -> Dict[str, Any]:
        """Load邮件Configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"邮件ConfigurationFile {self.config_path} 不存在，使用DefaultConfiguration")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """获取Default邮件Configuration"""
        return {
            'enabled': True,
            'provider': 'gmail',
            'smtp': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            'auth': {
                'username': '',
                'password': '',
                'use_oauth': False
            },
            'sender': {
                'name': 'AISecurity助手',
                'email': 'security@company.com'
            },
            'recipients': {
                'default': ['admin@company.com'],
                'emergency': ['emergency@company.com', 'ciso@company.com'],
                'reports': ['security-team@company.com']
            },
            'templates': {
                'daily_report': 'daily_report.html',
                'weekly_report': 'weekly_report.html',
                'threat_alert': 'threat_alert.html',
                'emergency_alert': 'emergency_alert.html'
            },
            'attachments': {
                'max_size_mb': 25,
                'allowed_types': ['.pdf', '.html', '.txt', '.json', '.csv'],
                'compress_large_files': True
            },
            'retry': {
                'max_attempts': 3,
                'delay_seconds': 5
            }
        }

    def create_default_templates(self):
        """CreateDefault邮件Template"""
        templates = {
            'daily_report.html': self.get_daily_report_template(),
            'weekly_report.html': self.get_weekly_report_template(),
            'threat_alert.html': self.get_threat_alert_template(),
            'emergency_alert.html': self.get_emergency_alert_template(),
            'base.html': self.get_base_template()
        }

        for template_name, content in templates.items():
            template_path = Path('email_templates') / template_name
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def get_base_template(self) -> str:
        """基础邮件Template"""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
            font-size: 28px;
        }
        .header .subtitle {
            color: #666;
            margin-top: 5px;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .alert-success { background: #d4edda; border-left: 4px solid #28a745; }
        .alert-warning { background: #fff3cd; border-left: 4px solid #ffc107; }
        .alert-danger { background: #f8d7da; border-left: 4px solid #dc3545; }
        .alert-info { background: #d1ecf1; border-left: 4px solid #17a2b8; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 {{ title }}</h1>
            <div class="subtitle">{{ subtitle }}</div>
        </div>

        {% block content %}{% endblock %}

        <div class="footer">
            <p>此邮件由AISecurity助手Automatic生成 | {{ timestamp }}</p>
            <p>如Has问题，请联系SecurityTeam</p>
        </div>
    </div>
</body>
</html>'''

    def get_daily_report_template(self) -> str:
        """每日ReportTemplate"""
        return '''{% extends "base.html" %}

{% block content %}
<div class="alert alert-info">
    <strong>📊 每日SecurityReport摘要</strong><br>
    今日SystemSecurity状况总体{{ '良好' if threat_level == 'low' else '需要关注' }}，
    共Detection到 {{ total_threats }} 个威胁，AlreadyProcess {{ handled_threats }} 个。
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">{{ scanned_files }}</div>
        <div class="stat-label">扫描File数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ total_threats }}</div>
        <div class="stat-label">Detection威胁</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ scan_time }}s</div>
        <div class="stat-label">平均扫描Time</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ success_rate }}%</div>
        <div class="stat-label">DetectionSuccess率</div>
    </div>
</div>

{% if threats %}
<h3>🚨 今日威胁Detection</h3>
<table>
    <thead>
        <tr>
            <th>威胁Type</th>
            <th>FilePath</th>
            <th>严重程度</th>
            <th>ProcessStatus</th>
        </tr>
    </thead>
    <tbody>
        {% for threat in threats %}
        <tr>
            <td>{{ threat.type }}</td>
            <td>{{ threat.file_path }}</td>
            <td>
                {% if threat.severity == 'high' %}
                    <span style="color: #dc3545;">🔴 高危</span>
                {% elif threat.severity == 'medium' %}
                    <span style="color: #ffc107;">🟡 中危</span>
                {% else %}
                    <span style="color: #28a745;">🟢 低危</span>
                {% endif %}
            </td>
            <td>{{ threat.status }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}

<h3>🧠 AIAnalysis洞察</h3>
<ul>
    {% for insight in ai_insights %}
    <li>{{ insight }}</li>
    {% endfor %}
</ul>

<h3>💡 Security建议</h3>
<ul>
    {% for recommendation in recommendations %}
    <li>{{ recommendation }}</li>
    {% endfor %}
</ul>

<div style="text-align: center; margin-top: 30px;">
    <a href="{{ dashboard_url }}" class="btn">查看详细Report</a>
    <a href="{{ settings_url }}" class="btn" style="background: #6c757d;">SystemSettings</a>
</div>
{% endblock %}'''

    def get_weekly_report_template(self) -> str:
        """周报Template"""
        return '''{% extends "base.html" %}

{% block content %}
<div class="alert alert-info">
    <strong>📅 本周Security状况总结</strong><br>
    本周共进行了 {{ total_scans }} 次扫描，Detection到 {{ total_threats }} 个威胁，
    相比上周威胁活动{{ '上升' if trend == 'up' else '下降' }} {{ trend_percentage }}%。
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">{{ total_scans }}</div>
        <div class="stat-label">总扫描次数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ total_files }}</div>
        <div class="stat-label">扫描FileTotal</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ total_threats }}</div>
        <div class="stat-label">Detection威胁Total</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ avg_response_time }}s</div>
        <div class="stat-label">平均ResponseTime</div>
    </div>
</div>

<h3>📈 威胁趋势Analysis</h3>
<table>
    <thead>
        <tr>
            <th>威胁Type</th>
            <th>本周Detection</th>
            <th>上周Detection</th>
            <th>变化趋势</th>
        </tr>
    </thead>
    <tbody>
        {% for trend in threat_trends %}
        <tr>
            <td>{{ trend.type }}</td>
            <td>{{ trend.current_week }}</td>
            <td>{{ trend.last_week }}</td>
            <td>
                {% if trend.change > 0 %}
                    <span style="color: #dc3545;">↗ +{{ trend.change }}%</span>
                {% elif trend.change < 0 %}
                    <span style="color: #28a745;">↘ {{ trend.change }}%</span>
                {% else %}
                    <span style="color: #6c757d;">→ No变化</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<h3>🎯 本周重点事件</h3>
{% for event in key_events %}
<div class="alert alert-{{ event.level }}">
    <strong>{{ event.title }}</strong><br>
    {{ event.description }}
</div>
{% endfor %}

<h3>📊 SystemPerformanceMetric</h3>
<ul>
    <li>平均CPU使用率: {{ avg_cpu }}%</li>
    <li>平均Memory使用率: {{ avg_memory }}%</li>
    <li>System可用性: {{ uptime }}%</li>
    <li>误报率: {{ false_positive_rate }}%</li>
</ul>
{% endblock %}'''

    def get_threat_alert_template(self) -> str:
        """威胁告警Template"""
        return '''{% extends "base.html" %}

{% block content %}
<div class="alert alert-danger">
    <strong>🚨 威胁告警</strong><br>
    Detection到 {{ threat_level }} Level威胁，需要立即关注和Process。
</div>

<h3>威胁详情</h3>
<table>
    <tr>
        <th>威胁Type</th>
        <td>{{ threat_type }}</td>
    </tr>
    <tr>
        <th>严重程度</th>
        <td>
            {% if severity == 'critical' %}
                <span style="color: #dc3545;">🔴 严重</span>
            {% elif severity == 'high' %}
                <span style="color: #fd7e14;">🟠 高危</span>
            {% elif severity == 'medium' %}
                <span style="color: #ffc107;">🟡 中危</span>
            {% else %}
                <span style="color: #28a745;">🟢 低危</span>
            {% endif %}
        </td>
    </tr>
    <tr>
        <th>DetectionTime</th>
        <td>{{ detection_time }}</td>
    </tr>
    <tr>
        <th>FilePath</th>
        <td><code>{{ file_path }}</code></td>
    </tr>
    <tr>
        <th>AI置信度</th>
        <td>{{ confidence }}%</td>
    </tr>
    <tr>
        <th>ProcessStatus</th>
        <td>{{ status }}</td>
    </tr>
</table>

<h3>🔍 威胁Analysis</h3>
<p>{{ threat_description }}</p>

<h3>⚡ 建议措施</h3>
<ol>
    {% for action in recommended_actions %}
    <li>{{ action }}</li>
    {% endfor %}
</ol>

{% if iocs %}
<h3>🎯 威胁Metric (IOCs)</h3>
<ul>
    {% for ioc in iocs %}
    <li><code>{{ ioc }}</code></li>
    {% endfor %}
</ul>
{% endif %}

<div style="text-align: center; margin-top: 30px;">
    <a href="{{ incident_url }}" class="btn" style="background: #dc3545;">查看事件详情</a>
    <a href="{{ response_url }}" class="btn">StartResponse流程</a>
</div>
{% endblock %}'''

    def get_emergency_alert_template(self) -> str:
        """紧急告警Template"""
        return '''{% extends "base.html" %}

{% block content %}
<div class="alert alert-danger" style="border: 3px solid #dc3545; animation: blink 1s infinite;">
    <strong>🚨🚨 紧急Security告警 🚨🚨</strong><br>
    Detection到严重Security威胁，需要立即采取行动！
</div>

<style>
@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0.7; }
}
</style>

<div class="alert alert-warning">
    <strong>⚠️ AutomaticResponseAlreadyStart</strong><br>
    SystemAlreadyAutomaticExecute初步Response措施，请立即确认并采取进一步行动。
</div>

<h3>🔥 紧急威胁概况</h3>
<div class="stats-grid">
    <div class="stat-card" style="background: #f8d7da;">
        <div class="stat-number" style="color: #dc3545;">{{ critical_threats }}</div>
        <div class="stat-label">严重威胁</div>
    </div>
    <div class="stat-card" style="background: #fff3cd;">
        <div class="stat-number" style="color: #856404;">{{ affected_systems }}</div>
        <div class="stat-label">受影响System</div>
    </div>
    <div class="stat-card" style="background: #d1ecf1;">
        <div class="stat-number" style="color: #0c5460;">{{ response_time }}min</div>
        <div class="stat-label">ResponseTime</div>
    </div>
    <div class="stat-card" style="background: #d4edda;">
        <div class="stat-number" style="color: #155724;">{{ actions_taken }}</div>
        <div class="stat-label">AlreadyExecute措施</div>
    </div>
</div>

<h3>🚨 威胁详情</h3>
{% for threat in threats %}
<div class="alert alert-danger">
    <strong>{{ threat.type }}</strong> - {{ threat.description }}<br>
    <small>File: <code>{{ threat.file_path }}</code> | 置信度: {{ threat.confidence }}%</small>
</div>
{% endfor %}

<h3>⚡ AlreadyExecute的AutomaticResponse</h3>
<ul>
    {% for action in auto_actions %}
    <li>✅ {{ action }}</li>
    {% endfor %}
</ul>

<h3>🎯 立即行动清单</h3>
<ol>
    {% for action in immediate_actions %}
    <li><strong>{{ action }}</strong></li>
    {% endfor %}
</ol>

<div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8d7da; border-radius: 5px;">
    <h4 style="color: #721c24; margin-top: 0;">🚨 紧急联系Information</h4>
    <p>SecurityTeam: {{ emergency_contact }}</p>
    <p>事件Response热线: {{ emergency_phone }}</p>

    <a href="{{ emergency_dashboard }}" class="btn" style="background: #dc3545; font-size: 18px; padding: 15px 30px;">
        🚨 进入紧急Response中心
    </a>
</div>
{% endblock %}'''

    async def send_email(self,
                        subject: str,
                        template_name: str,
                        template_data: Dict[str, Any],
                        recipients: Optional[List[str]] = None,
                        attachments: Optional[List[Union[str, Path]]] = None,
                        priority: str = 'normal') -> bool:
        """Send邮件"""

        if not self.config.get('enabled', False):
            logger.info("邮件Send功能Already禁用")
            return False

        try:
            # 准备收件人
            if recipients is None:
                recipients = self.config['recipients']['default']

            # 渲染邮件Content
            html_content = self.render_template(template_name, template_data)

            # Create邮件消息
            msg = self.create_message(subject, html_content, recipients, priority)

            # 添加附件
            if attachments:
                self.add_attachments(msg, attachments)

            # Send邮件
            success = await self.send_message(msg, recipients)

            if success:
                logger.info(f"邮件SendSuccess: {subject} -> {', '.join(recipients)}")
            else:
                logger.error(f"邮件SendFailed: {subject}")

            return success

        except Exception as e:
            logger.error(f"邮件SendException: {e}")
            return False

    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """渲染邮件Template"""
        try:
            # 添加通用Data
            data.update({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'dashboard_url': 'http://localhost:8080',
                'settings_url': 'http://localhost:8080#settings'
            })

            template = self.template_env.get_template(template_name)
            return template.render(**data)

        except Exception as e:
            logger.error(f"Template渲染Failed: {e}")
            # 返回简单的HTMLContent
            return f"""
            <html>
            <body>
                <h2>{data.get('title', 'SecurityReport')}</h2>
                <p>Template渲染Failed，请CheckTemplateFile。</p>
                <p>ErrorInformation: {str(e)}</p>
            </body>
            </html>
            """

    def create_message(self, subject: str, html_content: str,
                      recipients: List[str], priority: str = 'normal') -> MIMEMultipart:
        """Create邮件消息"""
        msg = MIMEMultipart('alternative')

        # Settings邮件头
        msg['Subject'] = subject
        msg['From'] = f"{self.config['sender']['name']} <{self.config['sender']['email']}>"
        msg['To'] = ', '.join(recipients)

        # Settings优先级
        if priority == 'high':
            msg['X-Priority'] = '1'
            msg['X-MSMail-Priority'] = 'High'
        elif priority == 'low':
            msg['X-Priority'] = '5'
            msg['X-MSMail-Priority'] = 'Low'

        # 添加HTMLContent
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # 生成纯TextVersion
        text_content = self.html_to_text(html_content)
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)

        return msg

    def html_to_text(self, html_content: str) -> str:
        """将HTML转换为纯Text"""
        try:
            # 简单的HTML到Text转换
            import re

            # 移除HTMLTag
            text = re.sub(r'<[^>]+>', '', html_content)

            # Process特殊Character
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&amp;', '&')

            # Clean多余的Null白
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)

            return text.strip()

        except Exception as e:
            logger.warning(f"HTML转TextFailed: {e}")
            return "邮件Content转换Failed，请查看HTMLVersion。"

    def add_attachments(self, msg: MIMEMultipart, attachments: List[Union[str, Path]]):
        """添加邮件附件"""
        max_size = self.config['attachments']['max_size_mb'] * 1024 * 1024
        allowed_types = self.config['attachments']['allowed_types']

        for attachment_path in attachments:
            try:
                file_path = Path(attachment_path)

                if not file_path.exists():
                    logger.warning(f"附件File不存在: {file_path}")
                    continue

                # CheckFileSize
                file_size = file_path.stat().st_size
                if file_size > max_size:
                    logger.warning(f"附件File过大: {file_path} ({file_size} bytes)")
                    continue

                # CheckFileType
                if file_path.suffix.lower() not in allowed_types:
                    logger.warning(f"不支持的附件Type: {file_path.suffix}")
                    continue

                # ReadFileContent
                with open(file_path, 'rb') as f:
                    attachment_data = f.read()

                # Create附件
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(attachment_data)
                encoders.encode_base64(attachment)

                # Settings附件头
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file_path.name}'
                )

                msg.attach(attachment)
                logger.info(f"Already添加附件: {file_path.name}")

            except Exception as e:
                logger.error(f"添加附件Failed {attachment_path}: {e}")

    async def send_message(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """Send邮件消息"""
        provider_config = self.providers.get(self.config['provider'], self.providers['custom'])

        max_attempts = self.config['retry']['max_attempts']
        delay = self.config['retry']['delay_seconds']

        for attempt in range(max_attempts):
            try:
                # CreateSMTPConnection
                if provider_config['use_ssl']:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(
                        provider_config['smtp_server'],
                        provider_config['smtp_port'],
                        context=context
                    )
                else:
                    server = smtplib.SMTP(
                        provider_config['smtp_server'],
                        provider_config['smtp_port']
                    )

                    if provider_config['use_tls']:
                        server.starttls()

                # 登录
                if self.config['auth']['username'] and self.config['auth']['password']:
                    server.login(
                        self.config['auth']['username'],
                        self.config['auth']['password']
                    )

                # Send邮件
                server.send_message(msg, to_addrs=recipients)
                server.quit()

                return True

            except Exception as e:
                logger.warning(f"邮件Send尝试 {attempt + 1} Failed: {e}")

                if attempt < max_attempts - 1:
                    await asyncio.sleep(delay)
                    delay *= 2  # 指数退避

        return False

    # 便捷的邮件SendMethod
    async def send_daily_report(self, report_data: Dict[str, Any],
                               report_file: Optional[str] = None) -> bool:
        """Send每日Report"""
        template_data = {
            'title': '每日SecurityReport',
            'subtitle': f'{datetime.now().strftime("%Y年%m月%d日")} Security状况Report',
            'scanned_files': report_data.get('scanned_files', 0),
            'total_threats': report_data.get('total_threats', 0),
            'handled_threats': report_data.get('handled_threats', 0),
            'scan_time': report_data.get('avg_scan_time', 0),
            'success_rate': report_data.get('success_rate', 100),
            'threat_level': report_data.get('threat_level', 'low'),
            'threats': report_data.get('threats', []),
            'ai_insights': report_data.get('ai_insights', []),
            'recommendations': report_data.get('recommendations', [])
        }

        attachments = [report_file] if report_file else None

        return await self.send_email(
            subject=f"📊 每日SecurityReport - {datetime.now().strftime('%Y-%m-%d')}",
            template_name='daily_report.html',
            template_data=template_data,
            recipients=self.config['recipients']['reports'],
            attachments=attachments
        )

    async def send_weekly_report(self, report_data: Dict[str, Any],
                                report_file: Optional[str] = None) -> bool:
        """Send周度Report"""
        template_data = {
            'title': '周度SecurityReport',
            'subtitle': f'{datetime.now().strftime("%Y年第%U周")} Security状况总结',
            'total_scans': report_data.get('total_scans', 0),
            'total_files': report_data.get('total_files', 0),
            'total_threats': report_data.get('total_threats', 0),
            'avg_response_time': report_data.get('avg_response_time', 0),
            'trend': report_data.get('trend', 'stable'),
            'trend_percentage': report_data.get('trend_percentage', 0),
            'threat_trends': report_data.get('threat_trends', []),
            'key_events': report_data.get('key_events', []),
            'avg_cpu': report_data.get('avg_cpu', 0),
            'avg_memory': report_data.get('avg_memory', 0),
            'uptime': report_data.get('uptime', 100),
            'false_positive_rate': report_data.get('false_positive_rate', 0)
        }

        attachments = [report_file] if report_file else None

        return await self.send_email(
            subject=f"📅 周度SecurityReport - {datetime.now().strftime('%Y年第%U周')}",
            template_name='weekly_report.html',
            template_data=template_data,
            recipients=self.config['recipients']['reports'],
            attachments=attachments
        )

    async def send_threat_alert(self, threat_data: Dict[str, Any]) -> bool:
        """Send威胁告警"""
        template_data = {
            'title': '威胁告警',
            'subtitle': 'Detection到Security威胁，需要关注',
            'threat_type': threat_data.get('type', 'Unknown'),
            'threat_level': threat_data.get('level', 'medium'),
            'severity': threat_data.get('severity', 'medium'),
            'detection_time': threat_data.get('detection_time', datetime.now().isoformat()),
            'file_path': threat_data.get('file_path', 'N/A'),
            'confidence': threat_data.get('confidence', 0),
            'status': threat_data.get('status', 'detected'),
            'threat_description': threat_data.get('description', ''),
            'recommended_actions': threat_data.get('recommended_actions', []),
            'iocs': threat_data.get('iocs', []),
            'incident_url': f"http://localhost:8080#incident/{threat_data.get('id', '')}",
            'response_url': f"http://localhost:8080#response/{threat_data.get('id', '')}"
        }

        # 根据威胁等级选择收件人
        if threat_data.get('severity') in ['critical', 'high']:
            recipients = self.config['recipients']['emergency']
            priority = 'high'
        else:
            recipients = self.config['recipients']['default']
            priority = 'normal'

        return await self.send_email(
            subject=f"🚨 威胁告警 - {threat_data.get('type', 'Unknown')} ({threat_data.get('severity', 'medium')})",
            template_name='threat_alert.html',
            template_data=template_data,
            recipients=recipients,
            priority=priority
        )

    async def send_emergency_alert(self, emergency_data: Dict[str, Any]) -> bool:
        """Send紧急告警"""
        template_data = {
            'title': '紧急Security告警',
            'subtitle': 'Detection到严重Security威胁，需要立即行动',
            'critical_threats': emergency_data.get('critical_threats', 0),
            'affected_systems': emergency_data.get('affected_systems', 0),
            'response_time': emergency_data.get('response_time', 0),
            'actions_taken': emergency_data.get('actions_taken', 0),
            'threats': emergency_data.get('threats', []),
            'auto_actions': emergency_data.get('auto_actions', []),
            'immediate_actions': emergency_data.get('immediate_actions', []),
            'emergency_contact': self.config.get('emergency_contact', 'security@company.com'),
            'emergency_phone': self.config.get('emergency_phone', '+1-800-SECURITY'),
            'emergency_dashboard': 'http://localhost:8080#emergency'
        }

        return await self.send_email(
            subject=f"🚨🚨 紧急Security告警 - {emergency_data.get('critical_threats', 0)}个严重威胁",
            template_name='emergency_alert.html',
            template_data=template_data,
            recipients=self.config['recipients']['emergency'],
            priority='high'
        )

    async def send_custom_report(self, subject: str, content: str,
                                recipients: Optional[List[str]] = None,
                                attachments: Optional[List[str]] = None) -> bool:
        """SendCustomReport"""
        template_data = {
            'title': subject,
            'subtitle': 'CustomSecurityReport',
            'content': content
        }

        # Create简单的CustomTemplate
        custom_template = '''{% extends "base.html" %}
{% block content %}
<div class="alert alert-info">
    {{ content | safe }}
</div>
{% endblock %}'''

        # Save临时Template
        temp_template_path = Path('email_templates') / 'custom_temp.html'
        with open(temp_template_path, 'w', encoding='utf-8') as f:
            f.write(custom_template)

        try:
            result = await self.send_email(
                subject=subject,
                template_name='custom_temp.html',
                template_data=template_data,
                recipients=recipients,
                attachments=attachments
            )
        finally:
            # Clean临时Template
            if temp_template_path.exists():
                temp_template_path.unlink()

        return result

    def test_email_config(self) -> Dict[str, Any]:
        """Test邮件Configuration"""
        result = {
            'config_valid': True,
            'errors': [],
            'warnings': []
        }

        # Check基本Configuration
        if not self.config.get('enabled'):
            result['warnings'].append('邮件Send功能Already禁用')

        if not self.config.get('auth', {}).get('username'):
            result['errors'].append('缺少邮箱User名')
            result['config_valid'] = False

        if not self.config.get('auth', {}).get('password'):
            result['errors'].append('缺少邮箱Password')
            result['config_valid'] = False

        if not self.config.get('sender', {}).get('email'):
            result['errors'].append('缺少发件人邮箱')
            result['config_valid'] = False

        if not self.config.get('recipients', {}).get('default'):
            result['errors'].append('缺少Default收件人')
            result['config_valid'] = False

        # CheckSMTPConfiguration
        provider = self.config.get('provider', 'custom')
        if provider not in self.providers:
            result['warnings'].append(f'Not知的邮件Service提供商: {provider}')

        return result

    async def send_test_email(self, recipient: str) -> bool:
        """SendTest邮件"""
        template_data = {
            'title': '邮件ConfigurationTest',
            'subtitle': 'AISecurity助手邮件ServiceTest',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config_info': {
                'provider': self.config.get('provider', 'unknown'),
                'sender': self.config.get('sender', {}).get('email', 'unknown')
            }
        }

        # CreateTest邮件Template
        test_template = '''{% extends "base.html" %}
{% block content %}
<div class="alert alert-success">
    <strong>✅ 邮件ConfigurationTestSuccess！</strong><br>
    如果您收到这封邮件，说明邮件ServiceConfiguration正确。
</div>

<h3>📋 ConfigurationInformation</h3>
<ul>
    <li>邮件Service商: {{ config_info.provider }}</li>
    <li>发件人: {{ config_info.sender }}</li>
    <li>TestTime: {{ test_time }}</li>
</ul>

<div class="alert alert-info">
    <strong>🤖 AISecurity助手</strong><br>
    邮件ServiceAlready准备就绪，可以正常SendSecurityReport和告警。
</div>
{% endblock %}'''

        # SaveTestTemplate
        test_template_path = Path('email_templates') / 'test_email.html'
        with open(test_template_path, 'w', encoding='utf-8') as f:
            f.write(test_template)

        try:
            result = await self.send_email(
                subject="🧪 AISecurity助手邮件ConfigurationTest",
                template_name='test_email.html',
                template_data=template_data,
                recipients=[recipient]
            )
        finally:
            # CleanTestTemplate
            if test_template_path.exists():
                test_template_path.unlink()

        return result

# Async上下文管理器
import asyncio

async def main():
    """Test邮件Service"""
    email_service = EmailService()

    # TestConfiguration
    config_test = email_service.test_email_config()
    print("📧 邮件ConfigurationTest:")
    print(f"   ConfigurationHas效: {config_test['config_valid']}")
    if config_test['errors']:
        print(f"   Error: {config_test['errors']}")
    if config_test['warnings']:
        print(f"   警告: {config_test['warnings']}")

    # 如果ConfigurationHas效，SendTest邮件
    if config_test['config_valid']:
        test_recipient = input("请InputTest邮箱地址: ").strip()
        if test_recipient:
            print("📤 SendTest邮件...")
            success = await email_service.send_test_email(test_recipient)
            print(f"   Result: {'Success' if success else 'Failed'}")

if __name__ == "__main__":
    asyncio.run(main())