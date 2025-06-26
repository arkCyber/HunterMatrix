import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { dialog } from '@tauri-apps/plugin-dialog';
import { listen } from '@tauri-apps/api/event';
import {
    Shield,
    ShieldCheck,
    ShieldAlert,
    Scan,
    Download,
    Settings,
    FolderOpen,
    FileText,
    Clock,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Loader2,
    Home,
    TrendingUp,
    Database,
    Play,
    Pause,
    RotateCcw,
    Info,
    Monitor,
    HardDrive,
    Wifi,
    Users,
    Zap,
    Activity,
    Search,
    Cpu,
    MemoryStick,
    X,
    RefreshCw,
    Trash2
} from 'lucide-react';
import clsx from 'clsx';

// 接口定义
interface ScanResult {
    status: 'safe' | 'infected' | 'error';
    files_scanned: number;
    threats_found: number;
    scan_time: string;
    log_path?: string;
    details?: string[];
    path: string;
    timestamp: string;
}

interface DatabaseStatus {
    version: string;
    last_update: string;
    signatures: number;
}

interface ScanHistory {
    id: string;
    path: string;
    result: ScanResult;
    timestamp: string;
}

interface SystemInfo {
    platform: string;
    memory_usage: number;
    disk_usage: number;
    cpu_usage: number;
}

