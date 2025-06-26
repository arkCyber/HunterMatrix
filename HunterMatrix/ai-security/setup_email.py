#!/usr/bin/env python3
"""
邮件ServiceConfiguration和TestTool
帮助User快速Configuration和Test邮件Send功能
"""

import asyncio
import yaml
import getpass
from pathlib import Path
from email_service import EmailService

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    📧 邮件ServiceConfigurationTool                       ║
║                                                              ║
║  快速ConfigurationAISecurityReport的邮件Send功能                             ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def get_email_provider():
    """选择邮件Service提供商"""
    providers = {
        '1': ('gmail', 'Gmail (推荐)'),
        '2': ('outlook', 'Outlook/Hotmail'),
        '3': ('yahoo', 'Yahoo Mail'),
        '4': ('qq', 'QQ邮箱'),
        '5': ('163', '163邮箱'),
        '6': ('custom', 'CustomSMTPService器')
    }
    
    print("\n📮 选择邮件Service提供商:")
    for key, (provider, name) in providers.items():
        print(f"  {key}. {name}")
    
    while True:
        choice = input("\n请选择 (1-6): ").strip()
        if choice in providers:
            return providers[choice][0]
        print("❌ No效选择，请重新Input")

def get_smtp_config():
    """获取CustomSMTPConfiguration"""
    print("\n🔧 ConfigurationCustomSMTPService器:")
    
    server = input("SMTPService器地址: ").strip()
    
    while True:
        try:
            port = int(input("SMTP端口 (Default587): ").strip() or "587")
            break
        except ValueError:
            print("❌ 请InputHas效的端口号")
    
    use_tls = input("使用TLSEncryption? (Y/n): ").strip().lower() != 'n'
    use_ssl = input("使用SSLEncryption? (y/N): ").strip().lower() == 'y'
    
    return {
        'server': server,
        'port': port,
        'use_tls': use_tls,
        'use_ssl': use_ssl
    }

def get_auth_info():
    """获取AuthenticationInformation"""
    print("\n🔐 Configuration邮箱AuthenticationInformation:")
    
    username = input("邮箱地址: ").strip()
    password = getpass.getpass("邮箱Password或Application专用Password: ")
    
    return username, password

def get_recipients():
    """获取收件人Configuration"""
    print("\n👥 Configuration收件人:")
    
    print("Default收件人 (用于一般Report):")
    default_recipients = []
    while True:
        email = input(f"  收件人 {len(default_recipients) + 1} (回车End): ").strip()
        if not email:
            break
        default_recipients.append(email)
    
    print("\n紧急联系人 (用于高危威胁告警):")
    emergency_recipients = []
    while True:
        email = input(f"  紧急联系人 {len(emergency_recipients) + 1} (回车End): ").strip()
        if not email:
            break
        emergency_recipients.append(email)
    
    # 如果没HasSettings紧急联系人，使用Default收件人
    if not emergency_recipients:
        emergency_recipients = default_recipients.copy()
    
    return {
        'default': default_recipients,
        'emergency': emergency_recipients,
        'reports': default_recipients,
        'technical': default_recipients
    }

def get_sender_info():
    """获取发件人Information"""
    print("\n📤 Configuration发件人Information:")
    
    name = input("发件人Name (Default: AISecurity助手): ").strip() or "AISecurity助手"
    email = input("发件人邮箱地址: ").strip()
    
    return {
        'name': name,
        'email': email
    }

def create_email_config(provider, smtp_config, username, password, sender, recipients):
    """Create邮件Configuration"""
    config = {
        'enabled': True,
        'provider': provider,
        'auth': {
            'username': username,
            'password': password,
            'use_oauth': False
        },
        'sender': sender,
        'recipients': recipients,
        'templates': {
            'daily_report': 'daily_report.html',
            'weekly_report': 'weekly_report.html',
            'threat_alert': 'threat_alert.html',
            'emergency_alert': 'emergency_alert.html'
        },
        'attachments': {
            'max_size_mb': 25,
            'allowed_types': ['.pdf', '.html', '.txt', '.json', '.csv'],
            'compress_large_files': True
        },
        'retry': {
            'max_attempts': 3,
            'delay_seconds': 5
        },
        'content': {
            'subject_prefix': '[AISecurity]',
            'company': {
                'name': '您的CompanyName',
                'support_email': sender['email']
            },
            'contacts': {
                'emergency_phone': '+1-800-SECURITY',
                'security_team': sender['email']
            }
        }
    }
    
    # 如果是CustomSMTP，添加SMTPConfiguration
    if provider == 'custom':
        config['smtp'] = smtp_config
    
    return config

