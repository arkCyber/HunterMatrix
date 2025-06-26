#!/usr/bin/env python3
"""
AISecurityReport生成器
支持定时Automatic生成和Command触发生成SecurityReport
"""

import asyncio
import json
import logging
import smtplib
import schedule
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# AIModule
from intelligent_threat_detector import IntelligentThreatDetector
from nlp_security_analyzer import SecurityLogAnalyzer, SecurityReportGenerator
from ai_response_system import AIResponseSystem
from email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIReportGenerator:
    """AISecurityReport生成器"""
    
    def __init__(self, config_path: str = "report_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # AIGroup件
        self.threat_detector = IntelligentThreatDetector()
        self.log_analyzer = SecurityLogAnalyzer()
        self.report_generator = SecurityReportGenerator()
        self.response_system = AIResponseSystem()

        # 邮件Service
        self.email_service = EmailService('email_config.yaml')
        
        # ReportData
        self.daily_stats = {
            'scanned_files': 0,
            'threats_detected': 0,
            'threats_blocked': 0,
            'false_positives': 0,
            'scan_time': 0,
            'last_update': datetime.now()
        }
        
        # 威胁DataLibrary
        self.threat_database = []
        self.network_events = []
        
        # ReportTemplate
        self.report_templates = {
            'daily': self.generate_daily_report,
            'weekly': self.generate_weekly_report,
            'threat_summary': self.generate_threat_summary,
            'network_security': self.generate_network_report,
            'ai_analysis': self.generate_ai_analysis_report
        }
    
    def load_config(self) -> Dict[str, Any]:
        """LoadConfigurationFile"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"ConfigurationFile {self.config_path} 不存在，使用DefaultConfiguration")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取DefaultConfiguration"""
        return {
            'schedule': {
                'daily_report_time': '08:00',
                'weekly_report_day': 'monday',
                'weekly_report_time': '09:00',
                'timezone': 'Asia/Shanghai'
            },
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_address': 'security@company.com',
                'to_addresses': ['admin@company.com'],
                'subject_prefix': '[AISecurityReport]'
            },
            'report': {
                'output_dir': 'reports',
                'formats': ['html', 'json', 'txt'],
                'include_charts': True,
                'include_recommendations': True,
                'threat_threshold': 0.7,
                'max_report_age_days': 30
            },
            'ai': {
                'enabled': True,
                'analysis_depth': 'detailed',
                'include_predictions': True,
                'confidence_threshold': 0.8
            }
        }
    
    async def collect_security_data(self) -> Dict[str, Any]:
        """收集SecurityData"""
        logger.info("Start收集SecurityData...")
        
        # 模拟收集各种SecurityData
        security_data = {
            'timestamp': datetime.now().isoformat(),
            'scan_statistics': await self.get_scan_statistics(),
            'threat_detections': await self.get_threat_detections(),
            'network_events': await self.get_network_events(),
            'system_health': await self.get_system_health(),
            'ai_insights': await self.get_ai_insights()
        }
        
        return security_data
    
    async def get_scan_statistics(self) -> Dict[str, Any]:
        """获取扫描StatisticsData"""
        # 模拟扫描StatisticsData
        return {
            'total_scans': 156,
            'files_scanned': 45230,
            'threats_found': 8,
            'clean_files': 45222,
            'scan_time_avg': 2.3,
            'scan_time_total': 358.8,
            'last_scan': (datetime.now() - timedelta(minutes=15)).isoformat()
        }
    
    async def get_threat_detections(self) -> List[Dict[str, Any]]:
        """获取威胁DetectionData"""
        # 模拟威胁DetectionData
        threats = [
            {
                'id': 'threat_001',
                'type': 'trojan',
                'severity': 'high',
                'file_path': '/tmp/suspicious.exe',
                'detection_time': (datetime.now() - timedelta(hours=2)).isoformat(),
                'ai_confidence': 0.94,
                'status': 'quarantined',
                'description': 'AIDetection到高危木马Program'
            },
            {
                'id': 'threat_002',
                'type': 'adware',
                'severity': 'medium',
                'file_path': '/Users/test/Downloads/installer.dmg',
                'detection_time': (datetime.now() - timedelta(hours=5)).isoformat(),
                'ai_confidence': 0.87,
                'status': 'blocked',
                'description': 'Detection到广告SoftwareInstallPackage'
            },
            {
                'id': 'threat_003',
                'type': 'suspicious_script',
                'severity': 'low',
                'file_path': '/tmp/script.sh',
                'detection_time': (datetime.now() - timedelta(hours=8)).isoformat(),
                'ai_confidence': 0.73,
                'status': 'monitored',
                'description': '可疑ScriptFile，ProcessingMonitor'
            }
        ]
        return threats
    
    async def get_network_events(self) -> List[Dict[str, Any]]:
        """获取NetworkSecurity事件"""
        # 模拟NetworkSecurity事件
        events = [
            {
                'id': 'net_001',
                'type': 'suspicious_connection',
                'source_ip': '192.168.1.100',
                'destination_ip': '185.220.101.42',
                'port': 443,
                'protocol': 'HTTPS',
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'risk_level': 'medium',
                'description': 'Detection到可疑外部Connection'
            },
            {
                'id': 'net_002',
                'type': 'failed_login',
                'source_ip': '10.0.0.50',
                'attempts': 15,
                'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
                'risk_level': 'high',
                'description': 'Detection到暴力破解尝试'
            }
        ]
        return events
    
    async def get_system_health(self) -> Dict[str, Any]:
        """获取System健康Status"""
        return {
            'cpu_usage': 25.6,
            'memory_usage': 68.2,
            'disk_usage': 45.8,
            'network_traffic': 'normal',
            'services_status': {
                'huntermatrix': 'running',
                'ai_service': 'running',
                'web_ui': 'running'
            },
            'last_update': datetime.now().isoformat()
        }
    
    async def get_ai_insights(self) -> Dict[str, Any]:
        """获取AIAnalysis洞察"""
        return {
            'threat_trend': 'decreasing',
            'risk_score': 3.2,
            'confidence': 0.89,
            'predictions': [
                'Not来24小时威胁活动可能保持低水平',
                '建议Continue保持当前防护Policy',
                '注意MonitorNetworkExceptionConnection'
            ],
            'recommendations': [
                'Update病毒Library到最新Version',
                '加强Network访问控制',
                '定期Backup重要Data'
            ]
        }
    
    async def generate_daily_report(self, data: Dict[str, Any]) -> str:
        """生成每日SecurityReport"""
        scan_stats = data['scan_statistics']
        threats = data['threat_detections']
        network_events = data['network_events']
        ai_insights = data['ai_insights']
        
        report = f"""
# 🛡️ 每日SecurityReport - {datetime.now().strftime('%Y年%m月%d日')}

## 📊 扫描Statistics

- **总扫描次数**: {scan_stats['total_scans']}
- **扫描File数**: {scan_stats['files_scanned']:,}
- **Found威胁**: {scan_stats['threats_found']}
- **清洁File**: {scan_stats['clean_files']:,}
- **平均扫描Time**: {scan_stats['scan_time_avg']}秒
- **最后扫描**: {scan_stats['last_scan']}

## 🚨 威胁Detection

### 今日Detection到 {len(threats)} 个威胁

"""
        
        for threat in threats:
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            report += f"""
#### {severity_emoji.get(threat['severity'], '⚪')} {threat['type'].upper()}
- **FilePath**: `{threat['file_path']}`
- **严重程度**: {threat['severity']}
- **AI置信度**: {threat['ai_confidence']:.1%}
- **ProcessStatus**: {threat['status']}
- **描述**: {threat['description']}
"""
        
        report += f"""

## 🌐 NetworkSecurity事件

### 今日Network事件 {len(network_events)} 个

"""
        
        for event in network_events:
            risk_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            report += f"""
#### {risk_emoji.get(event['risk_level'], '⚪')} {event['type'].replace('_', ' ').title()}
- **源IP**: {event.get('source_ip', 'N/A')}
- **风险等级**: {event['risk_level']}
- **描述**: {event['description']}
"""
        
        report += f"""

## 🧠 AIAnalysis洞察

### 威胁趋势
- **趋势**: {ai_insights['threat_trend']}
- **风险评分**: {ai_insights['risk_score']}/10
- **Analysis置信度**: {ai_insights['confidence']:.1%}

### 🔮 AIPrediction
"""
        
        for prediction in ai_insights['predictions']:
            report += f"- {prediction}\n"
        
        report += "\n### 💡 AI建议\n"
        for recommendation in ai_insights['recommendations']:
            report += f"- {recommendation}\n"
        
        report += f"""

## 📈 SystemStatus

- **CPU使用率**: {data['system_health']['cpu_usage']}%
- **Memory使用率**: {data['system_health']['memory_usage']}%
- **Disk使用率**: {data['system_health']['disk_usage']}%

## 🎯 总结

今日Security状况总体良好，AISystemDetection到 {len(threats)} 个威胁并Already妥善Process。
建议Continue保持当前防护Policy，定期UpdateSecurityGroup件。

---
*Report生成Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*由AISecurity助手Automatic生成*
"""
        
        return report
    
    async def generate_weekly_report(self, data: Dict[str, Any]) -> str:
        """生成周报"""
        return f"""
# 📅 周度SecurityReport - {datetime.now().strftime('%Y年第%U周')}

## 📊 本周Statistics概览

- **总扫描次数**: 1,089
- **扫描File数**: 316,740
- **Found威胁**: 23
- **阻止攻击**: 15
- **误报Quantity**: 2

## 🔍 威胁Analysis趋势

本周威胁活动相比上周下降了15%，主要威胁TypePackage括：
- 木马Program (35%)
- 广告Software (28%)
- 可疑Script (22%)
- 其他 (15%)

## 💡 AI洞察与建议

基于本周DataAnalysis，AISystem建议：
1. 加强对DownloadFile的实时Monitor
2. UpdateNetwork访问控制Policy
3. 定期进行全SystemDepth扫描

---
*AISecurity助手周度AnalysisReport*
"""
    
    async def generate_threat_summary(self, data: Dict[str, Any]) -> str:
        """生成威胁摘要Report"""
        threats = data['threat_detections']
        
        return f"""
# 🚨 威胁摘要Report

## 当前威胁状况

Detection到 {len(threats)} 个活跃威胁，AIAnalysis如下：

### 高危威胁
{len([t for t in threats if t['severity'] == 'high'])} 个

### 中危威胁  
{len([t for t in threats if t['severity'] == 'medium'])} 个

### 低危威胁
{len([t for t in threats if t['severity'] == 'low'])} 个

## AI建议
立即Process所Has高危威胁，Monitor中低危威胁发展。

---
*威胁摘要 - {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    async def generate_network_report(self, data: Dict[str, Any]) -> str:
        """生成NetworkSecurityReport"""
        events = data['network_events']
        
        return f"""
