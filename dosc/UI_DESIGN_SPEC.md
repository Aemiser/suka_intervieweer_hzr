# UI Neumorphism 视觉重设计规范

本文档定义当前面试产品 UI 的新拟物（Neumorphism）视觉方案，整体改为浅色、柔和、复古方向，突出纸感与陶土色点缀

## 1) 主题配色方案 (Theme Palette)

### 1.1 设计方向
- 风格关键词：Soft UI、奶油纸感、复古低饱和、实体按压感。
- 适用范围：主面板、输入区、按钮、AI 对话气泡、面试评价卡片。
- 核心策略：暖米色底色 + 双阴影（亮/暗）+ 低饱和强调渐变，兼顾质感与可读性。

### 1.2 基础色与阴影色

| Token | Hex | 用途 |
|---|---|---|
| Base Color | `#EDE4D7` | 全局中间背景，浅暖复古主基底 |
| Surface Raise | `#F5EEE4` | 凸起组件高光面 |
| Surface Press | `#DFD2C1` | 按下/内凹状态面 |
| Light Shadow | `#FFF9EF` | 顶左亮部阴影 |
| Dark Shadow | `#C3B39E` | 底右暗部阴影 |
| Text Primary | `#4E4338` | 主文本（复古深棕灰） |
| Text Secondary | `#7E6F61` | 次级文本 |
| Border Soft | `#D8CCBC` | 轻边界辅助分层 |

### 1.3 强调色（关键按钮）

用于“开始面试”“提交回答”“结束面试确认”等关键动作。

- Accent Gradient Start: `#CFA187`
- Accent Gradient End: `#B77B63`
- Accent Solid Fallback: `#BE886F`

渐变方向：`qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #CFA187, stop:1 #B77B63)`

可访问性补充：
- 渐变按钮文本统一使用 `#FFF8F2`，确保与暖色背景有足够对比。
- 非关键文本按钮不使用渐变，保持新拟物层级秩序。

---

## 2) Icon 选型方案 (Google Fonts Icons)

### 2.1 图标库与风格
- 图标库：Google Fonts Icons
- 链接：https://fonts.google.com/icons
- 风格：Outlined（推荐）

说明：Outlined 与浅色新拟物搭配时更轻盈，适合复古柔和界面。

### 2.2 场景图标映射（全项目版）

