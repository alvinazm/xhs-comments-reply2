# 微信视频号自动化操作指南

## 概述

视频号平台 (`channels.weixin.qq.com`) 使用 **wujie iframe** 技术加载内容，导致传统的 CDP (Chrome DevTools Protocol) 操作无法直接访问 iframe 内的 DOM 元素。

## 技术方案

### 问题分析

1. **iframe 隔离**：视频号页面运行在 `wujie-app.wujie_iframe` 中
2. **跨域限制**：主页面无法通过 `contentDocument` 访问 iframe 内容
3. **CDP frame 切换失败**：CDP 的 `Page.switchToFrame` 无法正确切换到 wujie iframe

### 解决方案：JavaScript 注入

通过在主页面执行 JavaScript，间接访问 `window.frames[0]` 来操作 iframe 内容。

## 核心实现

### 1. 文件上传

**选择器策略**：
```
.ant-upload input[type="file"]  →  找到隐藏的文件输入框
.ant-upload               →  点击此元素触发系统文件选择对话框
```

**JavaScript 代码**：
```javascript
(() => {
    const frame = window.frames[0];
    if (!frame || !frame.document) return 'no_frame';
    const doc = frame.document;
    
    // 找到文件输入框的父容器
    const fileInput = doc.querySelector('.ant-upload input[type="file"]');
    if (fileInput) {
        const container = fileInput.closest('.ant-upload');
        if (container) {
            container.click();
            return 'clicked';
        }
    }
    return 'not_found';
})()
```

**HTML 结构**：
```html
<span role="button" class="ant-upload">
    <input type="file" accept="video/mp4,video/x-m4v,video/*" 
           multiple="multiple" style="display: none;">
    <div class="ant-upload-drag-container">
        <div class="upload-content">
            <!-- 上传提示内容 -->
        </div>
    </div>
</span>
```

### 2. 标题填写

**选择器**：
```
input.weui-desktop-form__input[placeholder*="概括视频主要内容"]
```

**JavaScript 代码**：
```javascript
(() => {
    const frame = window.frames[0];
    if (!frame || !frame.document) return false;
    const doc = frame.document;
    
    const el = doc.querySelector('input.weui-desktop-form__input[placeholder*="概括"]');
    if (el) {
        el.focus();
        el.value = '标题内容';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    }
    return false;
})()
```

## 配置结构

```python
"weixin_video": {
    "name": "视频号",
    "url": "https://channels.weixin.qq.com/platform/post/create",
    "use_iframe": True,  # 标记为 iframe 平台
    "file_selectors": [
        ".upload-content input[type='file']",
        ".ant-upload input[type='file']",
        "input[type='file'][accept*='video']",
    ],
    "title_selectors": [
        'input.weui-desktop-form__input[placeholder*="概括视频主要内容"]',
        'input.weui-desktop-form__input[placeholder*="字数建议"]',
        'input.weui-desktop-form__input',
    ],
}
```

## 操作流程

### 正常流程

1. 打开视频号发布页面
2. 等待 iframe 加载完成 (3-5秒)
3. 填写标题（通过 JavaScript 注入）
4. 点击上传区域（通过 JavaScript 注入）
5. 用户手动选择视频文件
6. 系统自动处理上传

### 注意事项

1. **文件选择必须手动**：由于系统安全限制，无法通过 JavaScript 自动化文件对话框，必须由用户手动选择
2. **iframe 等待**：页面加载后需要等待 iframe 完全加载
3. **事件触发**：填写表单时需要同时触发 `input` 和 `change` 事件，确保 React/Vue 状态更新

## 调试方法

### 检查 iframe 是否可访问

```javascript
window.frames[0]?.document.querySelector('.upload-content') 
// 返回元素则说明可以访问
```

### 检查文件上传元素

```javascript
window.frames[0]?.document.querySelector('.ant-upload input[type="file"]')
// 返回 input 元素则正确
```

### 检查标题输入框

```javascript
window.frames[0]?.document.querySelector('input.weui-desktop-form__input[placeholder*="概括"]')
// 返回 input 元素则正确
```

## 平台差异

| 平台 | iframe | 文件上传 | 标题选择器 |
|------|--------|----------|-----------|
| 小红书 | 否 | CDP 直接设置 | 通用选择器 |
| 抖音 | 否 | CDP 直接设置 | 通用选择器 |
| 百家号 | 否 | CDP 直接设置 | 通用选择器 |
| **视频号** | 是 | JavaScript 点击 | `weui-desktop-form__input` |

## 未来优化方向

1. 支持 CDP frame 切换（需要 wujie 框架配合）
2. 自动化文件选择（需要浏览器扩展支持）
3. 上传进度监控
