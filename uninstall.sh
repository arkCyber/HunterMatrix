#!/bin/bash

# HunterMatrix AISmartSecurityPlatform - UninstallScript
# Copyright (C) 2024 arkSong

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# LogFunction
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 显示UninstallInformation
show_uninstall_info() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        🗑️  HunterMatrix AISmartSecurityPlatform UninstallProgram  🗑️         ║"
    echo "║                                                              ║"
    echo "║                  即将Uninstall HunterMatrix                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

# 确认Uninstall
confirm_uninstall() {
    log_warning "此Operation将完全Delete HunterMatrix 及其所HasData"
    echo
    echo "将要Delete的Content："
    echo "  - ProgramFile和BuildOutput"
    echo "  - Python 虚拟环境"
    echo "  - ConfigurationFile"
    echo "  - LogFile"
    echo "  - Cache和临时File"
    echo
    log_warning "UserData和扫描历史将被永久Delete！"
    echo
    
    read -p "确定要ContinueUninstall吗? (Input 'YES' 确认): " -r
    if [[ ! $REPLY == "YES" ]]; then
        log_info "UninstallAlready取消"
        exit 0
    fi
}

# StopRun的Service
stop_services() {
    log_step "Stop HunterMatrix Service..."
    
    # StopWebService
    pkill -f "start_server.py" 2>/dev/null || true
    pkill -f "huntermatrix" 2>/dev/null || true
    pkill -f "clamd" 2>/dev/null || true
    
    # 等待Process完全Stop
    sleep 2
    
    log_success "ServiceAlreadyStop"
}

# DeleteBuildFile
remove_build_files() {
    log_step "DeleteBuildFile..."
    
    if [ -d "build" ]; then
        rm -rf build/
        log_info "Delete build/ Directory"
    fi
    
    if [ -d "target" ]; then
        rm -rf target/
        log_info "Delete target/ Directory"
    fi
    
    log_success "BuildFileAlreadyDelete"
}

# DeletePython环境
remove_python_env() {
    log_step "Delete Python 虚拟环境..."
    
    if [ -d "venv" ]; then
        rm -rf venv/
        log_info "Delete venv/ Directory"
    fi
    
    if [ -d "__pycache__" ]; then
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        log_info "Delete Python CacheFile"
    fi
    
    if [ -d ".pytest_cache" ]; then
        rm -rf .pytest_cache/
        log_info "DeleteTestCache"
    fi
    
    log_success "Python 环境AlreadyDelete"
}

# DeleteNode.jsFile
remove_node_files() {
    log_step "Delete Node.js File..."
    
    if [ -d "node_modules" ]; then
        rm -rf node_modules/
        log_info "Delete node_modules/ Directory"
    fi
    
    if [ -f "package-lock.json" ]; then
        rm -f package-lock.json
        log_info "Delete package-lock.json"
    fi
    
    log_success "Node.js FileAlreadyDelete"
}

# DeleteConfigurationFile
remove_config_files() {
    log_step "DeleteConfigurationFile..."
    
    # ConfigurationFile列Table
    config_files=(
        "clamd.conf"
        "freshclam.conf"
        "config.json"
        "settings.json"
        ".env"
        ".env.local"
        "email_config.yaml"
        "matrix_config.toml"
    )
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_info "Delete $file"
        fi
    done
    
    log_success "ConfigurationFileAlreadyDelete"
}

# DeleteDataFile
remove_data_files() {
    log_step "DeleteDataFile..."
    
    # DataDirectory列Table
    data_dirs=(
        "user_data"
        "user_configs"
        "user_reports"
        "scan_results"
        "quarantine"
        "virus_database"
        "ai_cache"
        "network_logs"
        "mail_queue"
        "matrix_queue"
    )
    
    for dir in "${data_dirs[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir/"
            log_info "Delete $dir/ Directory"
        fi
    done
    
    # DataLibraryFile
    db_files=(
        "*.db"
        "*.sqlite"
        "*.sqlite3"
    )
    
    for pattern in "${db_files[@]}"; do
        find . -name "$pattern" -type f -delete 2>/dev/null || true
    done
    
    log_success "DataFileAlreadyDelete"
}