| 场景（页面/模块） | 功能动作 | Icon Name (Outlined) | 说明 |
|---|---|---|---|
| 顶部 Tab 导航 | 模拟面试 | `record_voice_over` | 面试主流程入口 |
| 顶部 Tab 导航 | 题库练习 | `menu_book` | 题库浏览与练习 |
| 顶部 Tab 导航 | 历史分析 | `query_stats` | 历史趋势与分析 |
| 顶部 Tab 导航 | AI 助手 | `smart_toy` | 智能问答入口 |
| 面试面板 Header | 姓名/候选人 | `person` | 用户身份输入 |
| 面试面板 Header | 岗位选择 | `work` | 岗位下拉选择 |
| 面试面板 Action Bar | 投递简历 | `upload_file` | 会话前置动作|
| 面试面板 Action Bar | 开始面试 | `play_circle` | 主 CTA，建议配复古暖色渐变 |
| 面试面板 Action Bar | 结束面试 | `stop_circle` | 结束流程，建议二次确认 |
| 面试状态提示 | AI 思考/处理中 | `hourglass_top` | 流式请求进行中 |
| 面试状态提示 | 面试完成 | `task_alt` | 完成态反馈 |
| 面试气泡区 | 新消息跳转 | `arrow_downward` | 快速跳转到底部 |
| 面试气泡区 | 评分报告 | `assessment` | 单题评估/总结卡片 |
| 通用输入区 | 发送回答 | `send` | 文本提交动作 |
| 语音录制区（ASR） | 开始录音 | `mic` | 默认录音入口 |
| 语音录制区（ASR） | 停止录音 | `stop` | 结束当前录音 |
| 语音录制区（ASR） | 取消录音 | `cancel` | 放弃当前录音 |
| 语音录制区（ASR） | 录音失败/禁用 | `mic_off` | 设备异常或不可用 |
| 语音录制区（ASR） | 播放录音 | `play_arrow` | 本地回放语音条 |
| 语音录制区（ASR） | 语音转文字 | `subtitles` | ASR 转写动作 |
| 语音录制区（ASR） | 发送语音结果 | `send` | 转写后提交 |
| 语音录制区（ASR） | 清除录音 | `delete` | 删除暂存录音 |
| 历史分析面板 | 同步数据 | `sync` | 刷新成员与记录 |
| 历史分析面板 | 成员选择 | `group` | 多成员历史视角 |
| 历史分析面板 | 综合得分趋势 | `trending_up` | 折线走势 |
| 历史分析面板 | 能力维度雷达 | `radar` | 维度能力分布 |
| 历史分析面板 | 面试回顾报告 | `article` | 文本报告展示 |
| 题库练习面板 | 搜索题目 | `search` | 关键词检索 |
| 题库练习面板 | 分类筛选 | `category` | 分类过滤 |
| 题库练习面板 | 难度筛选 | `tune` | 难度过滤 |
| 题库练习面板 | 排序 | `sort` | 排序策略切换 |
| 题库练习面板 | 查看全部题目 | `list_alt` | 重置筛选并展示全部 |
| 题库练习面板 | 刷新题库 | `refresh` | 重新拉取数据 |
| 题库练习面板 | 查看答案 | `visibility` | 展开答案卡片 |
| 题库练习面板 | 收起答案 | `visibility_off` | 折叠答案卡片 |
| 题库练习面板 | 首页 | `first_page` | 分页快速跳转 |
| 题库练习面板 | 上一页 | `chevron_left` | 分页导航 |
| 题库练习面板 | 下一页 | `chevron_right` | 分页导航 |
| 题库练习面板 | 末页 | `last_page` | 分页快速跳转 |
| 题库练习面板 | 跳转页码 | `find_replace` | 指定页数跳转 |
| 题库练习面板 | 题库总量统计 | `inventory_2` | 总题数徽标 |
| 题库练习面板 | 初级题统计 | `looks_one` | 初级分层统计 |
| 题库练习面板 | 中级题统计 | `looks_two` | 中级分层统计 |
| 题库练习面板 | 高级题统计 | `looks_3` | 高级分层统计 |
| 题库练习面板 | 分类数统计 | `dashboard` | 分类数量统计 |
| AI 助手面板 | 清空对话 | `cleaning_services` | 重置当前会话 |
| AI 助手快捷操作 | 随机抽题 | `shuffle` | 随机题练习 |
| AI 助手快捷操作 | 搜索题目 | `search` | 题目检索 |
| AI 助手快捷操作 | 题库统计 | `bar_chart` | 统计查询 |
| AI 助手快捷操作 | 联网搜索 | `travel_explore` | 外部资料检索 |
| AI 助手快捷操作 | 知识检索 | `library_books` | 技术知识库问答 |
| AI 助手快捷操作 | 历史记录 | `history` | 学生历史查询 |
| 通用系统操作 | 设置 | `settings` | 偏好配置入口 |
| 通用系统操作 | 帮助说明 | `help_outline` | 使用指南入口 |


尺寸与间距建议：
- 主按钮图标：20px
- 普通按钮图标：18px
- 图标与文字间距：8px

---

## 3) 按钮与组件样式 (QSS)

以下 QSS 为可直接复用的基础样式，覆盖普通/悬停/点击（内凹）状态。

### 3.1 设计令牌（QSS 变量占位）

```css
/* 约定：这些 token 可在 Python 中格式化替换 */
/* BASE=#EDE4D7, LIGHT=#FFF9EF, DARK=#C3B39E */
/* ACCENT_A=#CFA187, ACCENT_B=#B77B63 */
```

### 3.2 通用凸起按钮（默认状态）

```css
QPushButton#neuBtn {
    background: #EDE4D7;
    color: #4E4338;
    border: 1px solid #D7CABA;
    border-radius: 14px; /* >= 12px */
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;

    /* Qt 对 box-shadow 支持有限，这里通过渐变 + 边框 + 亮暗对比模拟双阴影逻辑 */
    background-image: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #F5EEE4,
        stop:1 #E3D6C7
    );
}

QPushButton#neuBtn:hover {
    color: #463B31;
    border: 1px solid #CEBFAD;
    background-image: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #FBF4EA,
        stop:1 #E9DDCE
    );
}

QPushButton#neuBtn:pressed {
    color: #42372D;
    border: 1px solid #BEAF9D;
    border-radius: 14px;

    /* Inset 内凹按压感：颜色向内收敛 */
    background-image: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #DCCFBE,
        stop:1 #F6EFE5
    );
    padding-top: 11px;
    padding-left: 17px;
}

QPushButton#neuBtn:disabled {
    color: #9B8E81;
    border: 1px solid #E1D7CA;
    background: #EEE6DB;
}
```

