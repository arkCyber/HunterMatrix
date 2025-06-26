import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
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
  Loader2
} from 'lucide-react';
import clsx from 'clsx';

// 接口定义
interface ScanResult {
  status: 'safe' | 'infected' | 'error';
  filesScanned: number;
  threatsFound: number;
  scanTime: string;
  logPath?: string;
  details?: string[];
}

interface DatabaseStatus {
  version: string;
  lastUpdate: string;
  signatures: number;
}

function App() {
  // 状态管理
  const [currentView, setCurrentView] = useState<'home' | 'scan' | 'settings'>('home');
  const [isScanning, setIsScanning] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [dbStatus, setDbStatus] = useState<DatabaseStatus | null>(null);
  const [selectedPath, setSelectedPath] = useState<string>('');

  // 获取数据库状态
  useEffect(() => {
    loadDatabaseStatus();
  }, []);

  const loadDatabaseStatus = async () => {
    try {
      const status = await invoke<DatabaseStatus>('get_database_status');
      setDbStatus(status);
    } catch (error) {
      console.error('加载数据库状态失败:', error);
    }
  };

  // 更新病毒库
  const updateDatabase = async () => {
    setIsUpdating(true);
    try {
      await invoke('update_virus_database');
      await loadDatabaseStatus();
    } catch (error) {
      console.error('更新病毒库失败:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  // 选择扫描路径
  const selectScanPath = async () => {
    try {
      const path = await invoke<string>('select_folder');
      setSelectedPath(path);
    } catch (error) {
      console.error('选择文件夹失败:', error);
    }
  };

  // 开始扫描
  const startScan = async (path?: string) => {
    setIsScanning(true);
    setScanResult(null);

    try {
      const result = await invoke<ScanResult>('start_scan', {
        path: path || selectedPath || '~/Downloads'
      });
      setScanResult(result);
    } catch (error) {
      console.error('扫描失败:', error);
      setScanResult({
        status: 'error',
        filesScanned: 0,
        threatsFound: 0,
        scanTime: '0s',
        details: [`扫描失败: ${error}`]
      });
    } finally {
      setIsScanning(false);
    }
  };

  // 渲染主界面
  const renderHomeView = () => (
    <div className="space-y-8">
      {/* 状态卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 系统状态 */}
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className={clsx(
              "p-3 rounded-full",
              scanResult?.status === 'safe' ? 'bg-green-100' :
                scanResult?.status === 'infected' ? 'bg-red-100' : 'bg-gray-100'
            )}>
              {scanResult?.status === 'safe' ? (
                <ShieldCheck className="h-6 w-6 text-green-600" />
              ) : scanResult?.status === 'infected' ? (
                <ShieldAlert className="h-6 w-6 text-red-600" />
              ) : (
                <Shield className="h-6 w-6 text-gray-600" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">系统状态</h3>
              <p className="text-sm text-gray-600">
                {scanResult?.status === 'safe' ? '安全' :
                  scanResult?.status === 'infected' ? '发现威胁' : '未扫描'}
              </p>
            </div>
          </div>
        </div>

        {/* 病毒库状态 */}
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-full bg-blue-100">
              <Download className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">病毒库</h3>
              <p className="text-sm text-gray-600">
                {dbStatus ? `${dbStatus.signatures.toLocaleString()} 个特征` : '加载中...'}
              </p>
            </div>
          </div>
        </div>

        {/* 最后扫描 */}
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-full bg-purple-100">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">最后扫描</h3>
              <p className="text-sm text-gray-600">
                {scanResult ? scanResult.scanTime : '从未扫描'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 快速操作 */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-6">快速操作</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => startScan('~/Downloads')}
            disabled={isScanning}
            className="flex flex-col items-center p-6 border-2 border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200 disabled:opacity-50"
          >
            <FolderOpen className="h-8 w-8 text-primary-600 mb-3" />
            <span className="font-medium text-gray-900">扫描下载</span>
            <span className="text-sm text-gray-600">扫描下载文件夹</span>
          </button>

          <button
            onClick={selectScanPath}
            disabled={isScanning}
            className="flex flex-col items-center p-6 border-2 border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200 disabled:opacity-50"
          >
            <Scan className="h-8 w-8 text-primary-600 mb-3" />
            <span className="font-medium text-gray-900">自定义扫描</span>
            <span className="text-sm text-gray-600">选择扫描路径</span>
          </button>

          <button
            onClick={updateDatabase}
            disabled={isUpdating}
            className="flex flex-col items-center p-6 border-2 border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200 disabled:opacity-50"
          >
            <Download className="h-8 w-8 text-primary-600 mb-3" />
            <span className="font-medium text-gray-900">更新病毒库</span>
            <span className="text-sm text-gray-600">获取最新特征</span>
          </button>

          <button
            onClick={() => setCurrentView('settings')}
            className="flex flex-col items-center p-6 border-2 border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
          >
            <Settings className="h-8 w-8 text-primary-600 mb-3" />
            <span className="font-medium text-gray-900">设置</span>
            <span className="text-sm text-gray-600">应用程序设置</span>
          </button>
        </div>
      </div>

      {/* 扫描结果 */}
      {(isScanning || scanResult) && (
        <div className="card animate-slide-up">
          <h2 className="text-xl font-bold text-gray-900 mb-6">扫描结果</h2>

          {isScanning ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <Loader2 className="h-12 w-12 text-primary-600 animate-spin mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">正在扫描中...</h3>
                <p className="text-gray-600">请耐心等待扫描完成</p>
              </div>
            </div>
          ) : scanResult && (
            <div>
              <div className={clsx(
                "flex items-center space-x-3 p-4 rounded-lg border-2",
                scanResult.status === 'safe' ? 'status-safe' :
                  scanResult.status === 'infected' ? 'status-danger' : 'status-warning'
              )}>
                {scanResult.status === 'safe' ? (
                  <CheckCircle className="h-6 w-6" />
                ) : scanResult.status === 'infected' ? (
                  <XCircle className="h-6 w-6" />
                ) : (
                  <AlertTriangle className="h-6 w-6" />
                )}
                <div>
                  <h3 className="font-semibold">
                    {scanResult.status === 'safe' ? '系统安全' :
                      scanResult.status === 'infected' ? '发现威胁' : '扫描出错'}
                  </h3>
                  <p className="text-sm">
                    扫描了 {scanResult.filesScanned} 个文件，
                    {scanResult.threatsFound > 0 ? `发现 ${scanResult.threatsFound} 个威胁` : '未发现威胁'}
                  </p>
                </div>
              </div>

              {scanResult.details && scanResult.details.length > 0 && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">详细信息</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {scanResult.details.map((detail, index) => (
                      <li key={index}>{detail}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-primary-600" />
              <h1 className="text-xl font-bold text-gray-900">ClamAV Scanner</h1>
            </div>

            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('home')}
                className={clsx(
                  "px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200",
                  currentView === 'home'
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-600 hover:text-gray-900"
                )}
              >
                首页
              </button>
              <button
                onClick={() => setCurrentView('scan')}
                className={clsx(
                  "px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200",
                  currentView === 'scan'
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-600 hover:text-gray-900"
                )}
              >
                扫描
              </button>
              <button
                onClick={() => setCurrentView('settings')}
                className={clsx(
                  "px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200",
                  currentView === 'settings'
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-600 hover:text-gray-900"
                )}
              >
                设置
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'home' && renderHomeView()}
        {currentView === 'scan' && (
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-6">高级扫描</h2>
            <p className="text-gray-600">高级扫描功能开发中...</p>
          </div>
        )}
        {currentView === 'settings' && (
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-6">设置</h2>
            <p className="text-gray-600">设置选项开发中...</p>
          </div>
        )}
      </main>

      {/* 状态栏 */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <div>
              {dbStatus && (
                <span>病毒库版本: {dbStatus.version} | 最后更新: {dbStatus.lastUpdate}</span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {(isScanning || isUpdating) && (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>{isScanning ? '扫描中' : '更新中'}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
