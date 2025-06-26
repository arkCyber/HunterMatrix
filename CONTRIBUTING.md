# 贡献Guide - HunterMatrix AISmartSecurityPlatform

感谢您对HunterMatrix项目的关注！我们欢迎所Has形式的贡献，Package括但不限于Code、Documentation、Test、反馈和建议。

## 🤝 如何贡献

### Report问题

如果您Found了bug或Has功能建议，请：

1. Check [Issues](https://github.com/arkCyber/HunterMatrix/issues) 确认问题Not被Report
2. 使用适当的IssueTemplateCreate新Issue
3. 提供详细的描述和复现步骤
4. Package含SystemInformation和ErrorLog

### CommitCode

1. **Fork项目**
   ```bash
   git clone https://github.com/arkCyber/HunterMatrix.git
   cd HunterMatrix
   ```

2. **Create功能Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b bugfix/issue-number
   ```

3. **进行Development**
   - 遵循CodeSpecification
   - 添加必要的Test
   - Update相关Documentation

4. **Commit更改**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **PushBranch**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **CreatePull Request**
   - 使用清晰的标题和描述
   - 关联相关的Issue
   - 等待Code审查

## 📝 CodeSpecification

### JavaScript/TypeScript

```javascript
// 使用ES6+Syntax
const functionName = (param1, param2) => {
    // 使用驼峰命名
    const variableName = 'value';
    
    // 添加Annotation说明复杂逻辑
    if (condition) {
        return result;
    }
};

// FunctionDocumentation
/**
 * 扫描指定Path的File
 * @param {string} path - 扫描Path
 * @param {Object} options - 扫描Options
 * @returns {Promise<Object>} 扫描Result
 */
async function scanPath(path, options) {
    // 实现Code
}
```

### Python

```python
# 遵循PEP 8Specification
import os
import sys
from typing import Dict, List, Optional

class AIReportGenerator:
    """AIReport生成器Class"""
    
    def __init__(self, config: Dict[str, str]) -> None:
        """InitializeReport生成器
        
        Args:
            config: Configuration字典
        """
        self.config = config
    
    def generate_report(self, data: List[Dict]) -> str:
        """生成Report
        
        Args:
            data: 扫描Data列Table
            
        Returns:
            生成的ReportContent
        """
        # 实现Code
        pass
```

### Rust

```rust
// 使用StandardRustFormat
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ScanConfig {
    pub path: String,
    pub recursive: bool,
    pub exclude_patterns: Vec<String>,
}

impl ScanConfig {
    /// Create新的扫描Configuration
    pub fn new(path: String) -> Self {
        Self {
            path,
            recursive: true,
            exclude_patterns: Vec::new(),
        }
    }
    
    /// 添加排除模式
    pub fn add_exclude_pattern(&mut self, pattern: String) {
        self.exclude_patterns.push(pattern);
    }
}
```

### HTML/CSS

```html
<!-- 使用语义化HTML -->
<section class="scan-panel">
    <header class="panel-header">
        <h2 class="panel-title">病毒扫描</h2>
    </header>
    
    <main class="panel-content">
        <!-- Content -->
    </main>
</section>
```

```css
/* 使用BEM命名Specification */
.scan-panel {
    @apply bg-white dark:bg-gray-800 rounded-lg shadow-lg;
}

.scan-panel__header {
    @apply border-b border-gray-200 dark:border-gray-700 p-4;
}

.scan-panel__title {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}
```

## 🧪 Test要求

### 前端Test

```javascript
// 使用Jest进行单元Test
describe('ScanManager', () => {
    test('should start scan successfully', async () => {
        const scanManager = new ScanManager();
        const result = await scanManager.startScan('/test/path');
        
        expect(result.success).toBe(true);
        expect(result.scanId).toBeDefined();
    });
});
```

### 后端Test

```python
# 使用pytest进行Test
import pytest
from ai_security.report_generator import AIReportGenerator

class TestAIReportGenerator:
    def test_generate_report(self):
        """TestReport生Success能"""
        generator = AIReportGenerator({})
        report = generator.generate_report([])
        
        assert isinstance(report, str)
        assert len(report) > 0
```

### 集成Test

```bash
# Run完整Test套件
./test_scanning.sh
python -m pytest ai-security/tests/
cargo test
```

## 📚 Documentation要求

### CodeDocumentation

- 所HasPublicFunction必须HasDocumentationAnnotation
- 复杂Algorithm需要详细说明
- APIInterface需要完整的Parameters和返回值说明

### UserDocumentation

- 新功能需要UpdateUserManual
- Configuration变更需要UpdateConfigurationDocumentation
- 重大变更需要Update迁移Guide

## 🔄 Development流程

### BranchPolicy

- `main`: 主Branch，稳定Version
- `develop`: DevelopmentBranch，集成新功能
- `feature/*`: 功能Branch
- `bugfix/*`: 修复Branch
- `hotfix/*`: 紧急修复Branch

### CommitInformationFormat

使用 [Conventional Commits](https://www.conventionalcommits.org/) Format：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Type说明：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: DocumentationUpdate
- `style`: CodeFormat调整
- `refactor`: Code重构
- `test`: Test相关
- `chore`: Build过程或辅助Tool的变动

Example：
```
feat(ai): add intelligent threat detection

- Implement machine learning based threat analysis
- Add support for behavioral pattern recognition
- Update AI model training pipeline

Closes #123
```

## 🚀 Release流程

### Version号Specification

使用 [Semantic Versioning](https://semver.org/)：
- `MAJOR.MINOR.PATCH`
- `1.0.0`: 主要Version，不兼容的API变更
- `1.1.0`: 次要Version，向后兼容的功能性新增
- `1.1.1`: 修订Version，向后兼容的问题修正

### ReleaseCheck清单

- [ ] 所HasTest通过
- [ ] DocumentationAlreadyUpdate
- [ ] 变更LogAlreadyUpdate
- [ ] Version号AlreadyUpdate
- [ ] Security审查Complete
- [ ] PerformanceTest通过

## 🛡️ Security要求

### CodeSecurity

- 不Commit敏感Information（Password、Key等）
- 使用Security的编码实践
- 定期Update依赖项
- 进行SecurityCode审查

### DataSecurity

- 保护User隐私
- SecurityProcess扫描Data
- Encryption敏感Configuration
- 遵循Data保护法规

## 📞 联系方式

- **GitHub Issues**: [项目Issues页面](https://github.com/arkCyber/HunterMatrix/issues)
- **Email**: arksong2018@gmail.com
- **讨论**: [GitHub Discussions](https://github.com/arkCyber/HunterMatrix/discussions)

## 📄 License证

通过贡献Code，您同意您的贡献将在与项目相同的 [GPL v2 License证](LICENSE) 下Authorization。

---

感谢您的贡献！🎉
