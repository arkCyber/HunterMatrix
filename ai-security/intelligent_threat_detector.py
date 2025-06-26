#!/usr/bin/env python3
"""
Smart威胁Detection引擎
使用Machine Learning和Depth学习技术进行高级威胁Detection
"""

import asyncio
import numpy as np
import pandas as pd
import joblib
import hashlib
import magic
import pefile
import yara
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# Machine LearningLibrary
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb

# Depth学习Library
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoTokenizer, AutoModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available, deep learning features disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThreatAnalysis:
    """威胁AnalysisResult"""
    file_path: str
    threat_score: float
    confidence: float
    threat_type: str
    threat_category: str
    ml_predictions: Dict[str, float]
    dl_predictions: Dict[str, float] = None
    features: Dict[str, Any] = None
    recommendations: List[str] = None
    analysis_time: datetime = None

class FileFeatureExtractor:
    """FileFeature提取器"""
    
    def __init__(self):
        self.magic = magic.Magic()
        self.yara_rules = self.load_yara_rules()
    
    def load_yara_rules(self) -> Optional[yara.Rules]:
        """LoadYARARules"""
        try:
            # 这里应该Load实际的YARARulesFile
            # 为了Demo，我们Create一个简单的Rules
            rule_text = '''
            rule SuspiciousStrings {
                strings:
                    $s1 = "CreateRemoteThread"
                    $s2 = "VirtualAllocEx"
                    $s3 = "WriteProcessMemory"
                    $s4 = "SetWindowsHookEx"
                meta:
                    description = "Suspicious API calls"
                condition:
                    any of them
            }
            '''
            return yara.compile(source=rule_text)
        except Exception as e:
            logger.warning(f"Failed to load YARA rules: {e}")
            return None
    
    def extract_basic_features(self, file_path: str) -> Dict[str, Any]:
        """提取基础FileFeature"""
        features = {}
        
        try:
            # File基本Information
            stat = os.stat(file_path)
            features['file_size'] = stat.st_size
            features['creation_time'] = stat.st_ctime
            features['modification_time'] = stat.st_mtime
            
            # FileType
            features['file_type'] = self.magic.from_file(file_path)
            
            # File扩展名
            features['file_extension'] = Path(file_path).suffix.lower()
            
            # File哈希
            with open(file_path, 'rb') as f:
                content = f.read()
                features['md5'] = hashlib.md5(content).hexdigest()
                features['sha1'] = hashlib.sha1(content).hexdigest()
                features['sha256'] = hashlib.sha256(content).hexdigest()
            
            # File熵值 (随机性度量)
            features['entropy'] = self.calculate_entropy(content)
            
            # Character串Feature
            features.update(self.extract_string_features(content))
            
        except Exception as e:
            logger.error(f"Error extracting basic features from {file_path}: {e}")
            
        return features
    
    def extract_pe_features(self, file_path: str) -> Dict[str, Any]:
        """提取PEFileFeature"""
        features = {}
        
        try:
            pe = pefile.PE(file_path)
            
            # PE头Information
            features['pe_machine'] = pe.FILE_HEADER.Machine
            features['pe_characteristics'] = pe.FILE_HEADER.Characteristics
            features['pe_subsystem'] = pe.OPTIONAL_HEADER.Subsystem
            features['pe_dll_characteristics'] = pe.OPTIONAL_HEADER.DllCharacteristics
            
            # 节Information
            features['pe_number_of_sections'] = pe.FILE_HEADER.NumberOfSections
            features['pe_size_of_code'] = pe.OPTIONAL_HEADER.SizeOfCode
            features['pe_size_of_initialized_data'] = pe.OPTIONAL_HEADER.SizeOfInitializedData
            
            # ImportTable
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                imports = []
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    dll_name = entry.dll.decode('utf-8', errors='ignore')
                    imports.append(dll_name)
                    for imp in entry.imports:
                        if imp.name:
                            imports.append(imp.name.decode('utf-8', errors='ignore'))
                
                features['pe_imports'] = imports
                features['pe_import_count'] = len(imports)
            
            # ExportTable
            if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
                exports = []
                for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                    if exp.name:
                        exports.append(exp.name.decode('utf-8', errors='ignore'))
                features['pe_exports'] = exports
                features['pe_export_count'] = len(exports)
            
            pe.close()
            
        except Exception as e:
            logger.warning(f"Failed to extract PE features from {file_path}: {e}")
            
        return features
    
    def extract_yara_features(self, file_path: str) -> Dict[str, Any]:
        """提取YARAMatchFeature"""
        features = {}
        
        if self.yara_rules:
            try:
                matches = self.yara_rules.match(file_path)
                features['yara_matches'] = [match.rule for match in matches]
                features['yara_match_count'] = len(matches)
            except Exception as e:
                logger.warning(f"YARA matching failed for {file_path}: {e}")
                features['yara_matches'] = []
                features['yara_match_count'] = 0
        else:
            features['yara_matches'] = []
            features['yara_match_count'] = 0
            
        return features
    
    def calculate_entropy(self, data: bytes) -> float:
        """CalculateData熵值"""
        if not data:
            return 0.0
        
        # Calculate字节频率
        byte_counts = np.bincount(data, minlength=256)
        probabilities = byte_counts / len(data)
        
        # Calculate熵
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return entropy
    
    def extract_string_features(self, content: bytes) -> Dict[str, Any]:
        """提取Character串Feature"""
        features = {}
        
        try:
            # 可打印Character串
            printable_strings = []
            current_string = ""
            
            for byte in content:
                if 32 <= byte <= 126:  # 可打印ASCIICharacter
                    current_string += chr(byte)
                else:
                    if len(current_string) >= 4:  # 最小Character串Length
                        printable_strings.append(current_string)
                    current_string = ""
            
            if len(current_string) >= 4:
                printable_strings.append(current_string)
            
            features['string_count'] = len(printable_strings)
            features['avg_string_length'] = np.mean([len(s) for s in printable_strings]) if printable_strings else 0
            features['max_string_length'] = max([len(s) for s in printable_strings]) if printable_strings else 0
            
            # 可疑Character串模式
            suspicious_patterns = [
                'CreateRemoteThread', 'VirtualAllocEx', 'WriteProcessMemory',
                'SetWindowsHookEx', 'GetProcAddress', 'LoadLibrary',
                'RegSetValueEx', 'CreateFile', 'InternetOpen'
            ]
            
            features['suspicious_string_count'] = sum(
                1 for pattern in suspicious_patterns 
                for string in printable_strings 
                if pattern.lower() in string.lower()
            )
            
        except Exception as e:
            logger.warning(f"String feature extraction failed: {e}")
            features.update({
                'string_count': 0,
                'avg_string_length': 0,
                'max_string_length': 0,
                'suspicious_string_count': 0
            })
        
        return features
    
    def extract_all_features(self, file_path: str) -> Dict[str, Any]:
        """提取所HasFeature"""
        features = {}
        
        # 基础Feature
        features.update(self.extract_basic_features(file_path))
        
        # PEFeature (如果是PEFile)
        if features.get('file_extension') in ['.exe', '.dll', '.sys']:
            features.update(self.extract_pe_features(file_path))
        
        # YARAFeature
        features.update(self.extract_yara_features(file_path))
        
        return features

