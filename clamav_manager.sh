#!/bin/bash

# HunterMatrix 管理Script
# 提供HunterMatrix的Start、Stop、Test等功能

echo "=== HunterMatrix 管理Tool ==="
echo

# Settings颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# SettingsPath
CLAMD_BIN="build/clamd/clamd"
FRESHCLAM_BIN="build/freshclam/freshclam"
CLAMSCAN_BIN="build/clamscan/clamscan"
CLAMDSCAN_BIN="build/clamdscan/clamdscan"
CLAMD_CONF="clamd.conf"
FRESHCLAM_CONF="freshclam.conf"
SOCKET_FILE="/tmp/clamd.sock"
PID_FILE="/tmp/clamd.pid"

# 显示Menu
show_menu() {
    echo -e "${PURPLE}=== HunterMatrix 管理Menu ===${NC}"
    echo
    echo "1) 🔍 CheckSystemStatus"
    echo "2) 🔄 Update病毒Library (freshclam)"
    echo "3) 🚀 Start ClamD 守护Process"
    echo "4) 🛑 Stop ClamD 守护Process"
    echo "5) 📊 查看 ClamD Status"
    echo "6) 🔍 扫描File/Directory (clamscan)"
    echo "7) ⚡ 快速扫描 (clamdscan)"
    echo "8) 🧪 RunTest套件"
    echo "9) 📋 查看Log"
    echo "10) ❓ 显示帮助"
    echo "0) 🚪 退出"
    echo
    read -p "请选择Operation (0-10): " choice
}