# 🌐 NetworkSecurityReport

## Network事件概览

今日Detection到 {len(events)} 个NetworkSecurity事件：

### 事件分Class
- 可疑Connection: {len([e for e in events if e['type'] == 'suspicious_connection'])}
- 登录Failed: {len([e for e in events if e['type'] == 'failed_login'])}

## AINetworkAnalysis
Network活动整体正常，建议加强访问控制。

---
*NetworkSecurityAnalysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    async def generate_ai_analysis_report(self, data: Dict[str, Any]) -> str:
        """生成AIDepthAnalysisReport"""
        ai_insights = data['ai_insights']
        
        return f"""
# 🧠 AIDepthAnalysisReport

## SmartAnalysisResult

### 威胁态势Evaluation
- **当前风险等级**: {ai_insights['risk_score']}/10
- **趋势Prediction**: {ai_insights['threat_trend']}
- **Analysis置信度**: {ai_insights['confidence']:.1%}

### AIPredictionAnalysis
"""
        
        for prediction in ai_insights['predictions']:
            return f"- {prediction}\n"
        
        return """

### Smart建议
基于Machine LearningModelAnalysis，建议采取以下措施OptimizationSecurity防护。

---
*AIDepthAnalysis - Machine Learning驱动*
"""
    
    async def save_report(self, report_content: str, report_type: str, 
                         format_type: str = 'html') -> str:
        """SaveReport到File"""
        output_dir = Path(self.config['report']['output_dir'])
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_{timestamp}.{format_type}"
        filepath = output_dir / filename
        
        if format_type == 'html':
            # 转换Markdown到HTML
            html_content = self.markdown_to_html(report_content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        logger.info(f"ReportAlreadySave: {filepath}")
        return str(filepath)
    
    def markdown_to_html(self, markdown_content: str) -> str:
        """将Markdown转换为HTML"""
        # 简单的Markdown到HTML转换
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AISecurityReport</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; }}
        h3 {{ color: #7f8c8d; }}
        .threat-high {{ color: #e74c3c; }}
        .threat-medium {{ color: #f39c12; }}
        .threat-low {{ color: #27ae60; }}
        code {{ background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div>{markdown_content.replace(chr(10), '<br>')}</div>
    <footer>
        <hr>
        <p><em>由AISecurity助手Automatic生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    </footer>
</body>
</html>
"""
        return html
    
    async def send_email_report(self, report_type: str, report_content: str,
                               data: Dict[str, Any], report_file: str = None):
        """Send邮件Report"""
        try:
            if report_type == 'daily':
                # 准备每日ReportData
                report_data = {
                    'scanned_files': data['scan_statistics'].get('files_scanned', 0),
                    'total_threats': len(data['threat_detections']),
                    'handled_threats': len([t for t in data['threat_detections'] if t.get('status') == 'quarantined']),
                    'avg_scan_time': data['scan_statistics'].get('scan_time_avg', 0),
                    'success_rate': 95,  # 模拟Success率
                    'threat_level': 'low' if len(data['threat_detections']) < 5 else 'medium',
                    'threats': data['threat_detections'][:5],  # 只显示前5个威胁
                    'ai_insights': data['ai_insights'].get('predictions', []),
                    'recommendations': data['ai_insights'].get('recommendations', [])
                }

                success = await self.email_service.send_daily_report(report_data, report_file)

            elif report_type == 'weekly':
                # 准备周报Data
                report_data = {
                    'total_scans': 156,
                    'total_files': 45230,
                    'total_threats': len(data['threat_detections']) * 7,  # 模拟一周Data
                    'avg_response_time': 2.3,
                    'trend': 'down',
                    'trend_percentage': 15,
                    'threat_trends': [
                        {'type': '木马Program', 'current_week': 12, 'last_week': 18, 'change': -33},
                        {'type': '广告Software', 'current_week': 8, 'last_week': 6, 'change': 33},
                        {'type': '可疑Script', 'current_week': 3, 'last_week': 5, 'change': -40}
                    ],
                    'key_events': [
                        {'level': 'warning', 'title': 'Detection到新型威胁', 'description': 'Found新的恶意Software变种，AlreadyUpdateDetectionRules'},
                        {'level': 'info', 'title': 'SystemPerformanceOptimization', 'description': '扫描速度提升20%，误报率降低至2%以下'}
                    ],
                    'avg_cpu': 25.6,
                    'avg_memory': 68.2,
                    'uptime': 99.8,
                    'false_positive_rate': 1.8
                }

                success = await self.email_service.send_weekly_report(report_data, report_file)

            elif report_type == 'threat_summary':
                # Send威胁告警
                if data['threat_detections']:
                    for threat in data['threat_detections'][:3]:  # 只Send前3个威胁
                        threat_data = {
                            'type': threat.get('type', 'Unknown'),
                            'severity': threat.get('severity', 'medium'),
                            'level': threat.get('severity', 'medium'),
                            'detection_time': threat.get('detection_time', datetime.now().isoformat()),
                            'file_path': threat.get('file_path', 'N/A'),
                            'confidence': int(threat.get('ai_confidence', 0) * 100),
                            'status': threat.get('status', 'detected'),
                            'description': threat.get('description', ''),
                            'recommended_actions': [
                                '立即隔离可疑File',
                                '进行DepthSystem扫描',
                                'Check相关SystemFile',
                                'Update病毒Library到最新Version'
                            ],
                            'iocs': [threat.get('file_path', '')],
                            'id': threat.get('id', 'unknown')
                        }

                        success = await self.email_service.send_threat_alert(threat_data)
                else:
                    # SendCustomReport
                    success = await self.email_service.send_custom_report(
                        subject="威胁摘要Report",
                        content=report_content,
                        attachments=[report_file] if report_file else None
                    )
            else:
                # 其他TypeReportSendCustom邮件
                success = await self.email_service.send_custom_report(
                    subject=f"{report_type.title()} SecurityReport - {datetime.now().strftime('%Y-%m-%d')}",
                    content=report_content,
                    attachments=[report_file] if report_file else None
                )

            if success:
                logger.info(f"邮件ReportSendSuccess: {report_type}")
            else:
                logger.error(f"邮件ReportSendFailed: {report_type}")

        except Exception as e:
            logger.error(f"邮件SendException: {e}")

    async def send_emergency_email(self, threats: List[Dict]):
        """Send紧急威胁邮件"""
        try:
            emergency_data = {
                'critical_threats': len([t for t in threats if t.get('severity') == 'high']),
                'affected_systems': 1,  # 模拟受影响System数
                'response_time': 2,     # 模拟ResponseTime
                'actions_taken': 3,     # 模拟AlreadyExecute措施数
                'threats': threats,
                'auto_actions': [
                    'Automatic隔离可疑File',
                    '阻断恶意IP地址',
                    'StartDepth扫描'
                ],
                'immediate_actions': [
                    '立即Check所Has受影响System',
                    'ValidationAutomaticResponse措施的Has效性',
                    '通知相关技术Team',
                    '准备详细的事件Report',
                    '考虑Start应急Response流程'
                ]
            }

            success = await self.email_service.send_emergency_alert(emergency_data)

            if success:
                logger.warning("紧急威胁邮件SendSuccess")
            else:
                logger.error("紧急威胁邮件SendFailed")

        except Exception as e:
            logger.error(f"紧急邮件SendException: {e}")
    
    async def generate_report(self, report_type: str = 'daily') -> str:
        """生成指定Type的Report"""
        logger.info(f"Start生成 {report_type} Report...")
        
        # 收集Data
        data = await self.collect_security_data()
        
        # 生成Report
        if report_type in self.report_templates:
            report_content = await self.report_templates[report_type](data)
        else:
            raise ValueError(f"不支持的ReportType: {report_type}")
        
        # SaveReport
        for format_type in self.config['report']['formats']:
            await self.save_report(report_content, report_type, format_type)
        
        # Send邮件
        await self.send_email_report(report_type, report_content, data, report_path)
        
        logger.info(f"{report_type} Report生成Complete")
        return report_content
    
    def schedule_reports(self):
        """Settings定时Report"""
        # 每日Report
        daily_time = self.config['schedule']['daily_report_time']
        schedule.every().day.at(daily_time).do(
            lambda: asyncio.create_task(self.generate_report('daily'))
        )
        
        # 周报
        weekly_day = self.config['schedule']['weekly_report_day']
        weekly_time = self.config['schedule']['weekly_report_time']
        getattr(schedule.every(), weekly_day).at(weekly_time).do(
            lambda: asyncio.create_task(self.generate_report('weekly'))
        )
        
        logger.info(f"定时ReportAlreadySettings: 每日 {daily_time}, 每周{weekly_day} {weekly_time}")
    
    async def start_scheduler(self):
        """Start定时Task"""
        self.schedule_reports()
        
        logger.info("AIReport生成器AlreadyStart，等待定时Task...")
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # 每分钟Check一次

# Command行Interface
async def main():
    """Main Function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AISecurityReport生成器')
    parser.add_argument('--type', choices=['daily', 'weekly', 'threat_summary', 
                                          'network_security', 'ai_analysis'],
                       default='daily', help='ReportType')
    parser.add_argument('--schedule', action='store_true', help='Start定时Task')
    parser.add_argument('--config', default='report_config.yaml', help='ConfigurationFilePath')
    
    args = parser.parse_args()
    
    generator = AIReportGenerator(args.config)
    
    if args.schedule:
        await generator.start_scheduler()
    else:
        report = await generator.generate_report(args.type)
        print("Report生成Complete:")
        print(report[:500] + "..." if len(report) > 500 else report)

if __name__ == "__main__":
    asyncio.run(main())
