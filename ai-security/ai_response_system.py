#!/usr/bin/env python3
"""
AI驱动的Automatic化ResponseSystem
使用Machine Learning和强化学习技术实现SmartSecurityResponse
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# Machine LearningLibrary
try:
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """威胁等级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ResponseAction(Enum):
    """Response动作枚举"""
    QUARANTINE_FILE = "quarantine_file"
    BLOCK_IP = "block_ip"
    KILL_PROCESS = "kill_process"
    ISOLATE_SYSTEM = "isolate_system"
    ALERT_ADMIN = "alert_admin"
    UPDATE_RULES = "update_rules"
    SCAN_SYSTEM = "scan_system"
    BACKUP_DATA = "backup_data"
    MONITOR_ACTIVITY = "monitor_activity"
    NO_ACTION = "no_action"

class ResponseStatus(Enum):
    """ResponseStatus枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ThreatEvent:
    """威胁事件"""
    event_id: str
    timestamp: datetime
    threat_type: str
    threat_level: ThreatLevel
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None
    file_path: Optional[str] = None
    process_name: Optional[str] = None
    user_name: Optional[str] = None
    description: str = ""
    confidence: float = 0.0
    iocs: List[str] = None
    
    def __post_init__(self):
        if self.iocs is None:
            self.iocs = []

@dataclass
class ResponsePlan:
    """Response计划"""
    plan_id: str
    threat_event: ThreatEvent
    actions: List[ResponseAction]
    priority: int
    estimated_duration: int  # 秒
    estimated_impact: str
    approval_required: bool
    created_at: datetime
    
@dataclass
class ResponseExecution:
    """ResponseExecuteRecord"""
    execution_id: str
    plan_id: str
    action: ResponseAction
    status: ResponseStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None

class DecisionEngine:
    """AI决策引擎"""
    
    def __init__(self, model_path: str = "models/decision_model.joblib"):
        self.model_path = model_path
        self.decision_tree = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        
        # 决策Rules权重
        self.rule_weights = {
            'threat_level': 0.4,
            'confidence': 0.3,
            'asset_criticality': 0.2,
            'business_impact': 0.1
        }
        
        self.load_model()
    
    def extract_features(self, threat_event: ThreatEvent) -> np.ndarray:
        """提取威胁事件Feature"""
        features = []
        
        # 威胁等级 (数值化)
        threat_level_map = {
            ThreatLevel.CRITICAL: 5,
            ThreatLevel.HIGH: 4,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.LOW: 2,
            ThreatLevel.INFO: 1
        }
        features.append(threat_level_map.get(threat_event.threat_level, 1))
        
        # 置信度
        features.append(threat_event.confidence)
        
        # TimeFeature (工作Time vs 非工作Time)
        hour = threat_event.timestamp.hour
        is_business_hours = 1 if 9 <= hour <= 17 else 0
        features.append(is_business_hours)
        
        # 威胁TypeFeature
        threat_type_map = {
            'malware': 5,
            'intrusion': 4,
            'data_breach': 4,
            'phishing': 3,
            'suspicious_activity': 2,
            'policy_violation': 1
        }
        features.append(threat_type_map.get(threat_event.threat_type, 1))
        
        # 资产关键性 (基于Path/IP推断)
        asset_criticality = self.assess_asset_criticality(threat_event)
        features.append(asset_criticality)
        
        return np.array(features).reshape(1, -1)
    
    def assess_asset_criticality(self, threat_event: ThreatEvent) -> int:
        """Evaluation资产关键性"""
        criticality = 1  # Default低关键性
        
        # 基于FilePath
        if threat_event.file_path:
            critical_paths = [
                'system32', 'windows', 'program files',
                'database', 'backup', 'config'
            ]
            if any(path in threat_event.file_path.lower() for path in critical_paths):
                criticality = 5
        
        # 基于IP地址
        if threat_event.source_ip or threat_event.target_ip:
            # 内网关键Service器IP段
            critical_ips = ['192.168.1.1', '10.0.0.1']  # Example
            if any(ip in [threat_event.source_ip, threat_event.target_ip] 
                   for ip in critical_ips if ip):
                criticality = 4
        
        # 基于User
        if threat_event.user_name:
            critical_users = ['admin', 'administrator', 'root']
            if threat_event.user_name.lower() in critical_users:
                criticality = 5
        
        return criticality
    
    def make_decision(self, threat_event: ThreatEvent) -> List[ResponseAction]:
        """AI决策制定"""
        if self.is_trained and self.decision_tree:
            # 使用Training好的Model
            features = self.extract_features(threat_event)
            prediction = self.decision_tree.predict(features)[0]
            return self.decode_actions(prediction)
        else:
            # 使用基于Rules的决策
            return self.rule_based_decision(threat_event)
    
    def rule_based_decision(self, threat_event: ThreatEvent) -> List[ResponseAction]:
        """基于Rules的决策"""
        actions = []
        
        # 根据威胁等级决定基础动作
        if threat_event.threat_level == ThreatLevel.CRITICAL:
            actions.extend([
                ResponseAction.QUARANTINE_FILE,
                ResponseAction.ISOLATE_SYSTEM,
                ResponseAction.ALERT_ADMIN,
                ResponseAction.BACKUP_DATA
            ])
        elif threat_event.threat_level == ThreatLevel.HIGH:
            actions.extend([
                ResponseAction.QUARANTINE_FILE,
                ResponseAction.BLOCK_IP,
                ResponseAction.ALERT_ADMIN,
                ResponseAction.SCAN_SYSTEM
            ])
        elif threat_event.threat_level == ThreatLevel.MEDIUM:
            actions.extend([
                ResponseAction.QUARANTINE_FILE,
                ResponseAction.MONITOR_ACTIVITY,
                ResponseAction.UPDATE_RULES
            ])
        elif threat_event.threat_level == ThreatLevel.LOW:
            actions.extend([
                ResponseAction.MONITOR_ACTIVITY,
                ResponseAction.UPDATE_RULES
            ])
        else:  # INFO
            actions.append(ResponseAction.NO_ACTION)
        
        # 根据威胁Type调整动作
        if threat_event.threat_type == 'malware' and threat_event.file_path:
            actions.append(ResponseAction.QUARANTINE_FILE)
        
        if threat_event.source_ip:
            actions.append(ResponseAction.BLOCK_IP)
        
        if threat_event.process_name:
            actions.append(ResponseAction.KILL_PROCESS)
        
        return list(set(actions))  # 去重
    
    def train_model(self, training_data: List[Tuple[ThreatEvent, List[ResponseAction]]]):
        """Training决策Model"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available, using rule-based decisions")
            return
        
        X = []
        y = []
        
        for threat_event, actions in training_data:
            features = self.extract_features(threat_event).flatten()
            action_encoding = self.encode_actions(actions)
            
            X.append(features)
            y.append(action_encoding)
        
        if X and y:
            X = np.array(X)
            y = np.array(y)
            
            self.decision_tree = DecisionTreeClassifier(random_state=42)
            self.decision_tree.fit(X, y)
            
            self.is_trained = True
            self.save_model()
            
            logger.info("Decision model trained successfully")
    
    def encode_actions(self, actions: List[ResponseAction]) -> str:
        """编码动作列Table"""
        return ','.join([action.value for action in actions])
    
    def decode_actions(self, encoded_actions: str) -> List[ResponseAction]:
        """解码动作列Table"""
        if not encoded_actions:
            return [ResponseAction.NO_ACTION]
        
        action_values = encoded_actions.split(',')
        return [ResponseAction(value) for value in action_values if value]
    
    def save_model(self):
        """SaveModel"""
        if self.decision_tree and ML_AVAILABLE:
            try:
                joblib.dump(self.decision_tree, self.model_path)
                logger.info(f"Model saved to {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to save model: {e}")
    
    def load_model(self):
        """LoadModel"""
        try:
            if ML_AVAILABLE:
                self.decision_tree = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("Decision model loaded successfully")
        except Exception as e:
            logger.info("No pre-trained model found, using rule-based decisions")