function App() {
    // 状态管理
    const [currentView, setCurrentView] = useState<'home' | 'scan' | 'settings' | 'history'>('home');
    const [isScanning, setIsScanning] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [currentScanFile, setCurrentScanFile] = useState<string>('');
    const [scanResult, setScanResult] = useState<ScanResult | null>(null);
    const [dbStatus, setDbStatus] = useState<DatabaseStatus | null>(null);
    const [selectedPath, setSelectedPath] = useState<string>('');
    const [scanHistory, setScanHistory] = useState<ScanHistory[]>([]);
    const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
    const [notifications, setNotifications] = useState<Array<{ id: string, type: 'success' | 'error' | 'info', message: string }>>([]);

    // 快速扫描选项
    const quickScanOptions = [
        { name: '下载文件夹', path: '/Users/arkSong/Downloads', icon: Download },
        { name: '桌面', path: '/Users/arkSong/Desktop', icon: Monitor },
        { name: '文档', path: '/Users/arkSong/Documents', icon: FileText },
        { name: '应用程序', path: '/Applications', icon: HardDrive }
    ];

    // 获取数据库状态
    useEffect(() => {
        loadDatabaseStatus();
        loadSystemInfo();
        loadScanHistory();

        // 监听扫描进度事件
        const unlisten = listen('scan-progress', (event: any) => {
            setScanProgress(event.payload.progress);
            setCurrentScanFile(event.payload.currentFile);
        });

        return () => {
            unlisten.then(fn => fn());
        };
    }, []);

    // 添加通知
    const addNotification = (type: 'success' | 'error' | 'info', message: string) => {
        const id = Date.now().toString();
        setNotifications(prev => [...prev, { id, type, message }]);
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
        }, 5000);
    };

    const loadDatabaseStatus = async () => {
        try {
            const status = await invoke<DatabaseStatus>('get_database_status');
            setDbStatus(status);
        } catch (error) {
            console.error('获取数据库状态失败:', error);
            addNotification('error', '无法获取病毒库状态');
        }
    };

    const loadSystemInfo = async () => {
        try {
            const info = await invoke<SystemInfo>('get_system_info');
            setSystemInfo(info);
        } catch (error) {
            console.error('获取系统信息失败:', error);
        }
    };

    const loadScanHistory = () => {
        // 从本地存储加载扫描历史
        const saved = localStorage.getItem('scan_history');
        if (saved) {
            setScanHistory(JSON.parse(saved));
        }
    };

    const saveScanHistory = (result: ScanResult) => {
        const historyItem: ScanHistory = {
            id: Date.now().toString(),
            path: result.path,
            result,
            timestamp: new Date().toISOString()
        };

        const newHistory = [historyItem, ...scanHistory].slice(0, 20); // 保留最近20条
        setScanHistory(newHistory);
        localStorage.setItem('scan_history', JSON.stringify(newHistory));
    };

    const handleUpdateDatabase = async () => {
        setIsUpdating(true);
        try {
            const result = await invoke<string>('update_virus_database');
            addNotification('success', result);
            await loadDatabaseStatus();
        } catch (error) {
            addNotification('error', `更新失败: ${error}`);
        } finally {
            setIsUpdating(false);
        }
    };

    const handleSelectFolder = async () => {
        try {
            const selected = await dialog.open({
                directory: true,
                multiple: false,
                title: '选择要扫描的文件夹'
            });

            if (selected && typeof selected === 'string') {
                setSelectedPath(selected);
            }
        } catch (error) {
            addNotification('error', '选择文件夹失败');
        }
    };

    const handleQuickScan = async (path: string) => {
        await performScan(path);
    };

    const handleCustomScan = async () => {
        if (!selectedPath) {
            addNotification('error', '请先选择要扫描的路径');
            return;
        }
        await performScan(selectedPath);
    };

    const performScan = async (path: string) => {
        setIsScanning(true);
        setScanProgress(0);
        setCurrentScanFile('');
        setScanResult(null);

        try {
            const result = await invoke<ScanResult>('start_scan', { path });
            setScanResult(result);
            saveScanHistory(result);

            if (result.status === 'infected') {
                addNotification('error', `发现 ${result.threats_found} 个威胁!`);
            } else if (result.status === 'safe') {
                addNotification('success', '扫描完成，未发现威胁');
            } else {
                addNotification('error', '扫描过程中出现错误');
            }
        } catch (error) {
            addNotification('error', `扫描失败: ${error}`);
        } finally {
            setIsScanning(false);
            setScanProgress(0);
            setCurrentScanFile('');
        }
    };

    // 渲染现代化首页视图
    const renderHomeView = () => (
        <div className="space-y-8">
            {/* 现代化系统状态卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="group relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-green-500 rounded-3xl blur opacity-20 group-hover:opacity-30 transition-opacity"></div>
                    <div className="relative bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105">
                        <div className="flex items-center justify-between">
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-gray-800">安全状态</h3>
                                <p className="text-emerald-600 font-semibold">系统受保护</p>
                                <div className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                                    <span className="text-sm text-gray-500">实时监控中</span>
                                </div>
                            </div>
                            <div className="relative">
                                <div className="absolute inset-0 bg-emerald-400 rounded-2xl blur opacity-30"></div>
                                <div className="relative bg-gradient-to-br from-emerald-400 to-green-500 p-4 rounded-2xl">
                                    <ShieldCheck className="h-12 w-12 text-white" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="group relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-3xl blur opacity-20 group-hover:opacity-30 transition-opacity"></div>
                    <div className="relative bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105">
                        <div className="flex items-center justify-between">
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-gray-800">病毒库</h3>
                                <p className="text-blue-600 font-bold text-lg">
                                    {dbStatus?.signatures.toLocaleString() || '未知'}
                                </p>
                                <p className="text-sm text-gray-500">{dbStatus?.version || 'ClamAV 1.5.0-beta'}</p>
                                <p className="text-xs text-blue-500">
                                    更新: {dbStatus?.last_update || '检查中...'}
                                </p>
                            </div>
                            <div className="relative">
                                <div className="absolute inset-0 bg-blue-400 rounded-2xl blur opacity-30"></div>
                                <div className="relative bg-gradient-to-br from-blue-400 to-indigo-500 p-4 rounded-2xl">
                                    <Database className="h-12 w-12 text-white" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="group relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-400 to-violet-500 rounded-3xl blur opacity-20 group-hover:opacity-30 transition-opacity"></div>
                    <div className="relative bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105">
                        <div className="flex items-center justify-between">
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-gray-800">扫描历史</h3>
                                <p className="text-purple-600 font-bold text-lg">{scanHistory.length}</p>
                                <p className="text-sm text-gray-500">次扫描记录</p>
                                <div className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                                    <span className="text-xs text-gray-400">最近活动</span>
                                </div>
                            </div>
                            <div className="relative">
                                <div className="absolute inset-0 bg-purple-400 rounded-2xl blur opacity-30"></div>
                                <div className="relative bg-gradient-to-br from-purple-400 to-violet-500 p-4 rounded-2xl">
                                    <Activity className="h-12 w-12 text-white" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 现代化快速操作区 */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/10 to-blue-500/10 rounded-3xl"></div>
                <div className="relative bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl">
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center space-x-4">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-2xl blur opacity-30"></div>
                                <div className="relative bg-gradient-to-r from-yellow-400 to-orange-500 p-3 rounded-2xl">
                                    <Zap className="h-6 w-6 text-white" />
                                </div>
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                                    快速扫描
                                </h2>
                                <p className="text-gray-500">一键扫描常用文件夹</p>
                            </div>
                        </div>
                        <div className="hidden md:flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            <span className="text-sm text-gray-500">准备就绪</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {quickScanOptions.map((option, index) => (
                            <button
                                key={option.path}
                                onClick={() => handleQuickScan(option.path)}
                                disabled={isScanning}
                                className="group relative overflow-hidden transform hover:scale-105 transition-all duration-300 disabled:opacity-50"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-indigo-500/20 rounded-2xl blur group-hover:blur-lg transition-all"></div>
                                <div className="relative bg-white/70 backdrop-blur-sm border border-white/30 rounded-2xl p-6 shadow-lg group-hover:shadow-2xl transition-all duration-300">
                                    <div className="flex flex-col items-center space-y-4">
                                        <div className="relative">
                                            <div className="absolute inset-0 bg-blue-400 rounded-xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
                                            <div className="relative bg-gradient-to-br from-blue-400 to-indigo-500 p-4 rounded-xl group-hover:from-blue-500 group-hover:to-indigo-600 transition-all">
                                                <option.icon className="h-8 w-8 text-white" />
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <h3 className="font-bold text-gray-800 mb-1">{option.name}</h3>
                                            <p className="text-xs text-gray-500 mb-2">
                                                {option.path.split('/').pop()}
                                            </p>
                                            <div className="flex items-center justify-center space-x-1">
                                                <Play className="h-3 w-3 text-blue-500" />
                                                <span className="text-xs text-blue-600 font-medium">扫描</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* 现代化自定义扫描区 */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-400/10 to-teal-500/10 rounded-3xl"></div>
                <div className="relative bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl">
                    <div className="flex items-center space-x-4 mb-8">
                        <div className="relative">
                            <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-2xl blur opacity-30"></div>
                            <div className="relative bg-gradient-to-r from-emerald-400 to-teal-500 p-3 rounded-2xl">
                                <FolderOpen className="h-6 w-6 text-white" />
                            </div>
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                                自定义扫描
                            </h2>
                            <p className="text-gray-500">选择任意路径进行深度扫描</p>
                        </div>
                    </div>

                    <div className="flex flex-col lg:flex-row gap-6">
                        <div className="flex-1 space-y-4">
                            <label className="block text-sm font-semibold text-gray-700">
                                扫描路径
                            </label>
                            <div className="relative">
                                <input
                                    type="text"
                                    value={selectedPath}
                                    onChange={(e) => setSelectedPath(e.target.value)}
                                    placeholder="输入完整路径或点击浏览选择..."
                                    className="w-full px-6 py-4 bg-white/70 backdrop-blur-sm border border-white/30 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-gray-800 placeholder-gray-400 shadow-lg"
                                    disabled={isScanning}
                                />
                                <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                                    <FolderOpen className="h-5 w-5 text-gray-400" />
                                </div>
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-4 lg:flex-col lg:w-64">
                            <button
                                onClick={handleSelectFolder}
                                disabled={isScanning}
                                className="flex items-center justify-center px-6 py-4 bg-white/70 backdrop-blur-sm border border-white/30 rounded-2xl text-gray-700 hover:bg-white/90 transition-all disabled:opacity-50 shadow-lg hover:shadow-xl transform hover:scale-105"
                            >
                                <FolderOpen className="h-5 w-5 mr-2" />
                                浏览文件夹
                            </button>

                            <button
                                onClick={handleCustomScan}
                                disabled={isScanning || !selectedPath}
                                className="relative overflow-hidden flex items-center justify-center px-8 py-4 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-600 hover:via-teal-600 hover:to-cyan-600 text-white font-bold rounded-2xl transition-all duration-300 disabled:opacity-50 shadow-xl hover:shadow-2xl transform hover:scale-105"
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent opacity-0 hover:opacity-100 transition-opacity"></div>
                                {isScanning ? (
                                    <>
                                        <Loader2 className="h-6 w-6 mr-3 animate-spin" />
                                        扫描中...
                                    </>
                                ) : (
                                    <>
                                        <Play className="h-6 w-6 mr-3" />
                                        🚀 开始扫描
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 现代化扫描进度显示窗口 */}
            {isScanning && (
                <div className="relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-500/20 rounded-3xl animate-pulse"></div>
                    <div className="relative bg-white/90 backdrop-blur-xl border border-white/30 rounded-3xl p-10 shadow-2xl">
                        <div className="text-center mb-8">
                            <div className="relative inline-flex items-center justify-center w-20 h-20 mb-6">
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full blur opacity-30"></div>
                                <div className="relative bg-gradient-to-r from-blue-500 to-purple-600 p-5 rounded-full">
                                    <Loader2 className="h-10 w-10 text-white animate-spin" />
                                </div>
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-20 rounded-full animate-pulse"></div>
                            </div>
                            <h3 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
                                正在扫描中
                            </h3>
                            <p className="text-gray-600 text-lg">AI驱动的威胁检测正在进行</p>
                        </div>

                        <div className="space-y-8">
                            {/* 现代化进度条 */}
                            <div className="relative">
                                <div className="w-full bg-gray-200/60 rounded-2xl h-8 overflow-hidden backdrop-blur-sm">
                                    <div
                                        className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 h-8 rounded-2xl transition-all duration-700 relative overflow-hidden"
                                        style={{ width: `${scanProgress}%` }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-50 animate-shimmer"></div>
                                        <div className="absolute inset-0 bg-gradient-to-r from-blue-400/50 to-purple-400/50 animate-pulse"></div>
                                    </div>
                                </div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <span className="text-sm font-bold text-white drop-shadow-lg">
                                        {scanProgress.toFixed(1)}%
                                    </span>
                                </div>
                            </div>

                            {/* 现代化扫描详情 */}
                            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/30 shadow-lg">
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <div className="space-y-3">
                                        <div className="flex items-center space-x-2">
                                            <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                                            <h4 className="font-semibold text-gray-800">当前扫描</h4>
                                        </div>
                                        <div className="bg-white/80 backdrop-blur-sm p-4 rounded-xl border border-white/40 shadow-sm">
                                            <p className="text-sm text-gray-700 break-all font-mono">
                                                {currentScanFile || '初始化扫描引擎...'}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="flex items-center space-x-2">
                                            <div className="w-3 h-3 bg-emerald-500 rounded-full animate-bounce"></div>
                                            <h4 className="font-semibold text-gray-800">扫描状态</h4>
                                        </div>
                                        <div className="bg-white/80 backdrop-blur-sm p-4 rounded-xl border border-white/40 shadow-sm">
                                            <div className="flex items-center space-x-3">
                                                <Activity className="h-5 w-5 text-emerald-500 animate-pulse" />
                                                <span className="text-emerald-600 font-semibold">深度扫描进行中</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* 现代化实时统计 */}
                            <div className="grid grid-cols-3 gap-6">
                                <div className="group relative overflow-hidden">
                                    <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-indigo-500/20 rounded-2xl blur group-hover:blur-lg transition-all"></div>
                                    <div className="relative bg-white/70 backdrop-blur-sm border border-white/30 rounded-2xl p-6 text-center shadow-lg hover:shadow-xl transition-all">
                                        <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
                                            {scanProgress.toFixed(0)}%
                                        </div>
                                        <div className="text-sm text-gray-600 font-medium">扫描进度</div>
                                        <div className="mt-2 w-full bg-blue-200/50 rounded-full h-1">
                                            <div
                                                className="bg-gradient-to-r from-blue-500 to-indigo-500 h-1 rounded-full transition-all duration-500"
                                                style={{ width: `${scanProgress}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>

                                <div className="group relative overflow-hidden">
                                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-400/20 to-green-500/20 rounded-2xl blur group-hover:blur-lg transition-all"></div>
                                    <div className="relative bg-white/70 backdrop-blur-sm border border-white/30 rounded-2xl p-6 text-center shadow-lg hover:shadow-xl transition-all">
                                        <div className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-green-600 bg-clip-text text-transparent mb-2">
                                            0
                                        </div>
                                        <div className="text-sm text-gray-600 font-medium">发现威胁</div>
                                        <div className="mt-2 flex items-center justify-center">
                                            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                                        </div>
                                    </div>
                                </div>

                                <div className="group relative overflow-hidden">
                                    <div className="absolute inset-0 bg-gradient-to-br from-purple-400/20 to-violet-500/20 rounded-2xl blur group-hover:blur-lg transition-all"></div>
                                    <div className="relative bg-white/70 backdrop-blur-sm border border-white/30 rounded-2xl p-6 text-center shadow-lg hover:shadow-xl transition-all">
                                        <div className="text-3xl font-bold text-purple-600 mb-2">
                                            <Loader2 className="h-8 w-8 mx-auto animate-spin" />
                                        </div>
                                        <div className="text-sm text-gray-600 font-medium">实时监控</div>
                                        <div className="mt-2 text-xs text-purple-500">AI驱动</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 扫描结果 */}
            {scanResult && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">最近扫描结果</h3>
                    <div className={clsx(
                        'p-4 rounded-lg',
                        scanResult.status === 'safe' && 'bg-green-50 border border-green-200',
                        scanResult.status === 'infected' && 'bg-red-50 border border-red-200',
                        scanResult.status === 'error' && 'bg-yellow-50 border border-yellow-200'
                    )}>
                        <div className="flex items-start space-x-3">
                            {scanResult.status === 'safe' && <CheckCircle className="h-6 w-6 text-green-500 mt-0.5" />}
                            {scanResult.status === 'infected' && <XCircle className="h-6 w-6 text-red-500 mt-0.5" />}
                            {scanResult.status === 'error' && <AlertTriangle className="h-6 w-6 text-yellow-500 mt-0.5" />}

                            <div className="flex-1">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    <div>
                                        <span className="font-medium">扫描文件:</span>
                                        <p className="text-gray-600">{scanResult.files_scanned}</p>
                                    </div>
                                    <div>
                                        <span className="font-medium">发现威胁:</span>
                                        <p className="text-gray-600">{scanResult.threats_found}</p>
                                    </div>
                                    <div>
                                        <span className="font-medium">用时:</span>
                                        <p className="text-gray-600">{scanResult.scan_time}</p>
                                    </div>
                                    <div>
                                        <span className="font-medium">路径:</span>
                                        <p className="text-gray-600 truncate">{scanResult.path}</p>
                                    </div>
                                </div>

                                {scanResult.details && scanResult.details.length > 0 && (
                                    <div className="mt-4">
                                        <h4 className="font-medium text-gray-900 mb-2">详细信息:</h4>
                                        <div className="bg-gray-50 p-3 rounded text-xs font-mono max-h-40 overflow-y-auto">
                                            {scanResult.details.map((detail, index) => (
                                                <div key={index} className="text-gray-700">{detail}</div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 更新病毒库 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">病毒库更新</h3>
                        <p className="text-gray-600">
                            {dbStatus && `当前版本: ${dbStatus.version} | 最后更新: ${dbStatus.last_update}`}
                        </p>
                    </div>
                    <button
                        onClick={handleUpdateDatabase}
                        disabled={isUpdating}
                        className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center"
                    >
                        {isUpdating ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                更新中
                            </>
                        ) : (
                            <>
                                <Download className="h-4 w-4 mr-2" />
                                立即更新
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );

    // 渲染扫描页面
    const renderScanView = () => (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                    <Scan className="h-7 w-7 mr-3 text-blue-500" />
                    高级扫描选项
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 快速扫描区域 */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-800">快速扫描</h3>
                        <div className="space-y-2">
                            {quickScanOptions.map((option) => (
                                <button
                                    key={option.path}
                                    onClick={() => handleQuickScan(option.path)}
                                    disabled={isScanning}
                                    className="w-full flex items-center p-4 bg-gray-50 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 border border-gray-200 hover:border-blue-200"
                                >
                                    <option.icon className="h-6 w-6 text-blue-500 mr-3" />
                                    <div className="text-left">
                                        <div className="font-medium text-gray-900">{option.name}</div>
                                        <div className="text-sm text-gray-500">{option.path}</div>
                                    </div>
                                    <Play className="h-4 w-4 text-gray-400 ml-auto" />
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* 自定义扫描区域 */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-800">自定义扫描</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    选择扫描路径
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={selectedPath}
                                        onChange={(e) => setSelectedPath(e.target.value)}
                                        placeholder="输入或选择路径..."
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        disabled={isScanning}
                                    />
                                    <button
                                        onClick={handleSelectFolder}
                                        disabled={isScanning}
                                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors disabled:opacity-50"
                                    >
                                        <FolderOpen className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>

                            <button
                                onClick={handleCustomScan}
                                disabled={isScanning || !selectedPath}
                                className="w-full px-8 py-4 bg-gradient-to-r from-green-600 via-green-700 to-green-800 hover:from-green-700 hover:via-green-800 hover:to-green-900 text-white text-xl font-bold rounded-xl transition-all duration-300 disabled:opacity-50 flex items-center justify-center shadow-xl hover:shadow-2xl transform hover:scale-105"
                            >
                                {isScanning ? (
                                    <>
                                        <Loader2 className="h-7 w-7 mr-3 animate-spin" />
                                        🔍 正在扫描中...
                                    </>
                                ) : (
                                    <>
                                        <Scan className="h-7 w-7 mr-3" />
                                        🔍 开始高级扫描
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 系统信息 */}
            {systemInfo && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">系统监控</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                            <Monitor className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                            <div className="text-2xl font-bold text-blue-600">{systemInfo.cpu_usage}%</div>
                            <div className="text-sm text-gray-600">CPU 使用率</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                            <HardDrive className="h-8 w-8 text-green-500 mx-auto mb-2" />
                            <div className="text-2xl font-bold text-green-600">{systemInfo.memory_usage}%</div>
                            <div className="text-sm text-gray-600">内存使用率</div>
                        </div>
                        <div className="text-center p-4 bg-purple-50 rounded-lg">
                            <Database className="h-8 w-8 text-purple-500 mx-auto mb-2" />
                            <div className="text-2xl font-bold text-purple-600">{systemInfo.disk_usage}%</div>
                            <div className="text-sm text-gray-600">磁盘使用率</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    // 渲染扫描历史页面
    const renderHistoryView = () => (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                        <Clock className="h-7 w-7 mr-3 text-green-500" />
                        扫描历史
                    </h2>
                    <button
                        onClick={() => {
                            setScanHistory([]);
                            localStorage.removeItem('scan_history');
                        }}
                        className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                        清空历史
                    </button>
                </div>

                {scanHistory.length === 0 ? (
                    <div className="text-center py-12">
                        <Clock className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">暂无扫描历史</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {scanHistory.map((item) => (
                            <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-2">
                                            {item.result.status === 'safe' && <CheckCircle className="h-5 w-5 text-green-500" />}
                                            {item.result.status === 'infected' && <XCircle className="h-5 w-5 text-red-500" />}
                                            {item.result.status === 'error' && <AlertTriangle className="h-5 w-5 text-yellow-500" />}
                                            <span className="font-medium text-gray-900">{item.path}</span>
                                        </div>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                                            <div>文件: {item.result.files_scanned}</div>
                                            <div>威胁: {item.result.threats_found}</div>
                                            <div>用时: {item.result.scan_time}</div>
                                            <div>时间: {new Date(item.timestamp).toLocaleString()}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );

    // 渲染设置页面
    const renderSettingsView = () => (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                    <Settings className="h-7 w-7 mr-3 text-gray-500" />
                    应用设置
                </h2>

                <div className="space-y-6">
                    {/* 病毒库设置 */}
                    <div className="border-b border-gray-200 pb-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">病毒库设置</h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-medium text-gray-900">自动更新病毒库</h4>
                                    <p className="text-sm text-gray-600">定期自动更新病毒特征库</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" defaultChecked />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <span className="font-medium">当前版本:</span>
                                        <p className="text-gray-600">{dbStatus?.version || '加载中...'}</p>
                                    </div>
                                    <div>
                                        <span className="font-medium">特征数量:</span>
                                        <p className="text-gray-600">{dbStatus?.signatures.toLocaleString() || '加载中...'}</p>
                                    </div>
                                    <div>
                                        <span className="font-medium">最后更新:</span>
                                        <p className="text-gray-600">{dbStatus?.last_update || '加载中...'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 扫描设置 */}
                    <div className="border-b border-gray-200 pb-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">扫描设置</h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-medium text-gray-900">实时保护</h4>
                                    <p className="text-sm text-gray-600">监控文件系统变化</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-medium text-gray-900">启动时扫描</h4>
                                    <p className="text-sm text-gray-600">应用启动时执行快速扫描</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* 系统信息 */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">系统信息</h3>
                        <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="font-medium">操作系统:</span>
                                    <p className="text-gray-600">{systemInfo?.platform || 'macOS'}</p>
                                </div>
                                <div>
                                    <span className="font-medium">ClamAV 版本:</span>
                                    <p className="text-gray-600">1.5.0-beta</p>
                                </div>
                                <div>
                                    <span className="font-medium">应用版本:</span>
                                    <p className="text-gray-600">1.0.0</p>
                                </div>
                                <div>
                                    <span className="font-medium">配置路径:</span>
                                    <p className="text-gray-600">/Users/arkSong/clamav-main</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50">
            {/* 通知栏 */}
            <div className="fixed top-4 right-4 z-50 space-y-2">
                {notifications.map((notification) => (
                    <div
                        key={notification.id}
                        className={clsx(
                            'px-4 py-3 rounded-lg shadow-lg transform transition-all duration-300',
                            notification.type === 'success' && 'bg-green-500 text-white',
                            notification.type === 'error' && 'bg-red-500 text-white',
                            notification.type === 'info' && 'bg-blue-500 text-white'
                        )}
                    >
                        <div className="flex items-center space-x-2">
                            {notification.type === 'success' && <CheckCircle className="h-5 w-5" />}
                            {notification.type === 'error' && <XCircle className="h-5 w-5" />}
                            {notification.type === 'info' && <Info className="h-5 w-5" />}
                            <span className="text-sm font-medium">{notification.message}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* 顶部导航栏 */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                                <Shield className="h-8 w-8 text-blue-600" />
                                <span className="text-xl font-bold text-gray-900">ClamAV Scanner</span>
                            </div>
                            <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500">
                                <span>病毒扫描工具</span>
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                                    v1.0.0
                                </span>
                            </div>
                        </div>

                        <nav className="flex space-x-1">
                            <button
                                onClick={() => setCurrentView('home')}
                                className={clsx(
                                    'px-4 py-2 rounded-lg transition-colors flex items-center space-x-2',
                                    currentView === 'home'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                                )}
                            >
                                <Home className="h-4 w-4" />
                                <span>首页</span>
                            </button>
                            <button
                                onClick={() => setCurrentView('scan')}
                                className={clsx(
                                    'px-4 py-2 rounded-lg transition-colors flex items-center space-x-2',
                                    currentView === 'scan'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                                )}
                            >
                                <Scan className="h-4 w-4" />
                                <span>扫描</span>
                            </button>
                            <button
                                onClick={() => setCurrentView('history')}
                                className={clsx(
                                    'px-4 py-2 rounded-lg transition-colors flex items-center space-x-2',
                                    currentView === 'history'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                                )}
                            >
                                <Clock className="h-4 w-4" />
                                <span>历史</span>
                            </button>
                            <button
                                onClick={() => setCurrentView('settings')}
                                className={clsx(
                                    'px-4 py-2 rounded-lg transition-colors flex items-center space-x-2',
                                    currentView === 'settings'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                                )}
                            >
                                <Settings className="h-4 w-4" />
                                <span>设置</span>
                            </button>
                        </nav>
                    </div>
                </div>
            </header>

            {/* 主内容区域 */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {currentView === 'home' && renderHomeView()}
                {currentView === 'scan' && renderScanView()}
                {currentView === 'history' && renderHistoryView()}
                {currentView === 'settings' && renderSettingsView()}
            </main>

            {/* 状态栏 */}
            <footer className="bg-white border-t border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center text-sm text-gray-600">
                        <div className="flex items-center space-x-4">
                            {dbStatus && (
                                <span>病毒库: {dbStatus.signatures.toLocaleString()} 个特征</span>
                            )}
                            <span>•</span>
                            <span>最后更新: {dbStatus?.last_update || '未知'}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            {(isScanning || isUpdating) && (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span>{isScanning ? '正在扫描...' : '正在更新...'}</span>
                                </>
                            )}
                            {!isScanning && !isUpdating && (
                                <span className="flex items-center text-green-600">
                                    <CheckCircle className="h-4 w-4 mr-1" />
                                    就绪
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}

export default App;