#!/usr/bin/env python3
"""
简化版 HunterMatrix + NetworkMonitor集成
适合快速Demo和Test
"""

import time
import json
import subprocess
import psutil
import requests
from datetime import datetime
from typing import Dict, List
import threading
import os

class SimpleNetworkMonitor:
    """简单的NetworkMonitor器"""
    
    def __init__(self):
        self.connections = []
        self.suspicious_ips = set()
        self.monitoring = False
    
    def start_monitoring(self):
        """StartMonitor"""
        self.monitoring = True
        print("🌐 StartNetworkMonitor...")
        
        while self.monitoring:
            try:
                # 获取NetworkConnection
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        
                        # Check是否为可疑Connection
                        if self.is_suspicious_connection(remote_ip, remote_port):
                            print(f"🚨 Found可疑Connection: {remote_ip}:{remote_port}")
                            self.suspicious_ips.add(remote_ip)
                            
                            # 触发HunterMatrix扫描
                            self.trigger_scan(f"可疑Connection: {remote_ip}:{remote_port}")
                
                time.sleep(5)  # 每5秒Check一次
                
            except Exception as e:
                print(f"❌ NetworkMonitorError: {e}")
                time.sleep(10)
    
    def is_suspicious_connection(self, ip: str, port: int) -> bool:
        """判断是否为可疑Connection"""
        # 简单的启发式Rules
        suspicious_ports = [22, 23, 135, 139, 445, 1433, 3389, 5900]
        
        # Check端口
        if port in suspicious_ports:
            return True
        
        # CheckIP段（Example：Check某些可疑IP段）
        if ip.startswith('192.168.') and not ip.startswith('192.168.1.'):
            return True
        
        return False
    
    def trigger_scan(self, reason: str):
        """触发HunterMatrix扫描"""
        print(f"🔍 触发扫描 - 原因: {reason}")
        
        # 这里可以调用HunterMatrix扫描
        # 为了Demo，我们扫描DownloadDirectory
        scan_paths = [
            os.path.expanduser("~/Downloads"),
            "/tmp"
        ]
        
        for path in scan_paths:
            if os.path.exists(path):
                self.run_huntermatrix_scan(path, reason)
    
    def run_huntermatrix_scan(self, path: str, reason: str):
        """RunHunterMatrix扫描"""
        try:
            print(f"🦠 扫描Path: {path}")
            
            # 模拟HunterMatrix扫描Command
            # 实际环境中使用: clamscan -r --bell -i /path
            result = {
                "timestamp": datetime.now().isoformat(),
                "path": path,
                "reason": reason,
                "status": "completed",
                "threats_found": 0,
                "files_scanned": 0
            }
            
            # 这里可以解析实际的HunterMatrixOutput
            # 为了Demo，我们模拟Result
            import random
            result["files_scanned"] = random.randint(10, 100)
            
            if random.random() < 0.1:  # 10%概率Found威胁
                result["threats_found"] = random.randint(1, 3)
                result["status"] = "threats_detected"
                print(f"⚠️  Found {result['threats_found']} 个威胁!")
            else:
                print(f"✅ 扫描Complete，NotFound威胁")
            
            # SaveResult
            self.save_scan_result(result)
            
        except Exception as e:
            print(f"❌ 扫描Failed: {e}")
    
    def save_scan_result(self, result: Dict):
        """Save扫描Result"""
        results_file = "scan_results.json"
        
        # Read现HasResult
        results = []
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            except:
                results = []
        
        # 添加新Result
        results.append(result)
        
        # 保持最近100条Record
        if len(results) > 100:
            results = results[-100:]
        
        # Save到File
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def stop_monitoring(self):
        """StopMonitor"""
        self.monitoring = False
        print("🛑 NetworkMonitorAlreadyStop")