class MLThreatDetector:
    """Machine Learning威胁Detection器"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.feature_extractor = FileFeatureExtractor()
        self.scaler = StandardScaler()
        
        # Model字典
        self.models = {
            'malware_classifier': RandomForestClassifier(n_estimators=100, random_state=42),
            'anomaly_detector': IsolationForest(contamination=0.1, random_state=42),
            'threat_scorer': xgb.XGBRegressor(random_state=42)
        }
        
        self.is_trained = False
        self.feature_names = []
    
    def prepare_features(self, features_dict: Dict[str, Any]) -> np.ndarray:
        """准备Machine LearningFeature"""
        # 选择数值Feature
        numerical_features = [
            'file_size', 'entropy', 'string_count', 'avg_string_length',
            'max_string_length', 'suspicious_string_count', 'yara_match_count'
        ]
        
        # PEFeature
        pe_features = [
            'pe_machine', 'pe_characteristics', 'pe_subsystem',
            'pe_dll_characteristics', 'pe_number_of_sections',
            'pe_size_of_code', 'pe_size_of_initialized_data',
            'pe_import_count', 'pe_export_count'
        ]
        
        # Group合Feature
        selected_features = numerical_features + pe_features
        
        # 提取Feature值
        feature_vector = []
        for feature_name in selected_features:
            value = features_dict.get(feature_name, 0)
            if isinstance(value, (int, float)):
                feature_vector.append(value)
            else:
                feature_vector.append(0)  # Default值
        
        return np.array(feature_vector).reshape(1, -1)
    
    def train_models(self, training_data: List[Tuple[str, int]]):
        """TrainingMachine LearningModel"""
        logger.info("StartTrainingMachine LearningModel...")
        
        # 提取Feature和Tag
        X = []
        y = []
        
        for file_path, label in training_data:
            try:
                features = self.feature_extractor.extract_all_features(file_path)
                feature_vector = self.prepare_features(features)
                X.append(feature_vector.flatten())
                y.append(label)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")
        
        if not X:
            logger.error("No valid training data")
            return
        
        X = np.array(X)
        y = np.array(y)
        
        # Standard化Feature
        X_scaled = self.scaler.fit_transform(X)
        
        # 分割Training和TestData
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # TrainingModel
        self.models['malware_classifier'].fit(X_train, y_train)
        self.models['anomaly_detector'].fit(X_train[y_train == 0])  # 只用正常SampleTraining
        
        # 为威胁评分器Create连续Tag
        threat_scores = np.random.random(len(y_train))  # 这里应该是实际的威胁评分
        self.models['threat_scorer'].fit(X_train, threat_scores)
        
        # EvaluationModel
        y_pred = self.models['malware_classifier'].predict(X_test)
        logger.info(f"ModelAccuracy: {np.mean(y_pred == y_test):.3f}")
        
        self.is_trained = True
        
        # SaveModel
        self.save_models()
    
    def predict(self, file_path: str) -> Dict[str, float]:
        """使用MLModel进行Prediction"""
        if not self.is_trained:
            self.load_models()
        
        try:
            # 提取Feature
            features = self.feature_extractor.extract_all_features(file_path)
            feature_vector = self.prepare_features(features)
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # ModelPrediction
            predictions = {}
            
            # 恶意Software分Class
            malware_prob = self.models['malware_classifier'].predict_proba(feature_vector_scaled)[0]
            predictions['malware_probability'] = float(malware_prob[1]) if len(malware_prob) > 1 else 0.0
            
            # ExceptionDetection
            anomaly_score = self.models['anomaly_detector'].decision_function(feature_vector_scaled)[0]
            predictions['anomaly_score'] = float(anomaly_score)
            
            # 威胁评分
            threat_score = self.models['threat_scorer'].predict(feature_vector_scaled)[0]
            predictions['threat_score'] = float(threat_score)
            
            return predictions
            
        except Exception as e:
            logger.error(f"ML prediction failed for {file_path}: {e}")
            return {
                'malware_probability': 0.0,
                'anomaly_score': 0.0,
                'threat_score': 0.0
            }
    
    def save_models(self):
        """SaveTraining好的Model"""
        try:
            for name, model in self.models.items():
                model_path = self.model_dir / f"{name}.joblib"
                joblib.dump(model, model_path)
            
            # SaveStandard化器
            scaler_path = self.model_dir / "scaler.joblib"
            joblib.dump(self.scaler, scaler_path)
            
            logger.info(f"ModelAlreadySave到 {self.model_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def load_models(self):
        """Load预TrainingModel"""
        try:
            for name in self.models.keys():
                model_path = self.model_dir / f"{name}.joblib"
                if model_path.exists():
                    self.models[name] = joblib.load(model_path)
            
            # LoadStandard化器
            scaler_path = self.model_dir / "scaler.joblib"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            
            self.is_trained = True
            logger.info("ModelLoadSuccess")
            
        except Exception as e:
            logger.warning(f"Failed to load models: {e}")
            self.is_trained = False

class IntelligentThreatDetector:
    """Smart威胁Detection引擎主Class"""
    
    def __init__(self, model_dir: str = "models"):
        self.ml_detector = MLThreatDetector(model_dir)
        self.feature_extractor = FileFeatureExtractor()
        
        # 威胁Type映射
        self.threat_types = {
            'trojan': '木马',
            'virus': '病毒',
            'worm': '蠕虫',
            'adware': '广告Software',
            'spyware': '间谍Software',
            'ransomware': '勒索Software',
            'rootkit': '根套件',
            'backdoor': '后门',
            'unknown': 'Not知威胁'
        }
    
    async def analyze_file(self, file_path: str) -> ThreatAnalysis:
        """综合AnalysisFile威胁"""
        start_time = datetime.now()
        
        try:
            # 提取Feature
            features = self.feature_extractor.extract_all_features(file_path)
            
            # MLPrediction
            ml_predictions = self.ml_detector.predict(file_path)
            
            # Calculate综合威胁评分
            threat_score = self.calculate_threat_score(ml_predictions, features)
            
            # 确定威胁Type
            threat_type = self.determine_threat_type(features, ml_predictions)
            
            # Calculate置信度
            confidence = self.calculate_confidence(ml_predictions)
            
            # 生成建议
            recommendations = self.generate_recommendations(threat_score, threat_type)
            
            return ThreatAnalysis(
                file_path=file_path,
                threat_score=threat_score,
                confidence=confidence,
                threat_type=threat_type,
                threat_category=self.categorize_threat(threat_score),
                ml_predictions=ml_predictions,
                features=features,
                recommendations=recommendations,
                analysis_time=start_time
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {e}")
            return ThreatAnalysis(
                file_path=file_path,
                threat_score=0.0,
                confidence=0.0,
                threat_type="error",
                threat_category="unknown",
                ml_predictions={},
                analysis_time=start_time
            )
    
    def calculate_threat_score(self, ml_predictions: Dict[str, float], 
                             features: Dict[str, Any]) -> float:
        """Calculate综合威胁评分"""
        # 权重Configuration
        weights = {
            'malware_probability': 0.4,
            'anomaly_score': 0.3,
            'threat_score': 0.2,
            'yara_matches': 0.1
        }
        
        # 基础评分
        score = 0.0
        
        # MLModel评分
        score += ml_predictions.get('malware_probability', 0) * weights['malware_probability']
        
        # Exception评分 (转换为0-1范围)
        anomaly_score = ml_predictions.get('anomaly_score', 0)
        normalized_anomaly = max(0, min(1, (anomaly_score + 1) / 2))
        score += normalized_anomaly * weights['anomaly_score']
        
        # 威胁评分
        score += ml_predictions.get('threat_score', 0) * weights['threat_score']
        
        # YARAMatch加分
        yara_matches = features.get('yara_match_count', 0)
        if yara_matches > 0:
            score += min(1.0, yara_matches * 0.2) * weights['yara_matches']
        
        return min(1.0, score)
    
    def determine_threat_type(self, features: Dict[str, Any], 
                            ml_predictions: Dict[str, float]) -> str:
        """确定威胁Type"""
        # 基于Feature和PredictionResult确定威胁Type
        yara_matches = features.get('yara_matches', [])
        
        # 基于YARARulesMatch
        if yara_matches:
            return 'trojan'  # 简化实现
        
        # 基于FileFeature
        file_extension = features.get('file_extension', '')
        if file_extension in ['.exe', '.dll']:
            if ml_predictions.get('malware_probability', 0) > 0.7:
                return 'trojan'
        
        # 基于可疑Character串
        suspicious_count = features.get('suspicious_string_count', 0)
        if suspicious_count > 3:
            return 'backdoor'
        
        return 'unknown'
    
    def calculate_confidence(self, ml_predictions: Dict[str, float]) -> float:
        """CalculatePrediction置信度"""
        # 基于多个Model的一致性Calculate置信度
        scores = list(ml_predictions.values())
        if not scores:
            return 0.0
        
        # Calculate方差，方差越小置信度越高
        variance = np.var(scores)
        confidence = 1.0 / (1.0 + variance)
        
        return min(1.0, confidence)
    
    def categorize_threat(self, threat_score: float) -> str:
        """威胁等级分Class"""
        if threat_score >= 0.8:
            return "critical"
        elif threat_score >= 0.6:
            return "high"
        elif threat_score >= 0.4:
            return "medium"
        elif threat_score >= 0.2:
            return "low"
        else:
            return "safe"
    
    def generate_recommendations(self, threat_score: float, threat_type: str) -> List[str]:
        """生成Process建议"""
        recommendations = []
        
        if threat_score >= 0.8:
            recommendations.extend([
                "立即隔离该File",
                "断开NetworkConnection",
                "Execute全System扫描",
                "CheckSystemLogException"
            ])
        elif threat_score >= 0.6:
            recommendations.extend([
                "隔离该File进行进一步Analysis",
                "MonitorSystem行为",
                "Update病毒Library"
            ])
        elif threat_score >= 0.4:
            recommendations.extend([
                "标记为可疑File",
                "定期Monitor",
                "考虑沙箱Analysis"
            ])
        else:
            recommendations.append("ContinueMonitor")
        
        return recommendations

# 使用Example
async def main():
    """Main FunctionExample"""
    detector = IntelligentThreatDetector()
    
    # AnalysisFile
    test_file = "/path/to/test/file.exe"
    if os.path.exists(test_file):
        result = await detector.analyze_file(test_file)
        
        print(f"File: {result.file_path}")
        print(f"威胁评分: {result.threat_score:.3f}")
        print(f"置信度: {result.confidence:.3f}")
        print(f"威胁Type: {result.threat_type}")
        print(f"威胁等级: {result.threat_category}")
        print(f"建议: {', '.join(result.recommendations)}")

if __name__ == "__main__":
    asyncio.run(main())
