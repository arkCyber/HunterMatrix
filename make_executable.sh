#!/bin/bash

# 为所HasScript添加ExecutePermission

echo "🔧 为 HunterMatrix Script添加ExecutePermission"
echo "=============================="
echo

# Script列Table
scripts=(
    "quick_start.sh"
    "huntermatrix_manager.sh"
    "test_executables.sh"
    "test_freshclam.sh"
    "test_clamd.sh"
    "test_scanning.sh"
    "make_executable.sh"
)

# 为每个Script添加ExecutePermission
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo "✅ $script - ExecutePermissionAlready添加"
    else
        echo "⚠️  $script - File不存在"
    fi
done

echo
echo "🎉 Complete！所HasScript现在都可以Execute了。"
echo
echo "快速Start："
echo "  ./quick_start.sh      # 一键Start HunterMatrix"
echo "  ./huntermatrix_manager.sh   # 打开管理Tool"