# CheckSystemStatus
check_status() {
    echo -e "${BLUE}=== SystemStatusCheck ===${NC}"
    echo
    
    # Check可ExecuteFile
    echo "Check可ExecuteFile:"
    for bin in "$CLAMD_BIN" "$FRESHCLAM_BIN" "$CLAMSCAN_BIN" "$CLAMDSCAN_BIN"; do
        if [ -f "$bin" ] && [ -x "$bin" ]; then
            echo -e "  ✅ $(basename "$bin"): ${GREEN}存在且可Execute${NC}"
        else
            echo -e "  ❌ $(basename "$bin"): ${RED}缺失或不可Execute${NC}"
        fi
    done
    
    echo
    
    # CheckConfigurationFile
    echo "CheckConfigurationFile:"
    for conf in "$CLAMD_CONF" "$FRESHCLAM_CONF"; do
        if [ -f "$conf" ]; then
            echo -e "  ✅ $(basename "$conf"): ${GREEN}存在${NC}"
        else
            echo -e "  ❌ $(basename "$conf"): ${RED}缺失${NC}"
        fi
    done
    
    echo
    
    # Check病毒Library
    echo "Check病毒Library:"
    if [ -d "virus_database" ]; then
        db_count=$(ls virus_database/*.c*d 2>/dev/null | wc -l)
        if [ "$db_count" -gt 0 ]; then
            echo -e "  ✅ 病毒Library: ${GREEN}存在 ($db_count 个File)${NC}"
            du -sh virus_database 2>/dev/null | sed 's/^/    /'
        else
            echo -e "  ⚠️  病毒Library: ${YELLOW}Directory存在但NoDataLibraryFile${NC}"
        fi
    else
        echo -e "  ❌ 病毒Library: ${RED}Directory不存在${NC}"
    fi
    
    echo
    
    # Check守护ProcessStatus
    echo "Check守护ProcessStatus:"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo -e "  ✅ ClamD: ${GREEN}Run中 (PID: $PID)${NC}"
        else
            echo -e "  ❌ ClamD: ${RED}PIDFile存在但ProcessNotRun${NC}"
        fi
    else
        echo -e "  ⚠️  ClamD: ${YELLOW}NotRun${NC}"
    fi
    
    if [ -S "$SOCKET_FILE" ]; then
        echo -e "  ✅ Socket: ${GREEN}存在${NC}"
    else
        echo -e "  ❌ Socket: ${RED}不存在${NC}"
    fi
}

# Update病毒Library
update_database() {
    echo -e "${BLUE}=== Update病毒Library ===${NC}"
    echo
    
    if [ ! -f "$FRESHCLAM_BIN" ]; then
        echo -e "${RED}Error: freshclam 不存在${NC}"
        return 1
    fi
    
    if [ ! -f "$FRESHCLAM_CONF" ]; then
        echo -e "${RED}Error: freshclam ConfigurationFile不存在${NC}"
        return 1
    fi
    
    echo "StartUpdate病毒Library..."
    if "$FRESHCLAM_BIN" --config-file="$FRESHCLAM_CONF"; then
        echo -e "${GREEN}病毒LibraryUpdateSuccess${NC}"
    else
        echo -e "${RED}病毒LibraryUpdateFailed${NC}"
        return 1
    fi
}

# Start守护Process
start_daemon() {
    echo -e "${BLUE}=== Start ClamD 守护Process ===${NC}"
    echo
    
    # Check是否Already经Run
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}ClamD Already经在Run (PID: $PID)${NC}"
            return 0
        fi
    fi
    
    if [ ! -f "$CLAMD_BIN" ]; then
        echo -e "${RED}Error: clamd 不存在${NC}"
        return 1
    fi
    
    if [ ! -f "$CLAMD_CONF" ]; then
        echo -e "${RED}Error: clamd ConfigurationFile不存在${NC}"
        return 1
    fi
    
    echo "Start ClamD 守护Process..."
    "$CLAMD_BIN" --config-file="$CLAMD_CONF"
    
    # 等待Start
    echo "等待守护ProcessStart..."
    for i in {1..10}; do
        if [ -S "$SOCKET_FILE" ]; then
            echo -e "${GREEN}ClamD StartSuccess${NC}"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    echo
    echo -e "${RED}ClamD StartFailed或超时${NC}"
    return 1
}

# Stop守护Process
stop_daemon() {
    echo -e "${BLUE}=== Stop ClamD 守护Process ===${NC}"
    echo
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo "Stop ClamD Process (PID: $PID)..."
            kill "$PID"
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                echo "强制Stop..."
                kill -9 "$PID"
            fi
            echo -e "${GREEN}ClamD AlreadyStop${NC}"
        else
            echo -e "${YELLOW}ClamD ProcessNotRun${NC}"
        fi
        rm -f "$PID_FILE"
    else
        echo -e "${YELLOW}Not找到 PID File${NC}"
    fi
    
    # CleansocketFile
    rm -f "$SOCKET_FILE"
}

# 查看守护ProcessStatus
daemon_status() {
    echo -e "${BLUE}=== ClamD Status ===${NC}"
    echo
    
    if [ -S "$SOCKET_FILE" ]; then
        echo "TestConnection..."
        if echo "PING" | nc -U "$SOCKET_FILE" 2>/dev/null | grep -q "PONG"; then
            echo -e "${GREEN}✅ 守护ProcessResponse正常${NC}"
            
            echo
            echo "VersionInformation:"
            echo "VERSION" | nc -U "$SOCKET_FILE" 2>/dev/null
            
            echo
            echo "StatisticsInformation:"
            echo "STATS" | nc -U "$SOCKET_FILE" 2>/dev/null
        else
            echo -e "${RED}❌ 守护ProcessNoResponse${NC}"
        fi
    else
        echo -e "${RED}❌ Socket File不存在，守护ProcessNotRun${NC}"
    fi
}

# 扫描File/Directory
scan_files() {
    echo -e "${BLUE}=== File扫描 ===${NC}"
    echo
    
    read -p "请Input要扫描的File或DirectoryPath: " scan_path
    
    if [ ! -e "$scan_path" ]; then
        echo -e "${RED}Error: Path不存在${NC}"
        return 1
    fi
    
    if [ ! -f "$CLAMSCAN_BIN" ]; then
        echo -e "${RED}Error: clamscan 不存在${NC}"
        return 1
    fi
    
    echo "Start扫描: $scan_path"
    echo
    
    if [ -d "$scan_path" ]; then
        "$CLAMSCAN_BIN" --database=virus_database --recursive --verbose "$scan_path"
    else
        "$CLAMSCAN_BIN" --database=virus_database --verbose "$scan_path"
    fi
}

# 快速扫描
quick_scan() {
    echo -e "${BLUE}=== 快速扫描 (ClamDScan) ===${NC}"
    echo
    
    if [ ! -S "$SOCKET_FILE" ]; then
        echo -e "${RED}Error: ClamD 守护ProcessNotRun${NC}"
        echo "请先Start守护Process (Options 3)"
        return 1
    fi
    
    read -p "请Input要扫描的File或DirectoryPath: " scan_path
    
    if [ ! -e "$scan_path" ]; then
        echo -e "${RED}Error: Path不存在${NC}"
        return 1
    fi
    
    echo "Start快速扫描: $scan_path"
    echo
    
    if [ -d "$scan_path" ]; then
        "$CLAMDSCAN_BIN" --config-file="$CLAMD_CONF" --recursive "$scan_path"
    else
        "$CLAMDSCAN_BIN" --config-file="$CLAMD_CONF" "$scan_path"
    fi
}

# RunTest
run_tests() {
    echo -e "${BLUE}=== RunTest套件 ===${NC}"
    echo
    
    echo "可用的Test:"
    echo "1) 可ExecuteFileTest"
    echo "2) FreshClam Test"
    echo "3) ClamD Test"
    echo "4) 扫描功能Test"
    echo "5) Run所HasTest"
    echo
    
    read -p "请选择Test (1-5): " test_choice
    
    case $test_choice in
        1)
            if [ -f "test_executables.sh" ]; then
                chmod +x test_executables.sh
                ./test_executables.sh
            else
                echo -e "${RED}TestScript不存在${NC}"
            fi
            ;;
        2)
            if [ -f "test_freshclam.sh" ]; then
                chmod +x test_freshclam.sh
                ./test_freshclam.sh
            else
                echo -e "${RED}TestScript不存在${NC}"
            fi
            ;;
        3)
            if [ -f "test_clamd.sh" ]; then
                chmod +x test_clamd.sh
                ./test_clamd.sh
            else
                echo -e "${RED}TestScript不存在${NC}"
            fi
            ;;
        4)
            if [ -f "test_scanning.sh" ]; then
                chmod +x test_scanning.sh
                ./test_scanning.sh
            else
                echo -e "${RED}TestScript不存在${NC}"
            fi
            ;;
        5)
            echo "Run所HasTest..."
            for script in test_executables.sh test_freshclam.sh test_clamd.sh test_scanning.sh; do
                if [ -f "$script" ]; then
                    echo -e "${PURPLE}=== Run $script ===${NC}"
                    chmod +x "$script"
                    ./"$script"
                    echo
                fi
            done
            ;;
        *)
            echo -e "${RED}No效选择${NC}"
            ;;
    esac
}

# 查看Log
view_logs() {
    echo -e "${BLUE}=== 查看Log ===${NC}"
    echo
    
    echo "可用的LogFile:"
    echo "1) ClamD Log (/tmp/clamd.log)"
    echo "2) FreshClam Log (/tmp/freshclam.log)"
    echo
    
    read -p "请选择Log (1-2): " log_choice
    
    case $log_choice in
        1)
            if [ -f "/tmp/clamd.log" ]; then
                echo -e "${GREEN}=== ClamD Log ===${NC}"
                tail -50 /tmp/clamd.log
            else
                echo -e "${YELLOW}ClamD LogFile不存在${NC}"
            fi
            ;;
        2)
            if [ -f "/tmp/freshclam.log" ]; then
                echo -e "${GREEN}=== FreshClam Log ===${NC}"
                tail -50 /tmp/freshclam.log
            else
                echo -e "${YELLOW}FreshClam LogFile不存在${NC}"
            fi
            ;;
        *)
            echo -e "${RED}No效选择${NC}"
            ;;
    esac
}

# 显示帮助
show_help() {
    echo -e "${BLUE}=== HunterMatrix 使用帮助 ===${NC}"
    echo
    echo "HunterMatrix 是一个Open Source的反病毒引擎，主要Group件Package括:"
    echo
    echo -e "${GREEN}主要Program:${NC}"
    echo "  • clamd     - 守护Process，提供实时扫描Service"
    echo "  • freshclam - 病毒LibraryUpdateTool"
    echo "  • clamscan  - Command行扫描Tool"
    echo "  • clamdscan - 守护ProcessClient扫描Tool"
    echo
    echo -e "${GREEN}使用流程:${NC}"
    echo "  1. 首先Update病毒Library (Options 2)"
    echo "  2. Start守护Process (Options 3) - 可选"
    echo "  3. 进行File扫描 (Options 6 或 7)"
    echo
    echo -e "${GREEN}ConfigurationFile:${NC}"
    echo "  • clamd.conf     - ClamD 守护ProcessConfiguration"
    echo "  • freshclam.conf - FreshClam UpdateConfiguration"
    echo
    echo -e "${GREEN}LogFile:${NC}"
    echo "  • /tmp/clamd.log     - ClamD Log"
    echo "  • /tmp/freshclam.log - FreshClam Log"
}

# 主循环
main() {
    while true; do
        show_menu
        
        case $choice in
            1) check_status ;;
            2) update_database ;;
            3) start_daemon ;;
            4) stop_daemon ;;
            5) daemon_status ;;
            6) scan_files ;;
            7) quick_scan ;;
            8) run_tests ;;
            9) view_logs ;;
            10) show_help ;;
            0) 
                echo -e "${GREEN}再见！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}No效选择，请重试${NC}"
                ;;
        esac
        
        echo
        read -p "按 Enter 键Continue..."
        echo
    done
}

# Run主Program
main
