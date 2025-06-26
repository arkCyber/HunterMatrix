# 🛡️ HunterMatrix Web UI - 现代化病毒扫描Tool

一个美观、现代化的HunterMatrix WebInterface，支持实时扫描进度显示和File滚动查看。

## ✨ 功能特性

### 🎨 现代化Interface设计
- **Response式布局** - 适配桌面和移动设备
- **Material Design** - 现代化的视觉设计
- **渐变色彩** - 美观的配色方案
- **流畅动画** - 丰富的交互动效

### 🔍 强大的扫描功能
- **实时进度显示** - 扫描过程可视化
- **File滚动显示** - 实时查看Processing扫描的File
- **快速扫描** - 预设常用Path一键扫描
- **Custom扫描** - 灵活选择扫描Path和Options

### 📊 SystemMonitor面板
- **CPU使用率** - 实时SystemPerformanceMonitor
- **Memory使用率** - Memory占用情况显示
- **Disk使用率** - StorageNull间使用Status
- **动态Update** - Automatic刷新SystemInformation

### 📋 扫描历史管理
- **历史Record** - Save最近20次扫描Record
- **详细Information** - 扫描Path、FileQuantity、威胁Statistics
- **本地Storage** - DataSave在浏览器本地

### ⚙️ 灵活SettingsOptions
- **扫描Options** - 递归扫描、压缩File扫描等
- **UpdateSettings** - 病毒LibraryAutomaticUpdateConfiguration
- **InterfaceSettings** - Theme切换等个性化Options

## 🚀 快速Start

### Method1: 一键Start（推荐）

```bash
# 进入Web UIDirectory
cd huntermatrix-main/web-ui

# 给Script添加ExecutePermission
chmod +x start.sh

# StartWebInterface
./start.sh
```

### Method2: PythonService器

```bash
# 使用Python内置Service器
python3 start_server.py

# 或者使用简单HTTPService器
python3 -m http.server 8080
```

### Method3: Node.jsService器

```bash
# Installhttp-server (如果NotInstall)
npm install -g http-server

# Start Service器
http-server . -p 8080 -o --cors
```

## 🎯 使用说明

### 1. StartInterface
RunStartScript后，浏览器会Automatic打开WebInterface。如果没HasAutomatic打开，请Manual访问 `http://localhost:8080`

### 2. 快速扫描
在首页点击快速OperationButton：
- 📁 DownloadFile夹
- 🖥️ 桌面
- 📄 Documentation
- 💾 ApplicationProgram

### 3. Custom扫描
1. 切换到"扫描"页面
2. 点击"浏览"选择扫描Path
3. Configuration扫描Options
4. 点击"Start扫描"

### 4. 实时Monitor
扫描过程中可以看到：
- 📊 实时进度条
- 📁 当前扫描File
- 📈 扫描StatisticsInformation
- 📜 File滚动列Table

### 5. 查看历史
在"历史"页面查看之前的扫描Record和Result

## ⌨️ 快捷键

- `Ctrl/Cmd + R` - 刷新Data
- `Ctrl/Cmd + U` - Update病毒Library
- `Escape` - Stop当前扫描
- `1-4` - 快速切换页面

## 🔧 Debug功能

### Development者Tool
按 `F12` 打开浏览器Development者Tool：
- **Console** - 查看JavaScriptLog
- **Network** - MonitorNetworkRequest
- **Elements** - CheckHTML结构
- **Sources** - DebugJavaScriptCode

### ConsoleCommand
在浏览器Console中可以使用：
```javascript
// 访问ApplicationInstance
window.huntermatrixUI

// Manual触发扫描
window.huntermatrixUI.startQuickScan('/path/to/scan')

// 切换页面
window.huntermatrixUI.switchPage('scan')

// 显示通知
window.huntermatrixUI.showNotification('Test消息', 'success')
```

## 📁 File结构

```
web-ui/
├── index.html          # 主HTMLFile
├── styles.css          # CSSStyleFile
├── script.js           # JavaScript功能File
├── start_server.py     # PythonStart Service器
├── start.sh           # StartScript
└── README.md          # 说明Documentation
```

## 🎨 Interface预览

### 仪Table板页面
- SystemStatus卡片
- 实时Monitor面板
- 快速OperationButton

### 扫描页面
- Path选择器
- 扫描OptionsConfiguration
- 实时进度显示
- File滚动列Table

### 历史页面
- 扫描Record列Table
- 详细StatisticsInformation
- Status指示器

### Settings页面
- 病毒LibrarySettings
- 扫描OptionsConfiguration
- Interface个性化

## 🔄 Data模拟

由于这是WebDemoVersion，所HasData都是模拟的：
- **SystemMonitor** - 随机生成的CPU/Memory/Disk使用率
- **扫描进度** - 模拟的File扫描过程
- **威胁Detection** - 随机生成的威胁（2%概率）
- **病毒Library** - 模拟的病毒FeatureQuantity

## 🌐 浏览器兼容性

支持所Has现代浏览器：
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## 📱 Response式设计

Interface完全Response式，支持：
- 🖥️ 桌面电脑 (1200px+)
- 💻 笔记本电脑 (768px-1199px)
- 📱 平板设备 (480px-767px)
- 📱 手机设备 (<480px)

## 🎯 技术特性

### 前端技术
- **纯HTML/CSS/JavaScript** - NoFramework依赖
- **CSS Grid & Flexbox** - 现代布局技术
- **CSS动画** - 流畅的视觉效果
- **LocalStorage** - 本地Data持久化

### 交互特性
- **事件驱动** - Response式User交互
- **实时Update** - 动态Content刷新
- **键盘支持** - 快捷键Operation
- **通知System** - User反馈机制

## 🚀 PerformanceOptimization

- **轻量级** - No外部依赖
- **快速Load** - Optimization的资源Size
- **流畅动画** - GPU加速的CSS动画
- **Memory友好** - 合理的Data管理

## 🔮 Not来计划

- [ ] 深色Theme支持
- [ ] 多Language国际化
- [ ] 更多扫描Options
- [ ] Export扫描Report
- [ ] WebSocket实时通信
- [ ] PWA支持

---

🎉 **享受现代化的HunterMatrix扫描体验！**

如Has问题或建议，请使用浏览器Development者Tool进行Debug。
