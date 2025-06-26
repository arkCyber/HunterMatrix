#!/usr/bin/env python3
"""
HunterMatrix + Ntopng Integration Service
实现Network流量Monitor与病毒扫描的联动
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HunterMatrix-Ntopng-Integration')

class NtopngAPI:
    """Ntopng API Client"""
    
    def __init__(self, host: str = "localhost", port: int = 3000, username: str = "admin", password: str = "admin"):
        self.base_url = f"http://{host}:{port}"
        self.auth = aiohttp.BasicAuth(username, password)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(auth=self.auth)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_active_flows(self) -> List[Dict]:
        """获取活跃的Network流量"""
        try:
            async with self.session.get(f"{self.base_url}/lua/get_flows_data.lua") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"获取流量DataFailed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"APIRequestFailed: {e}")
            return []
    
    async def get_suspicious_flows(self) -> List[Dict]:
        """获取可疑流量"""
        try:
            async with self.session.get(f"{self.base_url}/lua/get_alerts_data.lua") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"获取告警DataFailed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"APIRequestFailed: {e}")
            return []

class HunterMatrixAPI:
    """HunterMatrix API Client"""
    
    def __init__(self, host: str = "localhost", port: int = 8081):
        self.base_url = f"http://{host}:{port}"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scan_file(self, file_path: str) -> Dict:
        """扫描File"""
        try:
            # 这里模拟HunterMatrix扫描API调用
            # 实际实现需要根据HunterMatrix的具体APIInterface
            scan_result = {
                "file_path": file_path,
                "status": "safe",  # safe, infected, error
                "threats_found": 0,
                "scan_time": datetime.now().isoformat(),
                "details": []
            }
            
            # 模拟扫描过程
            await asyncio.sleep(0.1)
            
            # 随机模拟威胁Detection（2%概率）
            import random
            if random.random() < 0.02:
                scan_result["status"] = "infected"
                scan_result["threats_found"] = 1
                scan_result["details"] = ["Trojan.Generic.Suspicious"]
            
            return scan_result
            
        except Exception as e:
            logger.error(f"File扫描Failed: {e}")
            return {
                "file_path": file_path,
                "status": "error",
                "error": str(e),
                "scan_time": datetime.now().isoformat()
            }

class ThreatDetector:
    """威胁Detection器"""
    
    def __init__(self):
        self.suspicious_patterns = [
            "malware",
            "trojan",
            "virus",
            "suspicious",
            "anomaly",
            "attack"
        ]
        self.high_risk_ports = [22, 23, 135, 139, 445, 1433, 3389]
    
    def analyze_flow(self, flow: Dict) -> Dict:
        """AnalysisNetwork流量"""
        risk_score = 0
        risk_factors = []
        
        # Check端口
        dst_port = flow.get('dst_port', 0)
        if dst_port in self.high_risk_ports:
            risk_score += 30
            risk_factors.append(f"高风险端口: {dst_port}")
        
        # Check流量Size
        bytes_sent = flow.get('bytes_sent', 0)
        bytes_rcvd = flow.get('bytes_rcvd', 0)
        total_bytes = bytes_sent + bytes_rcvd
        
        if total_bytes > 100 * 1024 * 1024:  # 100MB
            risk_score += 20
            risk_factors.append("大流量Transfer")
        
        # CheckConnection时长
        duration = flow.get('duration', 0)
        if duration > 3600:  # 1小时
            risk_score += 15
            risk_factors.append("长TimeConnection")
        
        # CheckProtocol
        protocol = flow.get('protocol', '').lower()
        if protocol in ['p2p', 'bittorrent']:
            risk_score += 25
            risk_factors.append("P2PProtocol")
        
        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "risk_factors": risk_factors,
            "requires_scan": risk_score >= 50
        }
    
    def _get_risk_level(self, score: int) -> str:
        """获取风险等级"""
        if score >= 70:
            return "高风险"
        elif score >= 40:
            return "中风险"
        elif score >= 20:
            return "低风险"
        else:
            return "正常"

class IntegrationService:
    """Integration Service主Class"""
    
    def __init__(self):
        self.ntopng = None
        self.huntermatrix = None
        self.detector = ThreatDetector()
        self.scan_queue = asyncio.Queue()
        self.results = []
        
    async def start(self):
        """StartIntegration Service"""
        logger.info("🚀 Start HunterMatrix + Ntopng Integration Service")
        
        # InitializeAPIClient
        self.ntopng = NtopngAPI()
        self.huntermatrix = HunterMatrixAPI()
        
        # StartMonitorTask
        tasks = [
            asyncio.create_task(self.monitor_traffic()),
            asyncio.create_task(self.process_scan_queue()),
            asyncio.create_task(self.generate_reports())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 ServiceStop")
        finally:
            await self.cleanup()
    
    async def monitor_traffic(self):
        """MonitorNetwork流量"""
        logger.info("📡 StartMonitorNetwork流量")
        
        async with self.ntopng:
            while True:
                try:
                    # 获取活跃流量
                    flows = await self.ntopng.get_active_flows()
                    
                    for flow in flows:
                        # Analysis流量
                        analysis = self.detector.analyze_flow(flow)
                        
                        if analysis["requires_scan"]:
                            logger.warning(f"🚨 Found可疑流量: {flow.get('src_ip')} -> {flow.get('dst_ip')}")
                            
                            # 添加到扫描Queue
                            await self.scan_queue.put({
                                "type": "suspicious_flow",
                                "flow": flow,
                                "analysis": analysis,
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    # 获取告警
                    alerts = await self.ntopng.get_suspicious_flows()
                    for alert in alerts:
                        logger.warning(f"⚠️  Network告警: {alert}")
                        
                        # 触发相关File扫描
                        await self.scan_queue.put({
                            "type": "network_alert",
                            "alert": alert,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    await asyncio.sleep(10)  # 每10秒Check一次
                    
                except Exception as e:
                    logger.error(f"流量MonitorError: {e}")
                    await asyncio.sleep(30)
    
    async def process_scan_queue(self):
        """Process扫描Queue"""
        logger.info("🔍 StartProcess扫描Queue")
        
        async with self.huntermatrix:
            while True:
                try:
                    # 从Queue获取扫描Task
                    task = await self.scan_queue.get()
                    
                    if task["type"] == "suspicious_flow":
                        await self.handle_suspicious_flow(task)
                    elif task["type"] == "network_alert":
                        await self.handle_network_alert(task)
                    
                    self.scan_queue.task_done()
                    
                except Exception as e:
                    logger.error(f"扫描QueueProcessError: {e}")
    
    async def handle_suspicious_flow(self, task: Dict):
        """Process可疑流量"""
        flow = task["flow"]
        analysis = task["analysis"]
        
        logger.info(f"🔍 Process可疑流量: {flow.get('src_ip')} -> {flow.get('dst_ip')}")
        
        # 这里可以实现具体的File扫描逻辑
        # 例如：扫描Download的File、临时File等
        scan_paths = [
            "/tmp",
            "/Users/arkSong/Downloads",
            "/var/tmp"
        ]
        
        for path in scan_paths:
            if os.path.exists(path):
                result = await self.huntermatrix.scan_file(path)
                
                if result["status"] == "infected":
                    logger.error(f"🦠 Found威胁: {path} - {result['details']}")
                    
                    # RecordResult
                    self.results.append({
                        "type": "threat_detected",
                        "source": "suspicious_flow",
                        "flow": flow,
                        "scan_result": result,
                        "timestamp": datetime.now().isoformat()
                    })
    
    async def handle_network_alert(self, task: Dict):
        """ProcessNetwork告警"""
        alert = task["alert"]
        
        logger.info(f"⚠️  ProcessNetwork告警: {alert}")
        
        # 触发全System扫描
        result = await self.huntermatrix.scan_file("/")
        
        self.results.append({
            "type": "alert_scan",
            "source": "network_alert",
            "alert": alert,
            "scan_result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def generate_reports(self):
        """生成Report"""
        logger.info("📊 Start生成Report")
        
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟生成一次Report
                
                if self.results:
                    report = {
                        "timestamp": datetime.now().isoformat(),
                        "total_events": len(self.results),
                        "threats_detected": len([r for r in self.results if r["type"] == "threat_detected"]),
                        "recent_events": self.results[-10:],  # 最近10个事件
                        "summary": self._generate_summary()
                    }
                    
                    # SaveReport
                    report_file = f"integration_report_{int(time.time())}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"📄 ReportAlready生成: {report_file}")
                    
            except Exception as e:
                logger.error(f"Report生成Error: {e}")
    
    def _generate_summary(self) -> Dict:
        """生成摘要"""
        total = len(self.results)
        threats = len([r for r in self.results if r["type"] == "threat_detected"])
        
        return {
            "total_events": total,
            "threats_detected": threats,
            "threat_rate": f"{(threats/total*100):.1f}%" if total > 0 else "0%",
            "last_threat": self.results[-1]["timestamp"] if threats > 0 else None
        }
    
    async def cleanup(self):
        """Clean资源"""
        logger.info("🧹 Clean资源")
        # 这里可以添加Clean逻辑

async def main():
    """Main Function"""
    service = IntegrationService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
