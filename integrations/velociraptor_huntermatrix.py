#!/usr/bin/env python3
"""
Velociraptor + HunterMatrix Integration Service
Implements endpoint monitoring and malware detection integration
"""

import asyncio
import json
import subprocess
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import os
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Velociraptor-HunterMatrix')

class VelociraptorAPI:
    """Velociraptor API Client"""
    
    def __init__(self, server_url: str = "https://localhost:8000", 
                 api_key: str = "", cert_path: str = ""):
        self.server_url = server_url
        self.api_key = api_key
        self.cert_path = cert_path
        self.session = None
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)  # Development环境
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={"X-API-Key": self.api_key}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_vql_query(self, query: str) -> List[Dict]:
        """ExecuteVQLQuery"""
        try:
            payload = {
                "query": query,
                "max_rows": 1000
            }
            
            async with self.session.post(
                f"{self.server_url}/api/v1/RunVQL",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("rows", [])
                else:
                    logger.error(f"VQLQueryFailed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"VQLQueryException: {e}")
            return []
    
    async def create_hunt(self, artifact: str, parameters: Dict = None) -> str:
        """Create Hunt Task"""
        try:
            payload = {
                "artifacts": [artifact],
                "parameters": parameters or {},
                "description": f"HunterMatrix Integration Hunt - {artifact}"
            }
            
            async with self.session.post(
                f"{self.server_url}/api/v1/CreateHunt",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("hunt_id", "")
                else:
                    logger.error(f"Create狩猎Failed: {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Create狩猎Exception: {e}")
            return ""
    
    async def get_hunt_results(self, hunt_id: str) -> List[Dict]:
        """Get Hunt Results"""
        try:
            async with self.session.get(
                f"{self.server_url}/api/v1/GetHuntResults/{hunt_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"Get Hunt ResultsFailed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting hunt results: {e}")
            return []

class HunterMatrixScanner:
    """HunterMatrix Scanner"""
    
    def __init__(self, db_path: str = "/var/lib/huntermatrix"):
        self.db_path = db_path
        self.scan_history = []
    
    async def scan_file(self, file_path: str) -> Dict:
        """Scan Single File"""
        try:
            cmd = [
                "clamscan",
                "--database", self.db_path,
                "--no-summary",
                "--infected",
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "file_path": file_path,
                "scan_time": datetime.now().isoformat(),
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "status": "clean",
                "threats": []
            }
            
            # 解析扫描Result
            if process.returncode == 1:  # Found威胁
                result["status"] = "infected"
                # 解析威胁Information
                for line in result["stdout"].split('\n'):
                    if "FOUND" in line:
                        threat_info = line.strip()
                        result["threats"].append(threat_info)
            elif process.returncode == 0:  # 干净
                result["status"] = "clean"
            else:  # Error
                result["status"] = "error"
            
            # Record历史
            self.scan_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"扫描FileFailed {file_path}: {e}")
            return {
                "file_path": file_path,
                "scan_time": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def scan_directory(self, dir_path: str, recursive: bool = True) -> Dict:
        """Scan Directory"""
        try:
            cmd = [
                "clamscan",
                "--database", self.db_path,
                "--no-summary"
            ]
            
            if recursive:
                cmd.append("--recursive")
            
            cmd.append(dir_path)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "directory": dir_path,
                "scan_time": datetime.now().isoformat(),
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "files_scanned": 0,
                "threats_found": 0,
                "infected_files": []
            }
            
            # 解析Result
            lines = result["stdout"].split('\n')
            for line in lines:
                if "FOUND" in line:
                    result["threats_found"] += 1
                    result["infected_files"].append(line.strip())
                elif "scanned" in line and "infected" in line:
                    # 解析扫描Statistics
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "scanned" and i > 0:
                            try:
                                result["files_scanned"] = int(parts[i-1])
                            except:
                                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Scan DirectoryFailed {dir_path}: {e}")
            return {
                "directory": dir_path,
                "scan_time": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

class ThreatHunter:
    """Threat Hunter"""
    
    def __init__(self, velo_api: VelociraptorAPI, scanner: HunterMatrixScanner):
        self.velo_api = velo_api
        self.scanner = scanner
        self.hunt_rules = []
        self.load_hunt_rules()
    
    def load_hunt_rules(self):
        """Load狩猎Rules"""
        self.hunt_rules = [
            {
                "name": "suspicious_downloads",
                "description": "Detection可疑DownloadFile",
                "vql": """
                    SELECT FullPath, Size, Mtime, Atime
                    FROM glob(globs="C:\\\\Users\\\\**\\\\Downloads\\\\*.exe")
                    WHERE Size > 1000000 AND 
                          Mtime > timestamp(epoch=now() - 3600)
                """,
                "priority": "high"
            },
            {
                "name": "temp_executables",
                "description": "Detection临时Directory可ExecuteFile",
                "vql": """
                    SELECT FullPath, Size, Mtime
                    FROM glob(globs=["C:\\\\Temp\\\\*.exe", "C:\\\\Windows\\\\Temp\\\\*.exe"])
                    WHERE Mtime > timestamp(epoch=now() - 1800)
                """,
                "priority": "medium"
            },
            {
                "name": "startup_modifications",
                "description": "DetectionStart项Modify",
                "vql": """
                    SELECT Key, ValueName, ValueData
                    FROM registry(globs="HKEY_LOCAL_MACHINE\\\\Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run\\\\**")
                    WHERE ValueData =~ "\\\\.(exe|bat|cmd|scr)$"
                """,
                "priority": "high"
            }
        ]
    
    async def run_hunt(self, rule_name: str) -> List[Dict]:
        """Execute Hunt Rule"""
        rule = next((r for r in self.hunt_rules if r["name"] == rule_name), None)
        if not rule:
            logger.error(f"Not找到狩猎Rules: {rule_name}")
            return []
        
        logger.info(f"Execute Hunt Rule: {rule['name']}")
        
        # ExecuteVQLQuery
        results = await self.velo_api.run_vql_query(rule["vql"])
        
        # 对Found的File进行HunterMatrix扫描
        scan_results = []
        for result in results:
            if "FullPath" in result:
                file_path = result["FullPath"]
                logger.info(f"扫描Found的File: {file_path}")
                
                scan_result = await self.scanner.scan_file(file_path)
                
                # MergeResult
                combined_result = {
                    "hunt_rule": rule_name,
                    "discovery": result,
                    "scan_result": scan_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                scan_results.append(combined_result)
                
                # 如果Found威胁，Record高优先级Log
                if scan_result.get("status") == "infected":
                    logger.warning(f"🦠 Found威胁: {file_path} - {scan_result.get('threats', [])}")
        
        return scan_results
    
    async def continuous_hunt(self, interval: int = 300):
        """持续狩猎"""
        logger.info(f"Start持续威胁狩猎，间隔: {interval}秒")
        
        while True:
            try:
                for rule in self.hunt_rules:
                    logger.info(f"Execute Hunt Rule: {rule['name']}")
                    results = await self.run_hunt(rule["name"])
                    
                    if results:
                        logger.info(f"狩猎Rules {rule['name']} Found {len(results)} 个Result")
                        
                        # SaveResult
                        self.save_hunt_results(rule["name"], results)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"持续狩猎Error: {e}")
                await asyncio.sleep(60)
    
    def save_hunt_results(self, rule_name: str, results: List[Dict]):
        """Save Hunt Results"""
        timestamp = int(time.time())
        filename = f"hunt_results_{rule_name}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "rule_name": rule_name,
                    "timestamp": datetime.now().isoformat(),
                    "results_count": len(results),
                    "results": results
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"狩猎ResultAlreadySave: {filename}")
            
        except Exception as e:
            logger.error(f"Save Hunt ResultsFailed: {e}")

class VelociraptorHunterMatrixService:
    """Velociraptor + HunterMatrix Integration Service"""
    
    def __init__(self, config_file: str = "integration_config.yaml"):
        self.config = self.load_config(config_file)
        self.velo_api = None
        self.scanner = None
        self.hunter = None
    
    def load_config(self, config_file: str) -> Dict:
        """LoadConfigurationFile"""
        default_config = {
            "velociraptor": {
                "server_url": "https://localhost:8000",
                "api_key": "",
                "cert_path": ""
            },
            "huntermatrix": {
                "db_path": "/var/lib/huntermatrix"
            },
            "hunting": {
                "interval": 300,
                "enabled": True
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # MergeDefaultConfiguration
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.warning(f"LoadConfigurationFileFailed，使用DefaultConfiguration: {e}")
        
        return default_config
    
    async def start(self):
        """StartIntegration Service"""
        logger.info("🚀 Start Velociraptor + HunterMatrix Integration Service")
        
        # InitializeGroup件
        self.velo_api = VelociraptorAPI(
            server_url=self.config["velociraptor"]["server_url"],
            api_key=self.config["velociraptor"]["api_key"],
            cert_path=self.config["velociraptor"]["cert_path"]
        )
        
        self.scanner = HunterMatrixScanner(
            db_path=self.config["huntermatrix"]["db_path"]
        )
        
        self.hunter = ThreatHunter(self.velo_api, self.scanner)
        
        # Start Service
        tasks = []
        
        if self.config["hunting"]["enabled"]:
            tasks.append(
                asyncio.create_task(
                    self.hunter.continuous_hunt(
                        interval=self.config["hunting"]["interval"]
                    )
                )
            )
        
        try:
            async with self.velo_api:
                await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 ServiceStop")
        except Exception as e:
            logger.error(f"Service Runtime Error: {e}")

async def main():
    """Main Function"""
    service = VelociraptorHunterMatrixService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