class ResponseExecutor:
    """ResponseExecute器"""
    
    def __init__(self):
        self.execution_history = []
        
        # 动作Execute器映射
        self.action_executors = {
            ResponseAction.QUARANTINE_FILE: self.quarantine_file,
            ResponseAction.BLOCK_IP: self.block_ip,
            ResponseAction.KILL_PROCESS: self.kill_process,
            ResponseAction.ISOLATE_SYSTEM: self.isolate_system,
            ResponseAction.ALERT_ADMIN: self.alert_admin,
            ResponseAction.UPDATE_RULES: self.update_rules,
            ResponseAction.SCAN_SYSTEM: self.scan_system,
            ResponseAction.BACKUP_DATA: self.backup_data,
            ResponseAction.MONITOR_ACTIVITY: self.monitor_activity,
            ResponseAction.NO_ACTION: self.no_action
        }
    
    async def execute_plan(self, plan: ResponsePlan) -> List[ResponseExecution]:
        """ExecuteResponse计划"""
        executions = []
        
        logger.info(f"StartExecuteResponse计划: {plan.plan_id}")
        
        for action in plan.actions:
            execution = ResponseExecution(
                execution_id=f"exec_{int(time.time())}_{action.value}",
                plan_id=plan.plan_id,
                action=action,
                status=ResponseStatus.PENDING,
                start_time=datetime.now()
            )
            
            try:
                execution.status = ResponseStatus.IN_PROGRESS
                
                # Execute动作
                executor = self.action_executors.get(action)
                if executor:
                    result = await executor(plan.threat_event)
                    execution.result = result
                    execution.status = ResponseStatus.COMPLETED
                else:
                    execution.error_message = f"No executor for action: {action}"
                    execution.status = ResponseStatus.FAILED
                
            except Exception as e:
                execution.error_message = str(e)
                execution.status = ResponseStatus.FAILED
                logger.error(f"Action execution failed: {action} - {e}")
            
            finally:
                execution.end_time = datetime.now()
                executions.append(execution)
                self.execution_history.append(execution)
        
        logger.info(f"Response计划ExecuteComplete: {plan.plan_id}")
        return executions
    
    async def quarantine_file(self, threat_event: ThreatEvent) -> str:
        """隔离File"""
        if not threat_event.file_path:
            return "No file path specified"
        
        try:
            # 模拟File隔离 (实际实现应该移动File到隔离区)
            quarantine_path = f"/quarantine/{threat_event.event_id}_{threat_event.file_path.split('/')[-1]}"
            
            # 这里应该是实际的File移动Operation
            # shutil.move(threat_event.file_path, quarantine_path)
            
            logger.info(f"FileAlready隔离: {threat_event.file_path} -> {quarantine_path}")
            return f"File quarantined to {quarantine_path}"
            
        except Exception as e:
            raise Exception(f"File quarantine failed: {e}")
    
    async def block_ip(self, threat_event: ThreatEvent) -> str:
        """阻断IP地址"""
        ip_to_block = threat_event.source_ip or threat_event.target_ip
        if not ip_to_block:
            return "No IP address specified"
        
        try:
            # 模拟IP阻断 (实际实现应该调用防火墙API)
            # 例如: iptables -A INPUT -s {ip_to_block} -j DROP
            
            logger.info(f"IPAlready阻断: {ip_to_block}")
            return f"IP {ip_to_block} blocked successfully"
            
        except Exception as e:
            raise Exception(f"IP blocking failed: {e}")
    
    async def kill_process(self, threat_event: ThreatEvent) -> str:
        """终止Process"""
        if not threat_event.process_name:
            return "No process name specified"
        
        try:
            # 模拟Process终止
            # 实际实现: subprocess.run(['pkill', threat_event.process_name])
            
            logger.info(f"ProcessAlready终止: {threat_event.process_name}")
            return f"Process {threat_event.process_name} killed successfully"
            
        except Exception as e:
            raise Exception(f"Process termination failed: {e}")
    
    async def isolate_system(self, threat_event: ThreatEvent) -> str:
        """System隔离"""
        try:
            # 模拟System隔离 (断网、限制访问等)
            logger.warning(f"System隔离Already激活: {threat_event.event_id}")
            return "System isolation activated"
            
        except Exception as e:
            raise Exception(f"System isolation failed: {e}")
    
    async def alert_admin(self, threat_event: ThreatEvent) -> str:
        """Administrator告警"""
        try:
            # 模拟Send告警 (邮件、短信、Push等)
            alert_message = f"Security告警: {threat_event.threat_type} - {threat_event.description}"
            
            logger.warning(f"Administrator告警: {alert_message}")
            return "Admin alert sent successfully"
            
        except Exception as e:
            raise Exception(f"Admin alert failed: {e}")
    
    async def update_rules(self, threat_event: ThreatEvent) -> str:
        """UpdateDetectionRules"""
        try:
            # 模拟RulesUpdate
            logger.info(f"DetectionRulesAlreadyUpdate: {threat_event.event_id}")
            return "Detection rules updated successfully"
            
        except Exception as e:
            raise Exception(f"Rule update failed: {e}")
    
    async def scan_system(self, threat_event: ThreatEvent) -> str:
        """System扫描"""
        try:
            # 模拟触发System扫描
            logger.info(f"System扫描AlreadyStart: {threat_event.event_id}")
            return "System scan initiated successfully"
            
        except Exception as e:
            raise Exception(f"System scan failed: {e}")
    
    async def backup_data(self, threat_event: ThreatEvent) -> str:
        """DataBackup"""
        try:
            # 模拟DataBackup
            logger.info(f"DataBackupAlreadyStart: {threat_event.event_id}")
            return "Data backup initiated successfully"
            
        except Exception as e:
            raise Exception(f"Data backup failed: {e}")
    
    async def monitor_activity(self, threat_event: ThreatEvent) -> str:
        """Monitor活动"""
        try:
            # 模拟增强Monitor
            logger.info(f"增强MonitorAlready激活: {threat_event.event_id}")
            return "Enhanced monitoring activated"
            
        except Exception as e:
            raise Exception(f"Activity monitoring failed: {e}")
    
    async def no_action(self, threat_event: ThreatEvent) -> str:
        """No动作"""
        return "No action required"