async def test_email_config(config_file):
    """Test邮件Configuration"""
    print("\n🧪 Test邮件Configuration...")
    
    try:
        email_service = EmailService(config_file)
        
        # TestConfiguration
        config_test = email_service.test_email_config()
        
        print(f"   ConfigurationHas效性: {'✅ Has效' if config_test['config_valid'] else '❌ No效'}")
        
        if config_test['errors']:
            print("   Error:")
            for error in config_test['errors']:
                print(f"     ❌ {error}")
        
        if config_test['warnings']:
            print("   警告:")
            for warning in config_test['warnings']:
                print(f"     ⚠️  {warning}")
        
        if not config_test['config_valid']:
            return False
        
        # SendTest邮件
        test_email = input("\n📧 InputTest邮箱地址 (回车跳过): ").strip()
        if test_email:
            print("📤 SendTest邮件...")
            success = await email_service.send_test_email(test_email)
            
            if success:
                print("✅ Test邮件SendSuccess！请Check收件箱。")
            else:
                print("❌ Test邮件SendFailed，请CheckConfiguration。")
            
            return success
        else:
            print("⏭️  跳过邮件SendTest")
            return True
            
    except Exception as e:
        print(f"❌ TestFailed: {e}")
        return False

def save_config(config, config_file):
    """SaveConfiguration到File"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ ConfigurationAlreadySave到: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ SaveConfigurationFailed: {e}")
        return False

async def interactive_setup():
    """交互式Configuration"""
    print_banner()
    
    print("🚀 StartConfiguration邮件Service...")
    
    # 选择邮件Service提供商
    provider = get_email_provider()
    
    # 获取SMTPConfiguration (仅CustomService器需要)
    smtp_config = None
    if provider == 'custom':
        smtp_config = get_smtp_config()
    
    # 获取AuthenticationInformation
    username, password = get_auth_info()
    
    # 获取发件人Information
    sender = get_sender_info()
    
    # 获取收件人Configuration
    recipients = get_recipients()
    
    # CreateConfiguration
    config = create_email_config(provider, smtp_config, username, password, sender, recipients)
    
    # SaveConfiguration
    config_file = 'email_config.yaml'
    if save_config(config, config_file):
        # TestConfiguration
        success = await test_email_config(config_file)
        
        if success:
            print("\n🎉 邮件ServiceConfigurationComplete！")
            print("\n📋 后续步骤:")
            print("  1. StartAIService: ./start_ai_service.sh start")
            print("  2. 生成TestReport: python3 generate_report.py --type daily")
            print("  3. Check邮件Receive情况")
        else:
            print("\n⚠️  ConfigurationAlreadySave，但TestFailed。请CheckConfiguration后重新Test。")
    else:
        print("\n❌ ConfigurationSaveFailed，请ManualCreateConfigurationFile。")

def show_help():
    """显示帮助Information"""
    help_text = """
📖 邮件ServiceConfigurationTool使用说明

🎯 功能:
  - 交互式Configuration邮件Service
  - 支持多种邮件Service提供商
  - AutomaticTest邮件Send功能
  - 生成完整的ConfigurationFile

📮 支持的邮件Service商:
  - Gmail (推荐)
  - Outlook/Hotmail
  - Yahoo Mail
  - QQ邮箱
  - 163邮箱
  - CustomSMTPService器

🔐 Security提示:
  - 建议使用Application专用Password而非账户Password
  - GmailUser需要启用"不够Security的Application访问Permission"或使用ApplicationPassword
  - ConfigurationFilePackage含敏感Information，请妥善保管

🚀 快速Start:
  python3 setup_email.py

📧 Test邮件:
  python3 setup_email.py --test

🔧 重新Configuration:
  python3 setup_email.py --reconfigure
"""
    print(help_text)

async def main():
    """Main Function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='邮件ServiceConfigurationTool')
    parser.add_argument('--test', action='store_true', help='仅Test现HasConfiguration')
    parser.add_argument('--reconfigure', action='store_true', help='重新Configuration')
    parser.add_argument('--help-detail', action='store_true', help='显示详细帮助')
    
    args = parser.parse_args()
    
    if args.help_detail:
        show_help()
        return
    
    config_file = 'email_config.yaml'
    
    if args.test:
        # 仅Test现HasConfiguration
        if Path(config_file).exists():
            await test_email_config(config_file)
        else:
            print(f"❌ ConfigurationFile {config_file} 不存在，请先RunConfiguration")
        return
    
    if args.reconfigure or not Path(config_file).exists():
        # 交互式Configuration
        await interactive_setup()
    else:
        # ConfigurationFileAlready存在
        print(f"📧 邮件ConfigurationFile {config_file} Already存在")
        choice = input("是否重新Configuration? (y/N): ").strip().lower()
        
        if choice == 'y':
            await interactive_setup()
        else:
            print("使用现HasConfiguration，RunTest...")
            await test_email_config(config_file)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 ConfigurationAlready取消")
    except Exception as e:
        print(f"\n❌ Configuration过程出错: {e}")
