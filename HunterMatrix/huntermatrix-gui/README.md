# 🛡️ HunterMatrix Scanner - 现代化病毒扫描Tool

一个使用 Tauri + React + TypeScript Build的现代化 HunterMatrix 图形UserInterface。

## ✨ 功能特性

### 🎨 现代化Interface
- **Response式设计** - 适配不同屏幕尺寸
- **Material Design** - 美观的现代Interface
- **实时反馈** - 扫描进度和Status实时显示
- **中文Interface** - 完全本地化的User体验

### 🔍 强大的扫描功能
- **快速扫描** - 预设常用扫描Path
- **Custom扫描** - 选择任意File夹进行扫描
- **实时Monitor** - 扫描进度实时显示
- **详细Report** - 完整的扫描Result和威胁详情

### 🦠 病毒Library管理
- **AutomaticUpdate** - 一键Update病毒FeatureLibrary
- **本地Cache** - 病毒Library本地Storage，提高扫描速度
- **Version显示** - 实时显示病毒LibraryVersion和UpdateStatus

### 📊 StatusMonitor
- **SystemStatus** - 实时显示SecurityStatus
- **扫描历史** - Record扫描历史和Result
- **PerformanceMonitor** - 显示扫描PerformanceMetric

## 🚀 快速Start

### 环境要求

- **macOS** 10.13 或更高Version
- **Node.js** 18+ 
- **Rust** 1.70+
- **HunterMatrix** AlreadyInstall (通过项目Build或 Homebrew)

### Install依赖

```bash
# Install前端依赖
pnpm install

# Install HunterMatrix (如果NotInstall)
brew install huntermatrix
```

### Development模式

```bash
# StartDevelopmentService器
pnpm tauri dev
```

### Build生产Version

```bash
# BuildApplicationProgram
pnpm tauri build
```

## 📁 项目结构

```
huntermatrix-gui/
├── src/                    # React 前端源码
│   ├── App.tsx            # 主ApplicationGroup件
│   ├── index.css          # StyleFile
│   └── main.tsx           # Application入口
├── src-tauri/             # Tauri 后端源码
│   ├── src/
│   │   └── main.rs        # Rust 后端逻辑
│   ├── Cargo.toml         # Rust 依赖Configuration
│   └── tauri.conf.json    # Tauri ApplicationConfiguration
├── virus_database/        # 本地病毒LibraryFile
├── package.json           # Node.js 依赖Configuration
└── tailwind.config.js     # Tailwind CSS Configuration
```

## 🎯 使用Guide

### 1️⃣ StartApplicationProgram

```bash
# Development模式
pnpm tauri dev

# 或RunBuild后的ApplicationProgram
./src-tauri/target/release/huntermatrix-gui
```

### 2️⃣ Update病毒Library

1. 点击ApplicationProgram中的 **"Update病毒Library"** Button
2. 等待DownloadComplete
3. System会显示UpdateStatus

### 3️⃣ Start扫描

#### 快速扫描
- **扫描Download** - 扫描 `~/Downloads` File夹
- **扫描ApplicationProgram** - 扫描 `/Applications` File夹

#### Custom扫描
1. 点击 **"Custom扫描"** Button
2. 在File选择器中选择要扫描的File夹
3. 点击确认Start扫描

### 4️⃣ 查看Result

- **扫描Status** - Security/威胁/ErrorStatus显示
- **详细Information** - 扫描FileQuantity、Found威胁Quantity
- **威胁详情** - 具体的威胁File和Type
- **扫描Log** - 完整的扫描LogFile

## 🔧 技术栈

### 前端
- **React 18** - UserInterfaceFramework
- **TypeScript** - TypeSecurity的 JavaScript
- **Tailwind CSS** - 实用优先的 CSS Framework
- **Lucide React** - 现代IconLibrary
- **Vite** - 快速BuildTool

### 后端
- **Tauri 2.0** - Rust 驱动的桌面ApplicationFramework
- **Rust** - System级ProgrammingLanguage
- **Serde** - 序列化Framework
- **Tokio** - AsyncRun时

### 集成
- **HunterMatrix** - Open Source防病毒引擎
- **FreshClam** - 病毒LibraryUpdateTool

## 📦 BuildDistribution

### CreateInstallPackage

```bash
# Build所HasPlatform的InstallPackage
pnpm tauri build

# 仅Build macOS Version
pnpm tauri build --target universal-apple-darwin
```

### 生成的File

- **macOS**: `src-tauri/target/release/bundle/macos/HunterMatrix Scanner.app`
- **DMG**: `src-tauri/target/release/bundle/dmg/HunterMatrix Scanner_1.0.0_universal.dmg`

## 🔧 ConfigurationOptions

### 病毒LibraryConfiguration

Edit `virus_database/freshclam.conf`:

```conf
# Custom镜像Service器
DatabaseMirror your-mirror.example.com

# Update频率
Checks 12

# 代理Settings
HTTPProxyServer proxy.example.com
HTTPProxyPort 8080
```

### ApplicationProgramConfiguration

Edit `src-tauri/tauri.conf.json`:

```json
{
  "app": {
    "windows": [{
      "width": 1400,
      "height": 900,
      "title": "Custom标题"
    }]
  }
}
```

## 🚨 故障排除

### 常见问题

1. **HunterMatrix Not找到**
   ```bash
   # Install HunterMatrix
   brew install huntermatrix
   
   # CheckInstall
   which clamscan
   ```

2. **病毒LibraryUpdateFailed**
   ```bash
   # ManualUpdate
   sudo freshclam
   
   # CheckNetworkConnection
   ping database.huntermatrix.net
   ```

3. **BuildFailed**
   ```bash
   # CleanCache
   pnpm clean
   rm -rf node_modules
   pnpm install
   
   # 重新Build
   pnpm tauri build
   ```

### Log位置

- **ApplicationProgramLog**: `~/Library/Logs/HunterMatrix Scanner/`
- **扫描Log**: `/tmp/huntermatrix_scan_*.log`
- **病毒LibraryLog**: `virus_database/freshclam.log`

## 🤝 贡献Guide

1. Fork 项目
2. Create功能Branch: `git checkout -b feature/AmazingFeature`
3. Commit更改: `git commit -m 'Add some AmazingFeature'`
4. PushBranch: `git push origin feature/AmazingFeature`
5. 打开 Pull Request

## 📄 License证

本项目采用 GPL-2.0 License证 - 查看 [LICENSE](LICENSE) File了解详情。

## 🙏 致谢

- [HunterMatrix](https://www.huntermatrix.net/) - 强大的Open Source防病毒引擎
- [Tauri](https://tauri.app/) - 现代桌面ApplicationFramework
- [React](https://reactjs.org/) - UserInterfaceLibrary
- [Tailwind CSS](https://tailwindcss.com/) - CSS Framework

---

**享受Security的Calculate体验！** 🛡️✨
