#!/bin/bash

# HunterMatrix AISmartSecurityPlatform - InstallScript
# Copyright (C) 2024 arkSong
# 
# 这个Script将AutomaticInstallHunterMatrix及其所Has依赖项

set -e  # 遇到Error时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# 显示欢迎Information
show_welcome() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        🛡️  HunterMatrix AISmartSecurityPlatform InstallProgram  🛡️         ║"
    echo "║                                                              ║"
    echo "║                    基于HunterMatrix的下一代                        ║"
    echo "║                   AISmartSecurity防护Platform                         ║"
    echo "║                                                              ║"
    echo "║                  Created by arkSong                          ║"
    echo "║              https://github.com/arkCyber                     ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

# DetectionOperationSystem
detect_os() {
    log_step "DetectionOperationSystem..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            log_info "Detection到 Debian/Ubuntu System"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            log_info "Detection到 RedHat/CentOS/Fedora System"
        else
            OS="linux"
            log_info "Detection到 Linux System"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "Detection到 macOS System"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        log_info "Detection到 Windows System"
    else
        OS="unknown"
        log_warning "Not知OperationSystem: $OSTYPE"
    fi
}

# CheckSystem要求
check_requirements() {
    log_step "CheckSystem要求..."
    
    # CheckMemory
    if [[ "$OS" == "linux" ]] || [[ "$OS" == "debian" ]] || [[ "$OS" == "redhat" ]]; then
        MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        MEMORY_GB=$((MEMORY_KB / 1024 / 1024))
    elif [[ "$OS" == "macos" ]]; then
        MEMORY_BYTES=$(sysctl -n hw.memsize)
        MEMORY_GB=$((MEMORY_BYTES / 1024 / 1024 / 1024))
    fi
    
    if [ "$MEMORY_GB" -lt 4 ]; then
        log_warning "SystemMemory少于4GB，可能影响Performance"
    else
        log_success "MemoryCheck通过: ${MEMORY_GB}GB"
    fi
    
    # CheckDiskNull间
    DISK_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$DISK_SPACE" -lt 2 ]; then
        log_error "DiskNull间不足，至少需要2GB可用Null间"
        exit 1
    else
        log_success "DiskNull间Check通过: ${DISK_SPACE}GB可用"
    fi
}

# InstallSystem依赖
install_system_deps() {
    log_step "InstallSystem依赖..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y \
                cmake \
                build-essential \
                libssl-dev \
                pkg-config \
                python3 \
                python3-pip \
                python3-venv \
                curl \
                wget \
                git \
                unzip
            ;;
        "redhat")
            sudo yum update -y
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y \
                cmake \
                openssl-devel \
                pkgconfig \
                python3 \
                python3-pip \
                curl \
                wget \
                git \
                unzip
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_info "Install Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            brew install \
                cmake \
                openssl \
                pkg-config \
                python3 \
                rust \
                node
            ;;
        *)
            log_warning "请ManualInstall以下依赖: cmake, python3, rust, node"
            ;;
    esac
    
    log_success "System依赖InstallComplete"
}

# InstallRust
install_rust() {
    log_step "Install Rust..."
    
    if ! command -v rustc &> /dev/null; then
        log_info "Download并Install Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
        log_success "Rust InstallComplete"
    else
        log_info "Rust AlreadyInstall: $(rustc --version)"
    fi
}

# InstallNode.js
install_nodejs() {
    log_step "Install Node.js..."
    
    if ! command -v node &> /dev/null; then
        log_info "Download并Install Node.js..."
        
        case $OS in
            "debian"|"redhat"|"linux")
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                sudo apt-get install -y nodejs
                ;;
            "macos")
                brew install node
                ;;
            *)
                log_warning "请ManualInstall Node.js 18+"
                ;;
        esac
        
        log_success "Node.js InstallComplete"
    else
        log_info "Node.js AlreadyInstall: $(node --version)"
    fi
}

# InstallPython依赖
install_python_deps() {
    log_step "Install Python 依赖..."
    
    # Create虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Create Python 虚拟环境"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # Upgradepip
    pip install --upgrade pip
    
    # InstallAISecurityModule依赖
    if [ -f "ai-security/requirements.txt" ]; then
        pip install -r ai-security/requirements.txt
        log_success "AISecurityModule依赖InstallComplete"
    fi
    
    # Install其他Python依赖
    pip install \
        fastapi \
        uvicorn \
        websockets \
        aiofiles \
        pydantic \
        sqlalchemy \
        alembic
    
    log_success "Python 依赖InstallComplete"
}