class IntegrationDashboard:
    """集成仪Table板"""
    
    def __init__(self):
        self.monitor = SimpleNetworkMonitor()
        self.running = False
    
    def start(self):
        """StartIntegration Service"""
        print("🚀 Start HunterMatrix + NetworkMonitorIntegration Service")
        print("=" * 50)
        
        self.running = True
        
        # 在后台ThreadStartNetworkMonitor
        monitor_thread = threading.Thread(target=self.monitor.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start仪Table板
        self.run_dashboard()
    
    def run_dashboard(self):
        """Run仪Table板"""
        while self.running:
            try:
                self.display_status()
                
                print("\n" + "=" * 50)
                print("CommandMenu:")
                print("1. 查看NetworkStatus")
                print("2. Manual触发扫描")
                print("3. 查看扫描历史")
                print("4. 查看可疑IP")
                print("5. 生成Report")
                print("0. 退出")
                print("=" * 50)
                
                choice = input("请选择Operation (0-5): ").strip()
                
                if choice == '1':
                    self.show_network_status()
                elif choice == '2':
                    self.manual_scan()
                elif choice == '3':
                    self.show_scan_history()
                elif choice == '4':
                    self.show_suspicious_ips()
                elif choice == '5':
                    self.generate_report()
                elif choice == '0':
                    self.stop()
                    break
                else:
                    print("❌ No效选择")
                
                input("\n按回车键Continue...")
                
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"❌ 仪Table板Error: {e}")
    
    def display_status(self):
        """显示Status"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🛡️  HunterMatrix + NetworkMonitor集成仪Table板")
        print("=" * 50)
        print(f"⏰ 当前Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 NetworkMonitor: {'Run中' if self.monitor.monitoring else 'AlreadyStop'}")
        print(f"🚨 可疑IPQuantity: {len(self.monitor.suspicious_ips)}")
        
        # 显示System资源
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        print(f"💻 CPU使用率: {cpu_percent}%")
        print(f"🧠 Memory使用率: {memory.percent}%")
        
        # 显示NetworkConnection数
        connections = len(psutil.net_connections(kind='inet'))
        print(f"🔗 NetworkConnection数: {connections}")
    
    def show_network_status(self):
        """显示NetworkStatus"""
        print("\n🌐 NetworkConnectionStatus:")
        print("-" * 30)
        
        connections = psutil.net_connections(kind='inet')
        established = [c for c in connections if c.status == 'ESTABLISHED' and c.raddr]
        
        for i, conn in enumerate(established[:10]):  # 显示前10个
            print(f"{i+1}. {conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip}:{conn.raddr.port}")
        
        if len(established) > 10:
            print(f"... 还Has {len(established) - 10} 个Connection")
    
    def manual_scan(self):
        """Manual触发扫描"""
        print("\n🔍 Manual扫描")
        print("-" * 20)
        
        path = input("请Input扫描Path (回车使用DefaultPath): ").strip()
        if not path:
            path = os.path.expanduser("~/Downloads")
        
        if os.path.exists(path):
            self.monitor.run_huntermatrix_scan(path, "Manual触发")
        else:
            print(f"❌ Path不存在: {path}")
    
    def show_scan_history(self):
        """显示扫描历史"""
        print("\n📋 扫描历史:")
        print("-" * 30)
        
        results_file = "scan_results.json"
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                for i, result in enumerate(results[-10:]):  # 显示最近10条
                    status_icon = "⚠️" if result.get("threats_found", 0) > 0 else "✅"
                    print(f"{i+1}. {status_icon} {result['timestamp'][:19]} - {result['path']}")
                    print(f"   原因: {result['reason']}")
                    print(f"   File: {result.get('files_scanned', 0)}, 威胁: {result.get('threats_found', 0)}")
                    print()
                
            except Exception as e:
                print(f"❌ Read历史Failed: {e}")
        else:
            print("📝 暂No扫描历史")
    
    def show_suspicious_ips(self):
        """显示可疑IP"""
        print("\n🚨 可疑IP列Table:")
        print("-" * 20)
        
        if self.monitor.suspicious_ips:
            for i, ip in enumerate(self.monitor.suspicious_ips):
                print(f"{i+1}. {ip}")
        else:
            print("✅ 暂No可疑IP")
    
    def generate_report(self):
        """生成Report"""
        print("\n📊 生成集成Report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_status": self.monitor.monitoring,
            "suspicious_ips": list(self.monitor.suspicious_ips),
            "system_info": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "network_connections": len(psutil.net_connections(kind='inet'))
            }
        }
        
        # 添加扫描历史
        results_file = "scan_results.json"
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    scan_results = json.load(f)
                    report["scan_summary"] = {
                        "total_scans": len(scan_results),
                        "threats_detected": sum(1 for r in scan_results if r.get("threats_found", 0) > 0),
                        "recent_scans": scan_results[-5:]  # 最近5次扫描
                    }
            except:
                report["scan_summary"] = {"error": "No法Read扫描历史"}
        
        # SaveReport
        report_file = f"integration_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ ReportAlready生成: {report_file}")
    
    def stop(self):
        """StopService"""
        print("\n🛑 ProcessingStopService...")
        self.running = False
        self.monitor.stop_monitoring()
        print("✅ ServiceAlreadyStop")

def main():
    """Main Function"""
    try:
        dashboard = IntegrationDashboard()
        dashboard.start()
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ ProgramError: {e}")

if __name__ == "__main__":
    main()