# DeleteLogFile
remove_log_files() {
    log_step "DeleteLogFile..."
    
    # LogFile和Directory
    log_items=(
        "logs"
        "*.log"
        "*.log.*"
        "freshclam.log"
        "clamd.log"
        "scan.log"
        "ai_service.log"
    )
    
    for item in "${log_items[@]}"; do
        if [[ "$item" == *"*"* ]]; then
            # 通配符模式
            find . -name "$item" -type f -delete 2>/dev/null || true
        elif [ -d "$item" ]; then
            rm -rf "$item/"
            log_info "Delete $item/ Directory"
        elif [ -f "$item" ]; then
            rm -f "$item"
            log_info "Delete $item"
        fi
    done
    
    log_success "LogFileAlreadyDelete"
}

# Delete临时File
remove_temp_files() {
    log_step "Delete临时File..."
    
    # 临时File模式
    temp_patterns=(
        "*.tmp"
        "*.temp"
        "*.swp"
        "*.swo"
        "*~"
        ".DS_Store"
        "Thumbs.db"
        "*.bak"
        "*.backup"
        "*.old"
    )
    
    for pattern in "${temp_patterns[@]}"; do
        find . -name "$pattern" -type f -delete 2>/dev/null || true
    done
    
    # 临时Directory
    temp_dirs=(
        "temp"
        "cache"
        ".cache"
        "tmp"
    )
    
    for dir in "${temp_dirs[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir/"
            log_info "Delete $dir/ Directory"
        fi
    done
    
    log_success "临时FileAlreadyDelete"
}

# DeleteIDEFile
remove_ide_files() {
    log_step "DeleteIDE和Edit器File..."
    
    ide_dirs=(
        ".vscode"
        ".idea"
        ".atom"
    )
    
    for dir in "${ide_dirs[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir/"
            log_info "Delete $dir/ Directory"
        fi
    done
    
    ide_files=(
        "*.sublime-project"
        "*.sublime-workspace"
        ".brackets.json"
        "*.code-workspace"
    )
    
    for pattern in "${ide_files[@]}"; do
        find . -name "$pattern" -type f -delete 2>/dev/null || true
    done
    
    log_success "IDEFileAlreadyDelete"
}

# CleanSystemService（可选）
cleanup_system_services() {
    log_step "CleanSystemService..."
    
    # 这里可以添加CleanSystem级Service的Code
    # 例如：systemdService、launchdService等
    
    log_info "SystemServiceCleanComplete"
}

# 显示UninstallCompleteInformation
show_completion() {
    echo
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                  ✅ UninstallComplete！✅                            ║"
    echo "║                                                              ║"
    echo "║              HunterMatrix Already从您的System中移除                ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo -e "${CYAN}📋 Uninstall摘要:${NC}"
    echo "   ✅ ServiceAlreadyStop"
    echo "   ✅ ProgramFileAlreadyDelete"
    echo "   ✅ ConfigurationFileAlreadyDelete"
    echo "   ✅ DataFileAlreadyDelete"
    echo "   ✅ LogFileAlreadyDelete"
    echo "   ✅ 临时FileAlreadyClean"
    echo
    echo -e "${YELLOW}📝 注意事项:${NC}"
    echo "   - System依赖项（Python、Rust、Node.js等）Not被Delete"
    echo "   - 如需完全Clean，请ManualUninstall这些依赖项"
    echo "   - BackupFile（如果Has）需要ManualDelete"
    echo
    echo -e "${CYAN}🙏 感谢使用 HunterMatrix！${NC}"
    echo "   如Has问题或建议，请访问："
    echo "   https://github.com/arkCyber/HunterMatrix"
    echo
}

# 主Uninstall流程
main() {
    show_uninstall_info
    confirm_uninstall
    
    log_info "StartUninstall HunterMatrix..."
    
    stop_services
    remove_build_files
    remove_python_env
    remove_node_files
    remove_config_files
    remove_data_files
    remove_log_files
    remove_temp_files
    remove_ide_files
    cleanup_system_services
    
    show_completion
    
    log_success "HunterMatrix UninstallComplete！"
}

# ErrorProcess
trap 'log_error "Uninstall过程中发生Error"; exit 1' ERR

# Run主Program
main "$@"