### 3.3 强调按钮（开始面试）

```css
QPushButton#startInterviewBtn {
    color: #FFF8F2;
    border: none;
    border-radius: 16px;
    padding: 11px 18px;
    font-size: 14px;
    font-weight: 700;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #CFA187,
        stop:1 #B77B63
    );
}

QPushButton#startInterviewBtn:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #D9AE95,
        stop:1 #C48870
    );
}

QPushButton#startInterviewBtn:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #BB8D74,
        stop:1 #A96E58
    );
    padding-top: 12px;
}
```

### 3.3.1 会话前置按钮（投递简历）

- 组件定位：面试面板 Action Bar，位于“开始面试”之前。
- 样式归类：使用 `QPushButton#neuBtn`（通用凸起按钮），不使用强调渐变。
- 交互状态：默认可点击；未填写必要信息时置灰禁用。
- 建议对象名：`submitResumeBtn`（用于后续扩展流程与埋点）。

### 3.4 卡片、输入区、气泡基础样式

```css
QFrame#neuCard, QFrame#chatBubbleAI, QFrame#scoreCard {
    background: #EDE4D7;
    border: 1px solid #D6C8B7;
    border-radius: 16px;
}

QFrame#footerInputZone {
    background: #EDE4D7;
    border: 1px solid #D8CCBC;
    border-radius: 16px;
}

QLineEdit#chatInput, QTextEdit#chatInput {
    background: #EFE7DB;
    color: #4E4338;
    border: 1px solid #D2C3B1;
    border-radius: 12px;
    padding: 10px 12px;
}

QLineEdit#chatInput:focus, QTextEdit#chatInput:focus {
    border: 1px solid #C7977E;
}
```

### 3.5 Qt 阴影效果建议（配合 QGraphicsDropShadowEffect）

由于 QSS 本身不支持标准 CSS box-shadow，建议在 Python 中对关键组件叠加双阴影：

1. 亮阴影：`color=#FFF9EF`, `offset=(-4, -4)`, `blurRadius=14`
2. 暗阴影：`color=#C3B39E`, `offset=(4, 4)`, `blurRadius=14`
3. 按下态切换：减小 blur 并交换明暗权重，形成内凹触感。

### 3.6 按键类型定义（全局统一）

为避免实现阶段命名与视觉不一致，所有按键统一归类为以下类型：

| 按键类型 ID | 类型名称 | 视觉特征 | 典型对象名 | 适用动作 |
|---|---|---|---|---|
| BTN_PRIMARY | 主操作强调按钮 | 暖色渐变、高对比文本、圆角 16px | `startInterviewBtn` | 开始面试、确认提交、关键正向动作 |
| BTN_NEU_RAISED | 通用凸起按钮 | 浅色新拟物凸起、双阴影感、圆角 12-14px | `neuBtn` / `submitResumeBtn` | 投递简历、刷新、同步、分页、普通功能按钮 |
| BTN_NEU_PRESSED | 通用按下态 | 内凹按压感、边框收敛、轻位移 | `neuBtn:pressed` | 所有 BTN_NEU_RAISED 的点击态反馈 |
| BTN_ICON_ONLY | 图标按钮 | 无文字或弱文字、面积较小、强调图标识别 | `micBtn` / `sendBtn` / `scrollToBottomBtn` | 语音控制、发送、快捷跳转 |
| BTN_DANGER_SECONDARY | 风险次级按钮 | 非渐变、暖灰底、强调边框或文案提示 | `endInterviewBtn` | 结束面试、清空会话、删除等高风险动作 |
| BTN_DISABLED | 禁用态按钮 | 降低对比度与饱和度、不可交互 | 任意按钮 `:disabled` | 前置条件未满足（如未投递简历） |

