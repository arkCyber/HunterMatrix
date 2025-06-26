#!/usr/bin/env python3
"""
AISecurityReport生成Command行Tool
支持Manual生成各种Type的SecurityReport
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime
from pathlib import Path

from ai_report_generator import AIReportGenerator

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 AISecurityReport生成器                       ║
║                                                              ║
║  Smart生成SecurityReport，支持多种Format和Automatic化调度                    ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_report_types():
    """打印支持的ReportType"""
    types = {
        'daily': '📅 每日SecurityReport - Package含当日扫描Statistics、威胁Detection和AIAnalysis',
        'weekly': '📊 周度SecurityReport - 一周内的Security趋势和综合Analysis',
        'threat_summary': '🚨 威胁摘要Report - 当前威胁状况和Process建议',
        'network_security': '🌐 NetworkSecurityReport - Network事件和ConnectionAnalysis',
        'ai_analysis': '🧠 AIDepthAnalysisReport - Machine Learning驱动的DepthSecurityAnalysis'
    }
    
    print("\n📋 支持的ReportType:")
    for key, desc in types.items():
        print(f"  {key:<20} {desc}")

async def generate_single_report(report_type: str, config_path: str, output_format: str):
    """生成单个Report"""
    try:
        print(f"\n🚀 Start生成 {report_type} Report...")
        
        # CreateReport生成器
        generator = AIReportGenerator(config_path)
        
        # 生成Report
        start_time = datetime.now()
        report_content = await generator.generate_report(report_type)
        end_time = datetime.now()
        
        # Calculate生成Time
        generation_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Report生成Complete!")
        print(f"   📊 ReportType: {report_type}")
        print(f"   📝 ContentLength: {len(report_content):,} Character")
        print(f"   ⏱️  生成Time: {generation_time:.2f} 秒")
        
        # 如果指定了OutputFormat，SaveFile
        if output_format:
            file_path = await generator.save_report(report_content, report_type, output_format)
            print(f"   💾 AlreadySave到: {file_path}")
        
        return report_content
        
    except Exception as e:
        print(f"❌ Report生成Failed: {e}")
        return None

async def generate_batch_reports(report_types: list, config_path: str):
    """批量生成Report"""
    print(f"\n🔄 Start批量生成 {len(report_types)} 个Report...")
    
    results = []
    for i, report_type in enumerate(report_types, 1):
        print(f"\n[{i}/{len(report_types)}] 生成 {report_type} Report...")
        
        result = await generate_single_report(report_type, config_path, 'html')
        results.append({
            'type': report_type,
            'success': result is not None,
            'size': len(result) if result else 0
        })
    
    # 打印批量生成Result
    print(f"\n📊 批量生成Complete:")
    successful = sum(1 for r in results if r['success'])
    print(f"   ✅ Success: {successful}/{len(results)}")
    print(f"   ❌ Failed: {len(results) - successful}/{len(results)}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        size = f"({result['size']:,} Character)" if result['success'] else ""
        print(f"   {status} {result['type']} {size}")

async def interactive_mode():
    """交互模式"""
    print("\n🎮 进入交互模式...")
    print("Input 'help' 查看Command，Input 'quit' 退出")
    
    generator = AIReportGenerator()
    
    while True:
        try:
            command = input("\n🤖 AIReport> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                print("👋 再见!")
                break
            elif command == 'help':
                print_interactive_help()
            elif command == 'list':
                print_report_types()
            elif command.startswith('generate '):
                report_type = command.split(' ', 1)[1]
                if report_type in ['daily', 'weekly', 'threat_summary', 'network_security', 'ai_analysis']:
                    await generate_single_report(report_type, 'report_config.yaml', 'html')
                else:
                    print(f"❌ 不支持的ReportType: {report_type}")
            elif command == 'status':
                await show_system_status(generator)
            elif command == 'config':
                show_config_info(generator)
            else:
                print(f"❌ Not知Command: {command}")
                print("Input 'help' 查看可用Command")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ CommandExecuteError: {e}")

def print_interactive_help():
    """打印交互模式帮助"""
    help_text = """