# Build项目
build_project() {
    log_step "Build HunterMatrix 项目..."
    
    # CreateBuildDirectory
    mkdir -p build
    cd build
    
    # ConfigurationCMake
    log_info "Configuration CMake..."
    cmake .. -DCMAKE_BUILD_TYPE=Release
    
    # Compile项目
    log_info "Compile项目..."
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    
    cd ..
    log_success "项目BuildComplete"
}

# InstallNode.js依赖
install_node_deps() {
    log_step "Install Node.js 依赖..."
    
    if [ -f "package.json" ]; then
        npm install
        log_success "Node.js 依赖InstallComplete"
    fi
}

# SettingsPermission
setup_permissions() {
    log_step "SettingsFilePermission..."
    
    # SettingsScriptExecutePermission
    chmod +x *.sh
    chmod +x web-ui/*.sh
    
    # SettingsConfigurationFilePermission
    if [ -d "etc" ]; then
        chmod 644 etc/*.conf.sample
    fi
    
    log_success "PermissionSettingsComplete"
}

# CreateConfigurationFile
create_configs() {
    log_step "CreateConfigurationFile..."
    
    # 复制ExampleConfigurationFile
    if [ -f "etc/clamd.conf.sample" ] && [ ! -f "clamd.conf" ]; then
        cp etc/clamd.conf.sample clamd.conf
        log_info "Create clamd.conf"
    fi
    
    if [ -f "etc/freshclam.conf.sample" ] && [ ! -f "freshclam.conf" ]; then
        cp etc/freshclam.conf.sample freshclam.conf
        log_info "Create freshclam.conf"
    fi
    
    log_success "ConfigurationFileCreateComplete"
}

# TestInstall
test_installation() {
    log_step "TestInstall..."
    
    # TestBuildResult
    if [ -f "build/clamscan" ]; then
        log_success "HunterMatrix 扫描引擎BuildSuccess"
    else
        log_warning "HunterMatrix 扫描引擎Not找到"
    fi
    
    # TestPythonModule
    source venv/bin/activate
    python3 -c "import fastapi; print('FastAPI 可用')" 2>/dev/null && log_success "Python 依赖正常" || log_warning "Python 依赖可能Has问题"
    
    # TestNode.js
    if command -v node &> /dev/null; then
        log_success "Node.js 可用: $(node --version)"
    fi
    
    # TestRust
    if command -v cargo &> /dev/null; then
        log_success "Rust 可用: $(cargo --version)"
    fi
}

# 显示CompleteInformation
show_completion() {
    echo
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                  🎉 InstallComplete！🎉                            ║"
    echo "║                                                              ║"
    echo "║              HunterMatrix AlreadySuccessInstall到您的System               ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo -e "${CYAN}🚀 快速Start:${NC}"
    echo "   ./start_huntermatrix.sh"
    echo
    echo -e "${CYAN}🌐 访问地址:${NC}"
    echo "   http://localhost:8083/huntermatrix_final.html"
    echo
    echo -e "${CYAN}📚 更多Information:${NC}"
    echo "   README.md - UserManual"
    echo "   CONTRIBUTING.md - 贡献Guide"
    echo "   https://github.com/arkCyber/HunterMatrix"
    echo
    echo -e "${YELLOW}⚠️  注意事项:${NC}"
    echo "   1. 首次Start前请Update病毒Library: freshclam"
    echo "   2. 确保防火墙允许端口 8083"
    echo "   3. 建议定期Update病毒Library和SoftwareVersion"
    echo
}

# 主Install流程
main() {
    show_welcome
    
    # Check是否为rootUser
    if [ "$EUID" -eq 0 ]; then
        log_warning "不建议以rootUserRunInstallProgram"
        read -p "是否Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    detect_os
    check_requirements
    install_system_deps
    install_rust
    install_nodejs
    install_python_deps
    install_node_deps
    build_project
    setup_permissions
    create_configs
    test_installation
    show_completion
    
    log_success "HunterMatrix InstallComplete！"
}

# ErrorProcess
trap 'log_error "Install过程中发生Error，请CheckLog"; exit 1' ERR

# Run主Program
main "$@"