按钮使用约束：
- 同一区域只允许一个 `BTN_PRIMARY`，避免主次冲突。
- 会话前置动作“投递简历”固定使用 `BTN_NEU_RAISED`。
- 高风险动作默认采用 `BTN_DANGER_SECONDARY`，并搭配二次确认。
- 图标按钮点击热区建议不小于 `32x32`。

---

## 4) 卡片与气泡动画 (Animations)

目标对象：
- AI 对话气泡（ChatBubble）
- 面试评价卡片（ScoreCardBubble）

### 4.1 AI 对话气泡动效

#### A) Fade-in with Slide-up
- 触发时机：新 AI 消息创建时。
- 动效参数：
  - Duration: `300ms`
  - Easing: `QEasingCurve.OutCubic`
  - 属性：`opacity 0 -> 1`，`pos.y + 8 -> y`

建议实现：`QPropertyAnimation` + `QGraphicsOpacityEffect` 并行动画。

#### B) Shadow Pulse（轻呼吸）
- 触发时机：流式输出期间（token 持续到达）。
- 动效参数：
  - Duration: `1800ms`
  - Loop: `-1`（循环）
  - Easing: `QEasingCurve.InOutSine`
  - 变化：暗阴影 blur `10 -> 15 -> 10`

结束条件：流式完成后停止 pulse，回归静态阴影。

### 4.2 面试评价卡片动效

#### A) Card Reveal（淡入上浮）
- 触发时机：评分结果生成后插入卡片时。
- 动效参数：
  - Duration: `380ms`
  - Easing: `QEasingCurve.OutBack`
  - 属性：`opacity 0 -> 1`，`scale 0.98 -> 1.00`（可通过 geometry 插值近似）

#### B) Score Glow（分数强调）
- 触发时机：卡片 reveal 完成后。
- 动效参数：
  - Duration: `900ms`
  - Easing: `QEasingCurve.OutQuad`
  - 变化：综合得分文本颜色从 `#7E6F61 -> #B77B63`，或外发光 alpha `0 -> 0.24 -> 0`

### 4.3 动画节奏原则
- 同屏连续消息采用 stagger：每条延迟 `40ms`，避免机械同步。
- 交互动画总时长控制在 `180ms - 420ms`，保证灵敏度与柔和感。
- 循环动画仅用于“进行中”状态，完成后必须收敛，避免视觉疲劳。

---

## 5) 组件落地映射建议

### 5.1 关键对象对应
- 面试主按钮：`开始面试`、`结束面试`、`发送回答`
- 聊天气泡：AI 侧气泡、用户侧气泡、系统提示
- 评分卡片：技术/逻辑/深度/表达/综合分区块

### 5.2 视觉层级建议
1. 页面背景保持 Base Color 纯净。
2. 一级交互（主按钮）使用 Accent Gradient。
3. 二级交互（普通按钮/输入框）采用标准凸起新拟物。
4. 信息型容器（卡片/气泡）以柔和阴影区分，不抢主 CTA。

### 5.3 布局类型定义（全局统一）

| 布局类型 ID | 类型名称 | 结构说明 | 典型容器 |
|---|---|---|---|
| LYT_APP_SHELL | 应用壳层布局 | 顶部导航 + 主内容区 + 底部信息区 | 主窗口根容器 |
| LYT_TAB_TOP | 顶部标签布局 | 水平等距/自适应 Tab 排列 | 顶部 Tab 导航 |
| LYT_PANEL_STACK | 面板分层布局 | Header / Body / Footer 垂直分层 | 各功能面板根布局 |
| LYT_HEADER_FORM | 头部表单布局 | 标签+输入控件成组排列 | 面试信息区、筛选区 |
| LYT_ACTION_BAR | 动作条布局 | 同级操作按钮横向排列，主次分层 | 面试 Action Bar、工具条 |
| LYT_CHAT_STREAM | 消息流布局 | 气泡列表纵向堆叠，支持滚动与新消息定位 | 面试对话区、助手对话区 |
| LYT_CARD_GRID | 卡片网格布局 | 指标卡/统计卡按列对齐 | 历史分析卡片区 |
| LYT_CHART_ZONE | 图表区布局 | 图表容器与图例/标题组合 | 趋势图、雷达图区域 |
| LYT_PAGINATION_BAR | 分页布局 | 页码信息 + 跳转/前后按钮 | 题库分页区 |
| LYT_INPUT_DOCK | 输入停靠布局 | 输入框 + 发送/语音按钮固定底部 | 聊天输入区、语音输入区 |
| LYT_STATUS_INLINE | 行内状态布局 | 图标+短文本提示同排展示 | 处理中/完成提示条 |

