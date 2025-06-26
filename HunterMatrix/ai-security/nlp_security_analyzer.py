#!/usr/bin/env python3
"""
NLPSecurityAnalysis器
使用自然LanguageProcess技术AnalysisSecurityLog、威胁情报和生成SmartReport
"""

import asyncio
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

# NLPLibrary
try:
    import spacy
    import nltk
    from transformers import pipeline, AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer
    import openai
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    logging.warning("NLP libraries not available, some features disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LogAnalysisResult:
    """LogAnalysisResult"""
    original_text: str
    threat_level: str
    confidence: float
    entities: List[Dict[str, str]]
    iocs: List[str]
    anomaly_score: float
    sentiment: str
    keywords: List[str]
    classification: str

@dataclass
class ThreatIntelligence:
    """威胁情报"""
    ioc_type: str
    ioc_value: str
    threat_type: str
    severity: str
    description: str
    source: str
    confidence: float
    first_seen: datetime
    last_seen: datetime

class IOCExtractor:
    """威胁Metric提取器"""
    
    def __init__(self):
        # 正则Table达式模式
        self.patterns = {
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'domain': r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'md5': r'\b[a-fA-F0-9]{32}\b',
            'sha1': r'\b[a-fA-F0-9]{40}\b',
            'sha256': r'\b[a-fA-F0-9]{64}\b',
            'file_path': r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
            'registry_key': r'HKEY_[A-Z_]+\\[^\\]+(?:\\[^\\]+)*',
            'process_name': r'\b[a-zA-Z0-9_-]+\.exe\b'
        }
    
    def extract_iocs(self, text: str) -> Dict[str, List[str]]:
        """从Text中提取威胁Metric"""
        iocs = {}
        
        for ioc_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # 去重和Clean
                unique_matches = list(set(matches))
                iocs[ioc_type] = unique_matches
        
        return iocs
    
    def validate_iocs(self, iocs: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validation和FilterIOC"""
        validated_iocs = {}
        
        for ioc_type, ioc_list in iocs.items():
            validated_list = []
            
            for ioc in ioc_list:
                if self.is_valid_ioc(ioc_type, ioc):
                    validated_list.append(ioc)
            
            if validated_list:
                validated_iocs[ioc_type] = validated_list
        
        return validated_iocs
    
    def is_valid_ioc(self, ioc_type: str, ioc_value: str) -> bool:
        """ValidationIOC的Has效性"""
        # 基本Validation逻辑
        if ioc_type == 'ip_address':
            parts = ioc_value.split('.')
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False
        
        elif ioc_type == 'domain':
            # 排除常见的误报
            common_domains = ['localhost', 'example.com', 'test.com']
            return ioc_value.lower() not in common_domains
        
        elif ioc_type in ['md5', 'sha1', 'sha256']:
            # Check是否为Has效的哈希值
            return ioc_value.isalnum()
        
        return True

class SecurityLogAnalyzer:
    """SecurityLogAnalysis器"""
    
    def __init__(self):
        self.ioc_extractor = IOCExtractor()
        
        # InitializeNLPModel
        if NLP_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                self.classifier = pipeline("text-classification", 
                                         model="microsoft/DialoGPT-medium")
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Failed to load NLP models: {e}")
                self.nlp = None
        else:
            self.nlp = None
        
        # Security关键词
        self.security_keywords = {
            'attack': ['attack', 'exploit', 'malware', 'virus', 'trojan', 'backdoor'],
            'network': ['connection', 'traffic', 'packet', 'protocol', 'port'],
            'system': ['process', 'service', 'registry', 'file', 'memory'],
            'authentication': ['login', 'password', 'credential', 'token', 'session'],
            'encryption': ['encrypt', 'decrypt', 'certificate', 'key', 'hash']
        }
    
    async def analyze_log_entry(self, log_text: str) -> LogAnalysisResult:
        """Analysis单条Log"""
        try:
            # 提取IOC
            iocs = self.ioc_extractor.extract_iocs(log_text)
            validated_iocs = self.ioc_extractor.validate_iocs(iocs)
            
            # 实体识别
            entities = self.extract_entities(log_text)
            
            # 情感Analysis (威胁程度)
            sentiment_result = self.analyze_sentiment(log_text)
            
            # ExceptionDetection
            anomaly_score = self.detect_anomaly(log_text)
            
            # 关键词提取
            keywords = self.extract_keywords(log_text)
            
            # Log分Class
            classification = self.classify_log(log_text)
            
            # 威胁等级Evaluation
            threat_level = self.assess_threat_level(
                validated_iocs, sentiment_result, anomaly_score
            )
            
            return LogAnalysisResult(
                original_text=log_text,
                threat_level=threat_level,
                confidence=sentiment_result.get('score', 0.0),
                entities=entities,
                iocs=self.flatten_iocs(validated_iocs),
                anomaly_score=anomaly_score,
                sentiment=sentiment_result.get('label', 'NEUTRAL'),
                keywords=keywords,
                classification=classification
            )
            
        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
            return LogAnalysisResult(
                original_text=log_text,
                threat_level="unknown",
                confidence=0.0,
                entities=[],
                iocs=[],
                anomaly_score=0.0,
                sentiment="NEUTRAL",
                keywords=[],
                classification="unknown"
            )
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """提取命名实体"""
        entities = []
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'description': spacy.explain(ent.label_)
                    })
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """AnalysisText情感 (威胁程度)"""
        if hasattr(self, 'sentiment_analyzer') and self.sentiment_analyzer:
            try:
                result = self.sentiment_analyzer(text)[0]
                return result
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
        
        return {'label': 'NEUTRAL', 'score': 0.5}
    
    def detect_anomaly(self, text: str) -> float:
        """DetectionLogException"""
        anomaly_score = 0.0
        
        # 基于Rules的ExceptionDetection
        anomaly_patterns = [
            r'failed.*login',
            r'access.*denied',
            r'suspicious.*activity',
            r'malware.*detected',
            r'unauthorized.*access',
            r'brute.*force',
            r'privilege.*escalation'
        ]
        
        for pattern in anomaly_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                anomaly_score += 0.2
        
        # 基于频率的ExceptionDetection
        if len(text.split()) > 100:  # Exception长的Log
            anomaly_score += 0.1
        
        # 基于Time的ExceptionDetection (简化)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # 非工作Time
            anomaly_score += 0.1
        
        return min(1.0, anomaly_score)
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取Security关键词"""
        keywords = []
        text_lower = text.lower()
        
        for category, word_list in self.security_keywords.items():
            for word in word_list:
                if word in text_lower:
                    keywords.append(word)
        
        return list(set(keywords))
    
    def classify_log(self, text: str) -> str:
        """分ClassLogType"""
        # 简化的Log分Class
        if any(word in text.lower() for word in ['login', 'authentication', 'credential']):
            return 'authentication'
        elif any(word in text.lower() for word in ['network', 'connection', 'traffic']):
            return 'network'
        elif any(word in text.lower() for word in ['file', 'process', 'system']):
            return 'system'
        elif any(word in text.lower() for word in ['malware', 'virus', 'threat']):
            return 'security'
        else:
            return 'general'
    
    def assess_threat_level(self, iocs: Dict[str, List[str]], 
                          sentiment: Dict[str, Any], anomaly_score: float) -> str:
        """Evaluation威胁等级"""
        score = 0.0
        
        # IOC评分
        if iocs:
            score += len(self.flatten_iocs(iocs)) * 0.1
        
        # 情感评分
        if sentiment.get('label') == 'NEGATIVE':
            score += sentiment.get('score', 0) * 0.3
        
        # Exception评分
        score += anomaly_score * 0.4
        
        # 威胁等级映射
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'info'
    
    def flatten_iocs(self, iocs: Dict[str, List[str]]) -> List[str]:
        """扁平化IOC列Table"""
        flattened = []
        for ioc_list in iocs.values():
            flattened.extend(ioc_list)
        return flattened

class ThreatIntelligenceProcessor:
    """威胁情报Process器"""
    
    def __init__(self):
        self.ioc_extractor = IOCExtractor()
        
        # 威胁Type映射
        self.threat_types = {
            'malware': '恶意Software',
            'phishing': '钓鱼攻击',
            'botnet': '僵尸Network',
            'apt': '高级持续威胁',
            'ransomware': '勒索Software',
            'trojan': '木马',
            'backdoor': '后门'
        }
    
    async def process_threat_feed(self, threat_data: str) -> List[ThreatIntelligence]:
        """Process威胁情报源"""
        threat_intel = []
        
        try:
            # 解析威胁Data (False设是JSONFormat)
            if threat_data.strip().startswith('{'):
                data = json.loads(threat_data)
                threat_intel.append(self.parse_json_threat(data))
            else:
                # TextFormat威胁情报
                threat_intel.extend(self.parse_text_threat(threat_data))
        
        except Exception as e:
            logger.error(f"Threat intelligence processing failed: {e}")
        
        return threat_intel
    
    def parse_json_threat(self, data: Dict[str, Any]) -> ThreatIntelligence:
        """解析JSONFormat威胁情报"""
        return ThreatIntelligence(
            ioc_type=data.get('type', 'unknown'),
            ioc_value=data.get('value', ''),
            threat_type=data.get('threat_type', 'unknown'),
            severity=data.get('severity', 'medium'),
            description=data.get('description', ''),
            source=data.get('source', 'unknown'),
            confidence=data.get('confidence', 0.5),
            first_seen=datetime.fromisoformat(data.get('first_seen', datetime.now().isoformat())),
            last_seen=datetime.fromisoformat(data.get('last_seen', datetime.now().isoformat()))
        )
    
    def parse_text_threat(self, text: str) -> List[ThreatIntelligence]:
        """解析TextFormat威胁情报"""
        threat_intel = []
        
        # 提取IOC
        iocs = self.ioc_extractor.extract_iocs(text)
        
        for ioc_type, ioc_list in iocs.items():
            for ioc_value in ioc_list:
                threat_intel.append(ThreatIntelligence(
                    ioc_type=ioc_type,
                    ioc_value=ioc_value,
                    threat_type=self.infer_threat_type(text),
                    severity=self.infer_severity(text),
                    description=text[:200] + "..." if len(text) > 200 else text,
                    source='text_analysis',
                    confidence=0.7,
                    first_seen=datetime.now(),
                    last_seen=datetime.now()
                ))
        
        return threat_intel
    
    def infer_threat_type(self, text: str) -> str:
        """推断威胁Type"""
        text_lower = text.lower()
        
        for threat_type, keywords in {
            'malware': ['malware', 'virus', 'trojan'],
            'phishing': ['phishing', 'fake', 'scam'],
            'botnet': ['botnet', 'c2', 'command'],
            'ransomware': ['ransomware', 'encrypt', 'ransom']
        }.items():
            if any(keyword in text_lower for keyword in keywords):
                return threat_type
        
        return 'unknown'
    
    def infer_severity(self, text: str) -> str:
        """推断威胁严重程度"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'severe', 'high']):
            return 'high'
        elif any(word in text_lower for word in ['medium', 'moderate']):
            return 'medium'
        elif any(word in text_lower for word in ['low', 'minor']):
            return 'low'
        else:
            return 'medium'

class SecurityReportGenerator:
    """SecurityReport生成器"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
    
    async def generate_threat_report(self, analysis_results: List[LogAnalysisResult],
                                   threat_intel: List[ThreatIntelligence]) -> str:
        """生成威胁AnalysisReport"""
        # StatisticsAnalysis
        total_logs = len(analysis_results)
        threat_levels = {}
        classifications = {}
        
        for result in analysis_results:
            threat_levels[result.threat_level] = threat_levels.get(result.threat_level, 0) + 1
            classifications[result.classification] = classifications.get(result.classification, 0) + 1
        
        # 生成Report
        report = f"""
# 🛡️ Security威胁AnalysisReport

## 📊 概览Statistics
- **AnalysisLogTotal**: {total_logs}
- **威胁情报条目**: {len(threat_intel)}
- **生成Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚨 威胁等级分布
"""
        
        for level, count in sorted(threat_levels.items()):
            percentage = (count / total_logs) * 100 if total_logs > 0 else 0
            report += f"- **{level.upper()}**: {count} ({percentage:.1f}%)\n"
        
        report += "\n## 📋 Log分Class分布\n"
        for classification, count in sorted(classifications.items()):
            percentage = (count / total_logs) * 100 if total_logs > 0 else 0
            report += f"- **{classification}**: {count} ({percentage:.1f}%)\n"
        
        # 高威胁事件
        high_threat_events = [r for r in analysis_results if r.threat_level in ['critical', 'high']]
        if high_threat_events:
            report += f"\n## ⚠️ 高威胁事件 ({len(high_threat_events)})\n"
            for event in high_threat_events[:5]:  # 显示前5个
                report += f"- **{event.threat_level.upper()}**: {event.original_text[:100]}...\n"
        
        # IOC汇总
        all_iocs = []
        for result in analysis_results:
            all_iocs.extend(result.iocs)
        
        unique_iocs = list(set(all_iocs))
        if unique_iocs:
            report += f"\n## 🎯 威胁Metric (IOC) - {len(unique_iocs)}\n"
            for ioc in unique_iocs[:10]:  # 显示前10个
                report += f"- `{ioc}`\n"
        
        # 建议措施
        report += "\n## 💡 建议措施\n"
        if threat_levels.get('critical', 0) > 0:
            report += "- 🚨 **立即Response**: Found严重威胁，需要立即Process\n"
        if threat_levels.get('high', 0) > 0:
            report += "- ⚠️ **优先Process**: 高威胁事件需要优先关注\n"
        if len(unique_iocs) > 0:
            report += "- 🎯 **IOCMonitor**: 将威胁Metric加入Monitor列Table\n"
        
        report += "- 🔄 **持续Monitor**: 保持对System的持续Monitor\n"
        report += "- 📚 **UpdateRules**: 根据新Found的威胁UpdateDetectionRules\n"
        
        return report
    
    async def generate_ai_summary(self, report_content: str) -> str:
        """使用AI生成Report摘要"""
        if not self.openai_api_key:
            return "AI摘要功能需要OpenAI APIKey"
        
        try:
            prompt = f"""
            请为以下SecurityReport生成一个简洁的中文摘要，重点突出关键威胁和建议措施：
            
            {report_content}
            
            摘要应该Package括：
            1. 主要威胁Found
            2. 风险等级Evaluation
            3. 关键建议措施
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return "AI摘要生成Failed"

# 使用Example
async def main():
    """Main FunctionExample"""
    analyzer = SecurityLogAnalyzer()
    
    # ExampleLog
    sample_logs = [
        "Failed login attempt from 192.168.1.100 for user admin",
        "Malware detected: trojan.exe in C:\\temp\\suspicious.exe",
        "Suspicious network connection to malicious-domain.com:443",
        "Unauthorized access attempt to registry key HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    ]
    
    # AnalysisLog
    results = []
    for log in sample_logs:
        result = await analyzer.analyze_log_entry(log)
        results.append(result)
        print(f"Log: {log}")
        print(f"威胁等级: {result.threat_level}")
        print(f"IOCs: {result.iocs}")
        print(f"关键词: {result.keywords}")
        print("-" * 50)
    
    # 生成Report
    report_generator = SecurityReportGenerator()
    report = await report_generator.generate_threat_report(results, [])
    print("\n" + report)

if __name__ == "__main__":
    asyncio.run(main())