📖 可用Command:
  help                    显示此帮助Information
  list                    列出所HasReportType
  generate <type>         生成指定Type的Report
  status                  显示SystemStatus
  config                  显示ConfigurationInformation
  quit/exit              退出Program

📝 Example:
  generate daily          生成每日Report
  generate threat_summary 生成威胁摘要
"""
    print(help_text)

async def show_system_status(generator):
    """显示SystemStatus"""
    try:
        print("\n📊 SystemStatus:")
        
        # 获取System健康Data
        health_data = await generator.get_system_health()
        
        print(f"   🖥️  CPU使用率: {health_data.get('cpu_usage', 0)}%")
        print(f"   💾 Memory使用率: {health_data.get('memory_usage', 0)}%")
        print(f"   💿 Disk使用率: {health_data.get('disk_usage', 0)}%")
        
        # CheckServiceStatus
        services = health_data.get('services_status', {})
        print(f"   🛡️  HunterMatrix: {services.get('huntermatrix', 'unknown')}")
        print(f"   🤖 AIService: {services.get('ai_service', 'unknown')}")
        print(f"   🌐 WebInterface: {services.get('web_ui', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 获取SystemStatusFailed: {e}")

def show_config_info(generator):
    """显示ConfigurationInformation"""
    try:
        config = generator.config
        print("\n⚙️  ConfigurationInformation:")
        print(f"   📧 邮件Send: {'启用' if config['email']['enabled'] else '禁用'}")
        print(f"   📅 每日Report: {config['schedule']['daily_report_time']}")
        print(f"   📊 周报Time: 每周{config['schedule']['weekly_report_day']} {config['schedule']['weekly_report_time']}")
        print(f"   📁 OutputDirectory: {config['report']['output_dir']}")
        print(f"   📄 OutputFormat: {', '.join(config['report']['formats'])}")
        print(f"   🤖 AIAnalysis: {'启用' if config['ai']['enabled'] else '禁用'}")
        
    except Exception as e:
        print(f"❌ 获取ConfigurationInformationFailed: {e}")

def main():
    """Main Function"""
    parser = argparse.ArgumentParser(
        description='AISecurityReport生成Command行Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example用法:
  python3 generate_report.py --type daily                    # 生成每日Report
  python3 generate_report.py --type weekly --format json     # 生成JSONFormat周报
  python3 generate_report.py --batch daily weekly            # 批量生成Report
  python3 generate_report.py --interactive                   # 交互模式
  python3 generate_report.py --list                          # 列出ReportType
        """
    )
    
    parser.add_argument('--type', '-t', 
                       choices=['daily', 'weekly', 'threat_summary', 'network_security', 'ai_analysis'],
                       help='ReportType')
    
    parser.add_argument('--format', '-f',
                       choices=['html', 'json', 'txt'],
                       default='html',
                       help='OutputFormat (Default: html)')
    
    parser.add_argument('--config', '-c',
                       default='report_config.yaml',
                       help='ConfigurationFilePath (Default: report_config.yaml)')
    
    parser.add_argument('--batch', '-b',
                       nargs='+',
                       choices=['daily', 'weekly', 'threat_summary', 'network_security', 'ai_analysis'],
                       help='批量生成多个Report')
    
    parser.add_argument('--interactive', '-i',
                       action='store_true',
                       help='进入交互模式')
    
    parser.add_argument('--list', '-l',
                       action='store_true',
                       help='列出所Has支持的ReportType')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='静默模式，只OutputErrorInformation')
    
    args = parser.parse_args()
    
    # 静默模式Process
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.ERROR)
    else:
        print_banner()
    
    # ProcessCommand
    if args.list:
        print_report_types()
        return
    
    if args.interactive:
        asyncio.run(interactive_mode())
        return
    
    if args.batch:
        asyncio.run(generate_batch_reports(args.batch, args.config))
        return
    
    if args.type:
        result = asyncio.run(generate_single_report(args.type, args.config, args.format))
        if result is None:
            sys.exit(1)
        return
    
    # 如果没Has指定任何Operation，显示帮助
    parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 OperationAlready取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ProgramExecuteError: {e}")
        sys.exit(1)
