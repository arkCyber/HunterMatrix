#!/bin/bash

# HunterMatrix 快速StartScript
# AutomaticCompleteHunterMatrix的Initialize和Start过程

echo "🚀 HunterMatrix 快速StartScript"
echo "========================"
echo

# Settings颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# SettingsPath
CLAMD_BIN="build/clamd/clamd"
FRESHCLAM_BIN="build/freshclam/freshclam"
CLAMD_CONF="clamd.conf"
FRESHCLAM_CONF="freshclam.conf"
VIRUS_DB_DIR="virus_database"

# ErrorProcess
set -e
trap 'echo -e "\n${RED}❌ ScriptExecuteFailed${NC}"; exit 1' ERR

# 步骤1: CheckBuildStatus
echo "📋 步骤 1/5: CheckBuildStatus"
echo "------------------------"

if [ ! -f "$CLAMD_BIN" ] || [ ! -f "$FRESHCLAM_BIN" ]; then
    echo -e "${RED}❌ Error: HunterMatrix Not正确Build${NC}"
    echo "请先RunBuildCommand:"
    echo "  mkdir build && cd build"
    echo "  cmake .. && make"
    exit 1
fi

echo -e "${GREEN}✅ BuildFileCheck通过${NC}"
echo

# 步骤2: CheckConfigurationFile
echo "⚙️  步骤 2/5: CheckConfigurationFile"
echo "------------------------"

if [ ! -f "$CLAMD_CONF" ] || [ ! -f "$FRESHCLAM_CONF" ]; then
    echo -e "${RED}❌ Error: ConfigurationFile缺失${NC}"
    echo "请确保以下File存在:"
    echo "  - $CLAMD_CONF"
    echo "  - $FRESHCLAM_CONF"
    exit 1
fi

echo -e "${GREEN}✅ ConfigurationFileCheck通过${NC}"
echo

# 步骤3: Create病毒LibraryDirectory
echo "📁 步骤 3/5: 准备病毒LibraryDirectory"
echo "----------------------------"

if [ ! -d "$VIRUS_DB_DIR" ]; then
    echo "Create病毒LibraryDirectory: $VIRUS_DB_DIR"
    mkdir -p "$VIRUS_DB_DIR"
fi

echo -e "${GREEN}✅ 病毒LibraryDirectory准备Complete${NC}"
echo

# 步骤4: Update病毒Library
echo "🔄 步骤 4/5: Update病毒Library"
echo "----------------------"

# Check是否AlreadyHas病毒LibraryFile
db_count=$(ls "$VIRUS_DB_DIR"/*.c*d 2>/dev/null | wc -l || echo 0)

if [ "$db_count" -eq 0 ]; then
    echo "首次Run，需要Download病毒Library..."
    echo "这可能需要几分钟Time，请耐心等待..."
    echo
    
    if "$FRESHCLAM_BIN" --config-file="$FRESHCLAM_CONF"; then
        echo -e "${GREEN}✅ 病毒LibraryDownloadSuccess${NC}"
    else
        echo -e "${YELLOW}⚠️  病毒LibraryDownload可能Failed，但ContinueStart${NC}"
    fi
else
    echo "Found现Has病毒LibraryFile ($db_count 个)"
    echo "CheckUpdate..."
    
    if "$FRESHCLAM_BIN" --config-file="$FRESHCLAM_CONF" --check; then
        echo -e "${GREEN}✅ 病毒Library是最新的${NC}"
    else
        echo -e "${YELLOW}⚠️  病毒Library可能需要Update${NC}"
    fi
fi

echo

# 步骤5: StartClamD守护Process
echo "🚀 步骤 5/5: Start ClamD 守护Process"
echo "-------------------------------"

# Check是否Already经Run
PID_FILE="/tmp/clamd.pid"
SOCKET_FILE="/tmp/clamd.sock"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  ClamD Already经在Run (PID: $PID)${NC}"
    else
        echo "Clean旧的PIDFile..."
        rm -f "$PID_FILE" "$SOCKET_FILE"
    fi
fi

if [ ! -S "$SOCKET_FILE" ]; then
    echo "Start ClamD 守护Process..."
    "$CLAMD_BIN" --config-file="$CLAMD_CONF"
    
    # 等待Start
    echo -n "等待守护ProcessStart"
    for i in {1..15}; do
        if [ -S "$SOCKET_FILE" ]; then
            echo
            echo -e "${GREEN}✅ ClamD StartSuccess${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if [ ! -S "$SOCKET_FILE" ]; then
        echo
        echo -e "${RED}❌ ClamD StartFailed或超时${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ ClamD Already经Run${NC}"
fi

echo

# Validation功能
echo "🔍 Validation功能"
echo "----------"

# TestConnection
echo -n "Test守护ProcessConnection: "
if echo "PING" | nc -U "$SOCKET_FILE" 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}Success${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# 获取VersionInformation
echo -n "获取VersionInformation: "
VERSION=$(echo "VERSION" | nc -U "$SOCKET_FILE" 2>/dev/null)
if [ -n "$VERSION" ]; then
    echo -e "${GREEN}Success${NC}"
    echo "  Version: $VERSION"
else
    echo -e "${RED}Failed${NC}"
fi

echo

# 显示Status摘要
echo "📊 StartComplete - Status摘要"
echo "====================="
echo
echo -e "${GREEN}✅ HunterMatrix AlreadySuccessStart并Run${NC}"
echo
echo "ServiceStatus:"
echo "  • ClamD 守护Process: Run中"
echo "  • Socket File: $SOCKET_FILE"
echo "  • PID File: $PID_FILE"
echo "  • 病毒LibraryDirectory: $VIRUS_DB_DIR"
echo
echo "病毒LibraryInformation:"
db_files=$(ls "$VIRUS_DB_DIR"/*.c*d 2>/dev/null | wc -l || echo 0)
echo "  • DataLibraryFile: $db_files 个"
if [ "$db_files" -gt 0 ]; then
    db_size=$(du -sh "$VIRUS_DB_DIR" 2>/dev/null | cut -f1)
    echo "  • 总Size: $db_size"
fi

echo
echo "🎉 HunterMatrix 现在可以使用了！"
echo
echo "常用Command:"
echo -e "${BLUE}# 扫描File:${NC}"
echo "  build/clamdscan/clamdscan --config-file=clamd.conf /path/to/file"
echo
echo -e "${BLUE}# Scan Directory:${NC}"
echo "  build/clamdscan/clamdscan --config-file=clamd.conf --recursive /path/to/directory"
echo
echo -e "${BLUE}# 使用管理Tool:${NC}"
echo "  ./huntermatrix_manager.sh"
echo
echo -e "${BLUE}# Stop守护Process:${NC}"
echo "  echo 'SHUTDOWN' | nc -U $SOCKET_FILE"

echo
echo "🔗 更多Information请Run: ./huntermatrix_manager.sh"
