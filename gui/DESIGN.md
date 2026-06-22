# APM GUI — Design System

> Category: Developer Tools
> Dense operational desktop app for managing AI coding agent API providers.

## 1. Visual Theme & Atmosphere

APM GUI 采用 **Dark Operational** 设计方向，面向高频使用多个 AI agent 的开发者。
界面追求信息密度和操作效率，不追求装饰性视觉效果。

**设计DNA**：Linear 的精简 + Raycast 的紧凑 + Vercel 的工程感

**Key Characteristics:**
- 深色主题为主（减少视觉疲劳，贴合终端用户习惯）
- 紧凑信息布局（表格、列表优先于卡片）
- 状态色即信息色（绿=已同步/健康，橙=过期/警告，红=错误）
- Mono 字体用于 API key、URL 等技术信息
- 最小化装饰元素，功能即界面

## 2. Color Palette

### Backgrounds
- **App Background**: `#0a0a0a` — 纯深色底
- **Surface 1**: `#141414` — 侧边栏、面板
- **Surface 2**: `#1a1a1a` — 卡片、输入框
- **Surface 3**: `#222222` — hover 状态、选中行
- **Border**: `#2a2a2a` — 分隔线、边框

### Text
- **Primary**: `#f5f5f5` — 主文字
- **Secondary**: `#a0a0a0` — 描述、次要信息
- **Muted**: `#666666` — 占位符、禁用态

### Status
- **Success / Synced**: `#22c55e` (green-500)
- **Warning / Stale**: `#f59e0b` (amber-500)
- **Error / Failed**: `#ef4444` (red-500)
- **Info / Active**: `#3b82f6` (blue-500)

### Accent
- **Primary Accent**: `#3b82f6` — 主操作按钮、选中态
- **Accent Hover**: `#2563eb`
- **Accent Subtle**: `rgba(59, 130, 246, 0.1)` — 选中行背景

## 3. Typography

| Role | Font | Size | Weight | Color |
|------|------|------|--------|-------|
| Page Title | Inter | 20px | 600 | Primary |
| Section Title | Inter | 14px | 600 | Primary |
| Body | Inter | 13px | 400 | Primary |
| Description | Inter | 12px | 400 | Secondary |
| Mono (keys, URLs) | JetBrains Mono | 12px | 400 | Primary |
| Badge | Inter | 11px | 500 | varies |
| Shortcut | JetBrains Mono | 11px | 400 | Muted |

## 4. Layout

```
┌────────────────────────────────────────────────────┐
│  Title Bar (draggable, custom)                     │
├──────────┬─────────────────────────────────────────┤
│          │  Page Header (title + actions)          │
│  Sidebar │─────────────────────────────────────────│
│  (200px) │                                         │
│          │  Main Content                           │
│  - Home  │  (table / form / detail)               │
│  - Prov  │                                         │
│  - Agent │                                         │
│  - Sync  │                                         │
│  - Snap  │                                         │
│          │                                         │
├──────────┼─────────────────────────────────────────┤
│  Status  │  (optional: command output / logs)      │
└──────────┴─────────────────────────────────────────┘
```

- **Window**: 960×640 default, 最小 800×500
- **Sidebar**: 200px 固定宽度
- **Content padding**: 24px
- **Row height**: 40px（表格行）
- **Spacing scale**: 4, 8, 12, 16, 20, 24, 32

## 5. Components

### Sidebar Nav Item
- Height: 32px, padding: 0 12px
- Radius: 6px
- Active: accent-subtle bg + accent text
- Hover: surface-3 bg
- Icon (16px) + Label (13px 500)

### Table Row
- Height: 40px, border-bottom: 1px border
- Hover: surface-3 bg
- Cells: 13px, mono for technical values

### Status Badge
- Height: 20px, padding: 0 8px
- Radius: 9999px
- Font: 11px 500
- Variants: success/warning/error/neutral

### Button
- Primary: accent bg, white text, 6px radius, 32px height
- Secondary: transparent, border, primary text
- Danger: red-500 bg
- Icon button: 28×28, 6px radius

### Input
- Height: 32px
- Background: surface-2
- Border: border color, focus: accent
- Radius: 6px
- Font: 13px (mono for technical fields)

### Dialog/Modal
- Surface-1 bg, 8px radius
- Overlay: rgba(0,0,0,0.6)
- Max-width: 480px

## 6. Pages

### Dashboard (Home)
- 顶部统计卡片：N providers / N agents synced / last sync time
- Provider 列表（简表：name, models count, last synced）
- Agent 状态网格（icon + name + sync status badge）

### Providers
- 表格列：Name, Base URL, Models, Protocol, Status, Actions
- 右上角：Add Provider 按钮
- 行展开：显示完整配置、model 列表
- 行操作：Edit, Test, Remove

### Agents
- 卡片网格（2×5）：每个 agent 一个卡片
- 卡片内容：icon, name, installed badge, synced provider, sync time
- 卡片操作：Sync, View Config

### Sync
- Step 1: 选择 Provider（下拉）
- Step 2: 选择 Agents（checkbox grid）
- Step 3: Review + Execute
- 底部：实时输出面板

### Snapshots
- 表格：Name, Created, Agents, Actions (Restore / Delete)

## 7. Interactions

- 侧边栏导航切换：无动画，即时切换
- 表格 hover：行高亮
- 操作确认：Dialog（Sync/Delete 等破坏性操作）
- Toast 通知：右上角，auto-dismiss 3s
- 快捷键：⌘1-5 切换页面，⌘N 新建 provider，⌘S sync

## 8. Electron 架构

```
gui/
├── package.json
├── electron/
│   ├── main.ts          # Electron main process
│   ├── preload.ts       # IPC bridge
│   └── apm-bridge.ts   # 调用 Python CLI 的桥接层
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── components/      # 通用组件
│   ├── pages/           # 5 个页面
│   ├── hooks/           # useApm() 等
│   └── styles/          # Tailwind config
├── index.html
├── vite.config.ts
└── tailwind.config.ts
```

与 Python CLI 的通信方式：通过 `child_process.spawn('apm', [...args], { encoding: 'utf-8' })`，
解析 stdout/stderr 输出。
