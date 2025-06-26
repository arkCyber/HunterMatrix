#!/usr/bin/env python3
"""
AISecurityReport调度Service
支持定时生成、Command触发和紧急Report
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import schedule
import time
import threading

from ai_report_generator import AIReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('report_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReportScheduler:
    """Report调度Service"""
    
    def __init__(self, config_path: str = "report_config.yaml"):
        self.config_path = config_path
        self.generator = AIReportGenerator(config_path)
        self.running = False
        self.scheduler_thread = None
        
        # CommandQueue
        self.command_queue = asyncio.Queue()
        
        # Report历史
        self.report_history = []
        
        # 紧急Report阈值
        self.emergency_threshold = 0.9
        
        # Settings信号Process
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号Process器"""
        logger.info(f"Receive到信号 {signum}，Processing关闭Service...")
        self.stop()
        sys.exit(0)
    
    async def start(self):
        """Start调度Service"""
        logger.info("🚀 StartAISecurityReport调度Service...")
        
        self.running = True
        
        # Settings定时Task
        self.setup_scheduled_tasks()
        
        # Start调度器Thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # StartCommandProcess
        await self.start_command_processor()
    
    def setup_scheduled_tasks(self):
        """Settings定时Task"""
        config = self.generator.config
        
        # 每日Report
        daily_time = config['schedule']['daily_report_time']
        schedule.every().day.at(daily_time).do(self.schedule_daily_report)
        
        # 周报
        weekly_day = config['schedule']['weekly_report_day']
        weekly_time = config['schedule']['weekly_report_time']
        getattr(schedule.every(), weekly_day).at(weekly_time).do(self.schedule_weekly_report)
        
        # 每小时威胁Check
        schedule.every().hour.do(self.check_threats)
        
        # 每30分钟System健康Check
        schedule.every(30).minutes.do(self.health_check)
        
        logger.info(f"✅ 定时TaskAlreadySettings:")
        logger.info(f"   📅 每日Report: {daily_time}")
        logger.info(f"   📊 周报: 每周{weekly_day} {weekly_time}")
        logger.info(f"   🔍 威胁Check: 每小时")
        logger.info(f"   💓 健康Check: 每30分钟")
    
    def run_scheduler(self):
        """Run调度器"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟Check一次
    
    def schedule_daily_report(self):
        """调度每日Report"""
        asyncio.create_task(self.generate_report_async('daily'))
    
    def schedule_weekly_report(self):
        """调度周报"""
        asyncio.create_task(self.generate_report_async('weekly'))
    
    def check_threats(self):
        """Check威胁状况"""
        asyncio.create_task(self.threat_check_async())
    
    def health_check(self):
        """System健康Check"""
        asyncio.create_task(self.health_check_async())
    
    async def generate_report_async(self, report_type: str):
        """Async生成Report"""
        try:
            logger.info(f"📊 Start生成 {report_type} Report...")
            report = await self.generator.generate_report(report_type)
            
            # RecordReport历史
            self.report_history.append({
                'type': report_type,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'size': len(report)
            })
            
            logger.info(f"✅ {report_type} Report生成Complete")
            
        except Exception as e:
            logger.error(f"❌ {report_type} Report生成Failed: {e}")
            
            # RecordFailed
            self.report_history.append({
                'type': report_type,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            })
    
    async def threat_check_async(self):
        """Async威胁Check"""
        try:
            logger.info("🔍 Execute威胁Check...")
            
            # 收集威胁Data
            data = await self.generator.collect_security_data()
            threats = data['threat_detections']
            
            # Check是否Has高危威胁
            high_threats = [t for t in threats if t.get('ai_confidence', 0) > self.emergency_threshold]
            
            if high_threats:
                logger.warning(f"⚠️ Found {len(high_threats)} 个高危威胁，生成紧急Report...")
                await self.generate_emergency_report(high_threats)
            
            logger.info(f"✅ 威胁CheckComplete，Found {len(threats)} 个威胁")
            
        except Exception as e:
            logger.error(f"❌ 威胁CheckFailed: {e}")
    
    async def health_check_async(self):
        """Async健康Check"""
        try:
            logger.info("💓 ExecuteSystem健康Check...")
            
            # CheckServiceStatus
            health_data = await self.generator.get_system_health()
            
            # Check关键Metric
            cpu_usage = health_data.get('cpu_usage', 0)
            memory_usage = health_data.get('memory_usage', 0)
            
            if cpu_usage > 90 or memory_usage > 90:
                logger.warning(f"⚠️ System资源使用率过高: CPU {cpu_usage}%, Memory {memory_usage}%")
                await self.generate_system_alert(health_data)
            
            logger.info(f"✅ System健康CheckComplete: CPU {cpu_usage}%, Memory {memory_usage}%")
            
        except Exception as e:
            logger.error(f"❌ 健康CheckFailed: {e}")
    
    async def generate_emergency_report(self, threats: List[Dict]):
        """生成紧急威胁Report"""
        try:
            logger.warning("🚨 生成紧急威胁Report...")
            
            # Create紧急ReportContent
            report_content = f"""
# 🚨 紧急威胁Report

**ReportTime**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**威胁等级**: 🔴 高危

## 威胁概览

Detection到 {len(threats)} 个高危威胁，需要立即Process：

"""
            
            for i, threat in enumerate(threats, 1):
                report_content += f"""
### 威胁 {i}: {threat.get('type', 'Unknown').upper()}