class AIResponseSystem:
    """AIResponseSystem主Class"""
    
    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.executor = ResponseExecutor()
        self.response_plans = []
        self.active_responses = {}
        
    async def process_threat_event(self, threat_event: ThreatEvent) -> ResponsePlan:
        """Process威胁事件"""
        logger.info(f"Process威胁事件: {threat_event.event_id}")
        
        # AI决策
        recommended_actions = self.decision_engine.make_decision(threat_event)
        
        # CreateResponse计划
        plan = ResponsePlan(
            plan_id=f"plan_{threat_event.event_id}_{int(time.time())}",
            threat_event=threat_event,
            actions=recommended_actions,
            priority=self.calculate_priority(threat_event),
            estimated_duration=self.estimate_duration(recommended_actions),
            estimated_impact=self.estimate_impact(recommended_actions),
            approval_required=self.requires_approval(threat_event, recommended_actions),
            created_at=datetime.now()
        )
        
        self.response_plans.append(plan)
        
        # 如果不需要审批，AutomaticExecute
        if not plan.approval_required:
            await self.execute_response_plan(plan)
        
        return plan
    
    async def execute_response_plan(self, plan: ResponsePlan) -> List[ResponseExecution]:
        """ExecuteResponse计划"""
        self.active_responses[plan.plan_id] = plan
        
        try:
            executions = await self.executor.execute_plan(plan)
            return executions
        finally:
            if plan.plan_id in self.active_responses:
                del self.active_responses[plan.plan_id]
    
    def calculate_priority(self, threat_event: ThreatEvent) -> int:
        """CalculateResponse优先级"""
        priority_map = {
            ThreatLevel.CRITICAL: 1,
            ThreatLevel.HIGH: 2,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.LOW: 4,
            ThreatLevel.INFO: 5
        }
        return priority_map.get(threat_event.threat_level, 5)
    
    def estimate_duration(self, actions: List[ResponseAction]) -> int:
        """估算ExecuteTime"""
        duration_map = {
            ResponseAction.QUARANTINE_FILE: 30,
            ResponseAction.BLOCK_IP: 10,
            ResponseAction.KILL_PROCESS: 5,
            ResponseAction.ISOLATE_SYSTEM: 60,
            ResponseAction.ALERT_ADMIN: 5,
            ResponseAction.UPDATE_RULES: 120,
            ResponseAction.SCAN_SYSTEM: 1800,
            ResponseAction.BACKUP_DATA: 3600,
            ResponseAction.MONITOR_ACTIVITY: 10,
            ResponseAction.NO_ACTION: 0
        }
        
        return sum(duration_map.get(action, 30) for action in actions)
    
    def estimate_impact(self, actions: List[ResponseAction]) -> str:
        """估算业务影响"""
        high_impact_actions = [
            ResponseAction.ISOLATE_SYSTEM,
            ResponseAction.BACKUP_DATA
        ]
        
        if any(action in high_impact_actions for action in actions):
            return "high"
        elif len(actions) > 3:
            return "medium"
        else:
            return "low"
    
    def requires_approval(self, threat_event: ThreatEvent, 
                         actions: List[ResponseAction]) -> bool:
        """判断是否需要审批"""
        # 高影响动作需要审批
        high_impact_actions = [
            ResponseAction.ISOLATE_SYSTEM,
            ResponseAction.BACKUP_DATA
        ]
        
        return any(action in high_impact_actions for action in actions)

# 使用Example
async def main():
    """Main FunctionExample"""
    response_system = AIResponseSystem()
    
    # Create威胁事件
    threat_event = ThreatEvent(
        event_id="threat_001",
        timestamp=datetime.now(),
        threat_type="malware",
        threat_level=ThreatLevel.HIGH,
        file_path="/tmp/suspicious.exe",
        source_ip="192.168.1.100",
        description="Detected malware in downloaded file",
        confidence=0.9
    )
    
    # Process威胁事件
    plan = await response_system.process_threat_event(threat_event)
    
    print(f"Response计划: {plan.plan_id}")
    print(f"推荐动作: {[action.value for action in plan.actions]}")
    print(f"优先级: {plan.priority}")
    print(f"预估Time: {plan.estimated_duration}秒")
    print(f"业务影响: {plan.estimated_impact}")

if __name__ == "__main__":
    asyncio.run(main())
