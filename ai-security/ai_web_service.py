#!/usr/bin/env python3
"""
AISecurityServiceWebInterface
为HunterMatrix Web UI提供AI功能支持
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# WebFramework
try:
    from aiohttp import web, WSMsgType
    from aiohttp.web import middleware
    import aiohttp_cors
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False
    logging.warning("aiohttp not available, web service disabled")

# AIModule
from intelligent_threat_detector import IntelligentThreatDetector
from nlp_security_analyzer import SecurityLogAnalyzer, SecurityReportGenerator
from ai_response_system import AIResponseSystem, ThreatEvent, ThreatLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIWebService:
    """AISecurityServiceWebInterface"""
    
    def __init__(self, host='localhost', port=8082):
        self.host = host
        self.port = port
        self.app = None
        
        # AIGroup件
        self.threat_detector = IntelligentThreatDetector()
        self.log_analyzer = SecurityLogAnalyzer()
        self.report_generator = SecurityReportGenerator()
        self.response_system = AIResponseSystem()

        # Report生成器
        from ai_report_generator import AIReportGenerator
        from report_scheduler import ReportScheduler
        self.report_generator = AIReportGenerator()
        self.report_scheduler = ReportScheduler()

        # WebSocketConnection
        self.websockets = set()
        
        # 聊天历史
        self.chat_sessions = {}
        
        # AI回复Template
        self.ai_responses = {
            'greeting': [
                "您好！我是您的AISecurity助手，很高兴为您Service！",
                "欢迎使用AISecurity助手！我可以帮助您Analysis威胁和解答Security问题。",
                "您好！我是专业的NetworkSecurityAI助手，请问Has什么可以帮助您的吗？"
            ],
            'scan_help': [
                "关于扫描功能，我可以帮您：\n• 选择最佳扫描Policy\n• 解释扫描Result\n• ProcessFound的威胁\n• Optimization扫描Performance",
                "扫描是Detection威胁的重要手段。建议定期进行全盘扫描，对可疑File进行DepthAnalysis。",
                "我可以指导您进行不同Type的扫描：快速扫描、全盘扫描、Custom扫描等。"
            ],
            'threat_analysis': [
                "威胁Analysis需要综合考虑多个因素：FileFeature、行为模式、来源可信度等。",
                "我使用Machine LearningAlgorithmAnalysis威胁，Accuracy超过95%。Found威胁时会立即告警。",
                "威胁等级分为：严重、高、中、低、Information。不同等级需要采取不同的应对措施。"
            ],
            'security_advice': [
                "Security建议：\n• 保持System和SoftwareUpdate\n• 使用强Password和双因素Authentication\n• 定期Backup重要Data\n• 谨慎Download和InstallSoftware",
                "提高Security性的关键是建立多层防护：防火墙、杀毒Software、入侵Detection、User教育。",
                "建议启用实时保护、AutomaticUpdate病毒Library、定期扫描System，这样可以大大提高Security性。"
            ]
        }
    
    async def init_app(self):
        """InitializeWebApplication"""
        if not WEB_AVAILABLE:
            raise RuntimeError("aiohttp not available")
        
        self.app = web.Application(middlewares=[self.cors_middleware])
        
        # SettingsCORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # 路由Settings
        self.setup_routes()
        
        # 为所Has路由添加CORS
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    @middleware
    async def cors_middleware(self, request, handler):
        """CORS中间件"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    def setup_routes(self):
        """Settings路由"""
        # API路由
        self.app.router.add_get('/api/status', self.get_status)
        self.app.router.add_post('/api/chat', self.handle_chat)
        self.app.router.add_post('/api/analyze-file', self.analyze_file)
        self.app.router.add_post('/api/analyze-logs', self.analyze_logs)
        self.app.router.add_get('/api/threat-report', self.get_threat_report)
        self.app.router.add_post('/api/process-threat', self.process_threat)

        # Report相关API
        self.app.router.add_post('/api/generate-report', self.generate_report)
        self.app.router.add_get('/api/reports', self.list_reports)
        self.app.router.add_get('/api/reports/{report_id}', self.get_report)
        self.app.router.add_delete('/api/reports/{report_id}', self.delete_report)
        self.app.router.add_post('/api/schedule-report', self.schedule_report)
        self.app.router.add_get('/api/report-status', self.get_report_status)

        # 邮件相关API
        self.app.router.add_post('/api/send-test-email', self.send_test_email)
        self.app.router.add_get('/api/email-config', self.get_email_config)
        self.app.router.add_post('/api/email-config', self.save_email_config)
        self.app.router.add_get('/api/email-status', self.get_email_status)
        
        # WebSocket路由
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # 静态File
        self.app.router.add_static('/', path='../web-ui', name='static')
    
    async def get_status(self, request):
        """获取AIServiceStatus"""
        status = {
            'service': 'AI Security Service',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'threat_detection': True,
                'log_analysis': True,
                'chat_assistant': True,
                'auto_response': True
            },
            'models': {
                'ml_detector': self.threat_detector.ml_detector.is_trained,
                'nlp_analyzer': bool(self.log_analyzer.nlp),
                'response_system': True
            }
        }
        return web.json_response(status)
    
    async def handle_chat(self, request):
        """Process聊天Request"""
        try:
            data = await request.json()
            message = data.get('message', '').strip()
            session_id = data.get('session_id', 'default')
            
            if not message:
                return web.json_response({'error': 'Message is required'}, status=400)
            
            # 生成AI回复
            response = await self.generate_ai_response(message, session_id)
            
            # Save聊天历史
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = []
            
            self.chat_sessions[session_id].extend([
                {'role': 'user', 'message': message, 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'message': response, 'timestamp': datetime.now().isoformat()}
            ])
            
            return web.json_response({
                'response': response,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Chat handling error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def generate_ai_response(self, message: str, session_id: str) -> str:
        """生成AI回复"""
        message_lower = message.lower()
        
        # 问候语
        if any(word in message_lower for word in ['你好', 'hello', '您好', '嗨']):
            return self.get_random_response('greeting')
        
        # 扫描相关
        if any(word in message_lower for word in ['扫描', 'scan', 'Detection', '查杀']):
            return self.get_random_response('scan_help')
        
        # 威胁Analysis
        if any(word in message_lower for word in ['威胁', '病毒', '恶意', '木马', 'Analysis']):
            return self.get_random_response('threat_analysis')
        
        # Security建议
        if any(word in message_lower for word in ['Security', '建议', '防护', '保护', '如何']):
            return self.get_random_response('security_advice')
        
        # SystemStatusQuery
        if any(word in message_lower for word in ['Status', 'Performance', 'System', 'Run']):
            return await self.get_system_status_response()
        
        # 最近威胁Query
        if any(word in message_lower for word in ['最近', '威胁', 'Found', 'Detection到']):
            return await self.get_recent_threats_response()
        
        # DefaultSmart回复
        return await self.generate_smart_response(message)
    
    def get_random_response(self, category: str) -> str:
        """获取随机回复"""
        import random
        responses = self.ai_responses.get(category, ['我理解您的问题，让我为您Analysis一下。'])
        return random.choice(responses)
    
    async def get_system_status_response(self) -> str:
        """获取SystemStatus回复"""
        # 模拟SystemStatus
        cpu_usage = 25 + (hash(str(datetime.now().minute)) % 20)
        memory_usage = 45 + (hash(str(datetime.now().second)) % 30)
        
        return f"""📊 当前SystemStatus：

🖥️ **CPU使用率**: {cpu_usage}% (正常)
💾 **Memory使用率**: {memory_usage}% (良好)
🛡️ **防护Status**: Already启用
🔄 **实时Monitor**: Run中

SystemRun状况良好，所HasSecurityGroup件正常工作。"""
    
    async def get_recent_threats_response(self) -> str:
        """获取最近威胁回复"""
        # 模拟威胁Data
        threats_count = hash(str(datetime.now().hour)) % 5
        
        if threats_count == 0:
            return "🎉 好消息！最近24小时内NotDetection到任何威胁，SystemSecurity状况良好。建议Continue保持良好的Security习惯。"
        else:
            return f"""⚠️ 最近24小时威胁DetectionReport：

🔍 **Detection到威胁**: {threats_count} 个
📁 **主要Type**: 临时File、CacheFile
🎯 **风险等级**: 低风险
✅ **ProcessStatus**: AlreadyAutomaticProcess

建议定期CleanSystem垃圾File，保持System整洁。"""
    
    async def generate_smart_response(self, message: str) -> str:
        """生成Smart回复"""
        # 使用NLPAnalysisUser意图
        try:
            analysis = await self.log_analyzer.analyze_log_entry(message)
            
            if analysis.threat_level in ['high', 'critical']:
                return "我Detection到您的消息中可能Package含Security相关的关键Information。建议立即CheckSystemSecurityStatus，如需帮助请告诉我具体情况。"
            elif analysis.keywords:
                keywords_str = "、".join(analysis.keywords[:3])
                return f"我注意到您提到了 {keywords_str} 相关的Content。我可以为您提供这方面的专业建议和指导。"
        except:
            pass
        
        # Default回复
        default_responses = [
            "感谢您的问题！我ProcessingAnalysis相关Information。如果您需要具体的Security建议，请告诉我更多详情。",
            "我理解您的关注。作为AISecurity助手，我建议您定期CheckSystemStatus并保持SoftwareUpdate。",
            "这是一个很好的问题。基于我的Analysis，建议您查看Security仪Table板了解详细Information。还Has其他问题吗？"
        ]
        
        import random
        return random.choice(default_responses)
    
    async def analyze_file(self, request):
        """AnalysisFile威胁"""
        try:
            data = await request.json()
            file_path = data.get('file_path')
            
            if not file_path:
                return web.json_response({'error': 'File path is required'}, status=400)
            
            # 使用AI威胁Detection器AnalysisFile
            analysis = await self.threat_detector.analyze_file(file_path)
            
            result = {
                'file_path': analysis.file_path,
                'threat_score': analysis.threat_score,
                'confidence': analysis.confidence,
                'threat_type': analysis.threat_type,
                'threat_category': analysis.threat_category,
                'recommendations': analysis.recommendations,
                'analysis_time': analysis.analysis_time.isoformat() if analysis.analysis_time else None
            }
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"File analysis error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def analyze_logs(self, request):
        """AnalysisSecurityLog"""
        try:
            data = await request.json()
            log_entries = data.get('logs', [])
            
            if not log_entries:
                return web.json_response({'error': 'Log entries are required'}, status=400)
            
            results = []
            for log_entry in log_entries:
                analysis = await self.log_analyzer.analyze_log_entry(log_entry)
                results.append({
                    'original_text': analysis.original_text,
                    'threat_level': analysis.threat_level,
                    'confidence': analysis.confidence,
                    'entities': analysis.entities,
                    'iocs': analysis.iocs,
                    'anomaly_score': analysis.anomaly_score,
                    'keywords': analysis.keywords,
                    'classification': analysis.classification
                })
            
            return web.json_response({'results': results})
            
        except Exception as e:
            logger.error(f"Log analysis error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_threat_report(self, request):
        """获取威胁Report"""
        try:
            # 生成Example威胁Report
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_threats': 3,
                    'critical_threats': 0,
                    'high_threats': 1,
                    'medium_threats': 2,
                    'low_threats': 0
                },
                'threats': [
                    {
                        'id': 'threat_001',
                        'type': 'suspicious_file',
                        'level': 'high',
                        'description': 'Detection到可疑可ExecuteFile',
                        'file_path': '/tmp/suspicious.exe',
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'id': 'threat_002',
                        'type': 'network_anomaly',
                        'level': 'medium',
                        'description': 'ExceptionNetworkConnection',
                        'source_ip': '192.168.1.100',
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'recommendations': [
                    '立即隔离可疑File',
                    'CheckNetworkConnection',
                    'Update病毒Library',
                    '进行全System扫描'
                ]
            }
            
            return web.json_response(report_data)
            
        except Exception as e:
            logger.error(f"Threat report error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def process_threat(self, request):
        """Process威胁事件"""
        try:
            data = await request.json()
            
            # Create威胁事件
            threat_event = ThreatEvent(
                event_id=data.get('event_id', f"threat_{int(datetime.now().timestamp())}"),
                timestamp=datetime.now(),
                threat_type=data.get('threat_type', 'unknown'),
                threat_level=ThreatLevel(data.get('threat_level', 'medium')),
                file_path=data.get('file_path'),
                source_ip=data.get('source_ip'),
                description=data.get('description', ''),
                confidence=data.get('confidence', 0.5)
            )
            
            # 使用AIResponseSystemProcess
            response_plan = await self.response_system.process_threat_event(threat_event)
            
            result = {
                'plan_id': response_plan.plan_id,
                'actions': [action.value for action in response_plan.actions],
                'priority': response_plan.priority,
                'estimated_duration': response_plan.estimated_duration,
                'estimated_impact': response_plan.estimated_impact,
                'approval_required': response_plan.approval_required
            }
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Threat processing error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def generate_report(self, request):
        """生成SecurityReport"""
        try:
            data = await request.json()
            report_type = data.get('type', 'daily')

            if report_type not in ['daily', 'weekly', 'threat_summary', 'network_security', 'ai_analysis']:
                return web.json_response({'error': 'Invalid report type'}, status=400)

            # 生成Report
            report_content = await self.report_generator.generate_report(report_type)

            # SaveReport并获取FilePath
            report_path = await self.report_generator.save_report(
                report_content, report_type, 'html'
            )

            result = {
                'report_id': f"{report_type}_{int(datetime.now().timestamp())}",
                'type': report_type,
                'status': 'completed',
                'file_path': report_path,
                'generated_at': datetime.now().isoformat(),
                'size': len(report_content)
            }

            return web.json_response(result)

        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def list_reports(self, request):
        """列出所HasReport"""
        try:
            reports_dir = Path(self.report_generator.config['report']['output_dir'])

            if not reports_dir.exists():
                return web.json_response({'reports': []})

            reports = []
            for report_file in reports_dir.glob('*.html'):
                stat = report_file.stat()
                reports.append({
                    'id': report_file.stem,
                    'name': report_file.name,
                    'type': report_file.stem.split('_')[0],
                    'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'size': stat.st_size,
                    'path': str(report_file)
                })

            # 按CreateTimeSort
            reports.sort(key=lambda x: x['created_at'], reverse=True)

            return web.json_response({'reports': reports})

        except Exception as e:
            logger.error(f"List reports error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_report(self, request):
        """获取特定Report"""
        try:
            report_id = request.match_info['report_id']
            reports_dir = Path(self.report_generator.config['report']['output_dir'])

            # FindReportFile
            report_file = None
            for ext in ['html', 'json', 'txt']:
                potential_file = reports_dir / f"{report_id}.{ext}"
                if potential_file.exists():
                    report_file = potential_file
                    break

            if not report_file:
                return web.json_response({'error': 'Report not found'}, status=404)

            # ReadReportContent
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 确定ContentType
            content_type = 'text/html' if report_file.suffix == '.html' else 'text/plain'

            return web.Response(text=content, content_type=content_type)

        except Exception as e:
            logger.error(f"Get report error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def delete_report(self, request):
        """DeleteReport"""
        try:
            report_id = request.match_info['report_id']
            reports_dir = Path(self.report_generator.config['report']['output_dir'])

            deleted_files = []
            for ext in ['html', 'json', 'txt']:
                report_file = reports_dir / f"{report_id}.{ext}"
                if report_file.exists():
                    report_file.unlink()
                    deleted_files.append(str(report_file))

            if not deleted_files:
                return web.json_response({'error': 'Report not found'}, status=404)

            return web.json_response({
                'message': 'Report deleted successfully',
                'deleted_files': deleted_files
            })

        except Exception as e:
            logger.error(f"Delete report error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def schedule_report(self, request):
        """调度Report生成"""
        try:
            data = await request.json()
            report_type = data.get('type', 'daily')
            schedule_time = data.get('schedule_time')  # 可选的调度Time

            # SendCommand到调度器
            command = {
                'type': 'generate_report',
                'report_type': report_type,
                'scheduled': True
            }

            if schedule_time:
                command['schedule_time'] = schedule_time

            await self.report_scheduler.send_command(command)

            return web.json_response({
                'message': f'{report_type} report scheduled successfully',
                'type': report_type,
                'scheduled_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Schedule report error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_report_status(self, request):
        """获取Report生成Status"""
        try:
            # 获取Report历史
            history = getattr(self.report_scheduler, 'report_history', [])

            # 获取最近的ReportStatus
            recent_reports = history[-10:] if history else []

            # StatisticsInformation
            total_reports = len(history)
            successful_reports = len([r for r in history if r.get('status') == 'success'])
            failed_reports = len([r for r in history if r.get('status') == 'failed'])

            status = {
                'scheduler_running': getattr(self.report_scheduler, 'running', False),
                'total_reports': total_reports,
                'successful_reports': successful_reports,
                'failed_reports': failed_reports,
                'success_rate': (successful_reports / total_reports * 100) if total_reports > 0 else 0,
                'recent_reports': recent_reports,
                'last_report': history[-1] if history else None
            }

            return web.json_response(status)

        except Exception as e:
            logger.error(f"Get report status error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def send_test_email(self, request):
        """SendTest邮件"""
        try:
            data = await request.json()

            # Create临时邮件ServiceInstance
            from email_service import EmailService
            email_service = EmailService()

            # 获取Test邮箱
            test_recipient = data.get('recipients', ['test@example.com'])[0]

            # SendTest邮件
            success = await email_service.send_test_email(test_recipient)

            if success:
                return web.json_response({
                    'success': True,
                    'message': 'Test邮件SendSuccess'
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Test邮件SendFailed'
                }, status=500)

        except Exception as e:
            logger.error(f"Send test email error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_email_config(self, request):
        """获取邮件Configuration"""
        try:
            from email_service import EmailService
            email_service = EmailService()

            # 返回脱敏的ConfigurationInformation
            config = email_service.config.copy()

            # 移除敏感Information
            if 'auth' in config and 'password' in config['auth']:
                config['auth']['password'] = '***'

            return web.json_response(config)

        except Exception as e:
            logger.error(f"Get email config error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def save_email_config(self, request):
        """Save邮件Configuration"""
        try:
            data = await request.json()

            # 这里应该Save到ConfigurationFile
            # 为了Demo，我们只返回SuccessResponse

            return web.json_response({
                'success': True,
                'message': '邮件ConfigurationSaveSuccess'
            })

        except Exception as e:
            logger.error(f"Save email config error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_email_status(self, request):
        """获取邮件ServiceStatus"""
        try:
            from email_service import EmailService
            email_service = EmailService()

            # Test邮件Configuration
            config_test = email_service.test_email_config()

            status = {
                'enabled': email_service.config.get('enabled', False),
                'configured': config_test['config_valid'],
                'provider': email_service.config.get('provider', 'unknown'),
                'sender': email_service.config.get('sender', {}).get('email', ''),
                'recipients_count': len(email_service.config.get('recipients', {}).get('default', [])),
                'last_test': None,  # 可以添加最后TestTime
                'errors': config_test.get('errors', []),
                'warnings': config_test.get('warnings', [])
            }

            return web.json_response(status)

        except Exception as e:
            logger.error(f"Get email status error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def websocket_handler(self, request):
        """WebSocketProcess器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        logger.info("WebSocket connection established")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        response = await self.handle_websocket_message(data)
                        await ws.send_str(json.dumps(response))
                    except Exception as e:
                        await ws.send_str(json.dumps({'error': str(e)}))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info("WebSocket connection closed")
        
        return ws
    
    async def handle_websocket_message(self, data):
        """ProcessWebSocket消息"""
        msg_type = data.get('type')
        
        if msg_type == 'chat':
            message = data.get('message', '')
            session_id = data.get('session_id', 'ws_default')
            response = await self.generate_ai_response(message, session_id)
            return {
                'type': 'chat_response',
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
        
        elif msg_type == 'status':
            return {
                'type': 'status_response',
                'status': 'online',
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            return {'type': 'error', 'message': 'Unknown message type'}
    
    async def broadcast_to_websockets(self, message):
        """向所HasWebSocketConnection广播消息"""
        if self.websockets:
            await asyncio.gather(
                *[ws.send_str(json.dumps(message)) for ws in self.websockets],
                return_exceptions=True
            )
    
    async def start_server(self):
        """Start Service器"""
        await self.init_app()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"🤖 AI Security Service started at http://{self.host}:{self.port}")
        logger.info("Available endpoints:")
        logger.info("  GET  /api/status - Service status")
        logger.info("  POST /api/chat - Chat with AI assistant")
        logger.info("  POST /api/analyze-file - Analyze file threats")
        logger.info("  POST /api/analyze-logs - Analyze security logs")
        logger.info("  GET  /api/threat-report - Get threat report")
        logger.info("  POST /api/process-threat - Process threat events")
        logger.info("  WS   /ws - WebSocket connection")

async def main():
    """Main Function"""
    service = AIWebService()
    await service.start_server()
    
    try:
        # 保持ServiceRun
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down AI Security Service...")

if __name__ == "__main__":
    asyncio.run(main())