### 5.4 全模块按键类型与布局类型映射

| 模块 | 区域/动作 | 按键类型 | 布局类型 |
|---|---|---|---|
| 顶部导航 | 模拟面试/题库练习/历史分析/AI 助手 Tab | BTN_NEU_RAISED | LYT_TAB_TOP |
| 面试面板 | 姓名/岗位信息输入区 | （无按钮） | LYT_HEADER_FORM |
| 面试面板 | 投递简历 | BTN_NEU_RAISED | LYT_ACTION_BAR |
| 面试面板 | 开始面试 | BTN_PRIMARY | LYT_ACTION_BAR |
| 面试面板 | 结束面试 | BTN_DANGER_SECONDARY | LYT_ACTION_BAR |
| 面试面板 | AI 思考/完成状态提示 | （状态控件） | LYT_STATUS_INLINE |
| 面试面板 | 对话气泡区/新消息跳转 | BTN_ICON_ONLY（跳转） | LYT_CHAT_STREAM |
| 面试面板 | 发送回答 | BTN_ICON_ONLY 或 BTN_NEU_RAISED（带文字时） | LYT_INPUT_DOCK |
| 语音录制区 | 开始/停止/取消录音 | BTN_ICON_ONLY | LYT_INPUT_DOCK |
| 语音录制区 | 播放录音/转写/发送/清除 | BTN_ICON_ONLY 或 BTN_NEU_RAISED | LYT_INPUT_DOCK |
| 历史分析面板 | 同步数据 | BTN_NEU_RAISED | LYT_ACTION_BAR |
| 历史分析面板 | 成员选择与筛选控件 | BTN_NEU_RAISED（触发类） | LYT_HEADER_FORM |
| 历史分析面板 | 趋势图/雷达图/报告卡 | （无按钮或局部 BTN_ICON_ONLY） | LYT_CHART_ZONE / LYT_CARD_GRID |
| 题库练习面板 | 搜索/分类/难度/排序/查看全部/刷新 | BTN_NEU_RAISED | LYT_HEADER_FORM + LYT_ACTION_BAR |
| 题库练习面板 | 查看答案/收起答案 | BTN_NEU_RAISED | LYT_PANEL_STACK |
| 题库练习面板 | 首页/上一页/下一页/末页/跳转页码 | BTN_NEU_RAISED | LYT_PAGINATION_BAR |
| AI 助手面板 | 清空对话 | BTN_DANGER_SECONDARY | LYT_ACTION_BAR |
| AI 助手面板 | 快捷操作（随机抽题/搜索/统计/联网/知识检索/历史） | BTN_NEU_RAISED | LYT_ACTION_BAR |
| 通用系统操作 | 设置/帮助说明 | BTN_NEU_RAISED | LYT_ACTION_BAR |


### 5.5 面试会话前置流程

在正式面试会话开始前，面试面板增加前置流程：

1. 填写候选人信息（姓名、岗位等必填字段）。
2. 点击“投递简历”按钮上传/提交简历数据。
3. 系统校验信息与简历投递状态。
4. 校验通过后启用“开始面试”，进入正式会话流程。

流程约束建议：
- “开始面试”在前置步骤未完成时保持禁用。
- “投递简历”成功后给出明确状态反馈（如 `task_alt` + 成功文案）。
- 若投递失败，保留重试入口并显示错误提示，不进入正式会话。

---

## 6) 交付标准

- 已定义 Base / Light Shadow / Dark Shadow / Accent 全套色值。
- 已指定 Google Fonts Icons 且风格为 Outlined。
- 已提供可执行 QSS：普通、Hover、Pressed（Inset 逻辑）状态齐全。
- 已定义全局按键类型（主按钮/通用凸起/图标按钮/风险按钮/禁用态）及适用规则。
- 已定义全局布局类型并完成各模块按键类型与布局类型映射。
- 所有按钮和卡片圆角均不低于 `12px`。
- 已定义 AI 气泡与评分卡片的动画名称、时长、缓动和触发时机。

本规范可直接作为 UI 改造设计基线，并可逐步映射到现有 Qt 组件实现。