- **FilePath**: `{threat.get('file_path', 'N/A')}`
- **AI置信度**: {threat.get('ai_confidence', 0):.1%}
- **DetectionTime**: {threat.get('detection_time', 'N/A')}`
- **描述**: {threat.get('description', 'N/A')}
- **建议**: 立即隔离并进行DepthAnalysis

"""
            
            report_content += f"""
## 🚨 紧急Process建议

1. **立即隔离** 所Has受影响的System
2. **断开Network** 防止横向传播
3. **Start应急Response** 流程
4. **通知SecurityTeam** 进行Depth调查
5. **Backup关键Data** 防止Data丢失

---
*这是一个Automatic生成的紧急威胁Report*
*请立即采取行动Process上述威胁*
"""
            
            # Save紧急Report
            await self.generator.save_report(report_content, 'emergency', 'html')
            
            # Send紧急邮件
            await self.generator.send_emergency_email(threats)
            
            logger.warning("✅ 紧急威胁ReportAlready生成并Send")
            
        except Exception as e:
            logger.error(f"❌ 紧急Report生成Failed: {e}")
    
    async def generate_system_alert(self, health_data: Dict):
        """生成System告警"""
        try:
            logger.warning("⚠️ 生成System告警...")
            
            alert_content = f"""
# ⚠️ System资源告警

**告警Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SystemStatus

- **CPU使用率**: {health_data.get('cpu_usage', 0)}%
- **Memory使用率**: {health_data.get('memory_usage', 0)}%
- **Disk使用率**: {health_data.get('disk_usage', 0)}%

## 建议措施

1. Check高CPU/Memory占用Process
2. Clean临时File和Log
3. Restart相关Service
4. MonitorSystemPerformance

---
*SystemAutomatic告警*
"""
            
            # Send告警邮件
            if self.generator.config['email']['enabled']:
                await self.generator.send_email_report(
                    alert_content, 
                    "⚠️ System资源告警"
                )
            
            logger.warning("✅ System告警AlreadySend")
            
        except Exception as e:
            logger.error(f"❌ System告警生成Failed: {e}")
    
    async def start_command_processor(self):
        """StartCommandProcess器"""
        logger.info("🎮 StartCommandProcess器...")
        
        while self.running:
            try:
                # 等待Command
                command = await asyncio.wait_for(
                    self.command_queue.get(), 
                    timeout=1.0
                )
                
                await self.process_command(command)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"CommandProcessError: {e}")
    
    async def process_command(self, command: Dict):
        """ProcessCommand"""
        cmd_type = command.get('type')
        
        logger.info(f"📝 ProcessCommand: {cmd_type}")
        
        if cmd_type == 'generate_report':
            report_type = command.get('report_type', 'daily')
            await self.generate_report_async(report_type)
            
        elif cmd_type == 'threat_check':
            await self.threat_check_async()
            
        elif cmd_type == 'health_check':
            await self.health_check_async()
            
        elif cmd_type == 'emergency_scan':
            await self.emergency_scan()
            
        elif cmd_type == 'status':
            await self.show_status()
            
        else:
            logger.warning(f"Not知CommandType: {cmd_type}")
    
    async def emergency_scan(self):
        """紧急扫描"""
        logger.warning("🚨 Execute紧急扫描...")
        
        try:
            # Execute全面威胁Check
            await self.threat_check_async()
            
            # 生成紧急Report
            await self.generate_report_async('threat_summary')
            
            logger.warning("✅ 紧急扫描Complete")
            
        except Exception as e:
            logger.error(f"❌ 紧急扫描Failed: {e}")
    
    async def show_status(self):
        """显示ServiceStatus"""
        logger.info("📊 ServiceStatus:")
        logger.info(f"   RunStatus: {'Run中' if self.running else 'AlreadyStop'}")
        logger.info(f"   Report历史: {len(self.report_history)} 个")
        logger.info(f"   最后Report: {self.report_history[-1]['timestamp'] if self.report_history else 'No'}")
        logger.info(f"   ConfigurationFile: {self.config_path}")
    
    async def send_command(self, command: Dict):
        """SendCommand到Queue"""
        await self.command_queue.put(command)
    
    def stop(self):
        """StopService"""
        logger.info("🛑 ProcessingStopAISecurityReport调度Service...")
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("✅ ServiceAlreadyStop")

# Command行Interface
async def main():
    """Main Function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AISecurityReport调度Service')
    parser.add_argument('--config', default='report_config.yaml', help='ConfigurationFilePath')
    parser.add_argument('--daemon', action='store_true', help='以守护Process模式Run')
    parser.add_argument('--command', choices=['generate', 'check', 'scan', 'status'], 
                       help='Execute单次Command')
    parser.add_argument('--type', default='daily', help='ReportType')
    
    args = parser.parse_args()
    
    scheduler = ReportScheduler(args.config)
    
    if args.command:
        # Execute单次Command
        if args.command == 'generate':
            await scheduler.send_command({
                'type': 'generate_report',
                'report_type': args.type
            })
        elif args.command == 'check':
            await scheduler.send_command({'type': 'threat_check'})
        elif args.command == 'scan':
            await scheduler.send_command({'type': 'emergency_scan'})
        elif args.command == 'status':
            await scheduler.send_command({'type': 'status'})
        
        # Start ServiceProcessCommand
        await scheduler.start()
    else:
        # Start守护Process
        try:
            await scheduler.start()
        except KeyboardInterrupt:
            scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
