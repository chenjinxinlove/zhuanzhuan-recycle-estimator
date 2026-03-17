---
name: zhuanzhuan-recycle-estimator
description: Use when manually testing or demoing the OpenClaw recycle valuation API with text, images, token continuation, session continuation, or product switching flows
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# Zhuanzhuan Recycle Estimator

## Overview

使用本技能对本地或测试环境中的 OpenClaw 回收估价接口做端到端验证。
它适用于图片估价、文字估价、多轮澄清、`skill_token` 续用、`session_id` 续接、商品切换测试。

## When to Use

- 需要手动验证 `POST /zai/find_mate/v1/openclaw/recycle-skill/valuate`
- 需要复用上一轮返回的 `skill_token`
- 需要验证 `session_id` 续接或 `allow_auto_resume`
- 需要测试"换一个商品"后的新上下文
- 需要给 ClawHub/OpenClaw 做 demo

## Prerequisites

- 服务已启动
- 默认接口地址：
  `https://zai.zhuanzhuan.com/zai/find_mate/v1/openclaw/recycle-skill/valuate`
- 只向用户返回估价结果、识别结果和补充建议，不暴露内部实现细节

## Quick Start

### 0. 新会话请求

如果用户当前是在发起一个新的独立估价请求，而不是延续上一轮补充属性，优先重置本地状态，避免旧 `skill_token` / `session_id` 污染新商品。

脚本会优先按当前对话的会话标识隔离本地状态；如果 Claude Code 在新对话或 `/clear` 后提供了新的会话标识，会自动使用新的本地状态文件。

典型新会话表达：
- `我有一个 iPhone 17 Pro 需要回收`
- `帮我估一下这台手机`
- `我想卖一个平板`

推荐命令：

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --reset-state \
  --text "我有一个 iPhone 17 Pro 需要回收"
```

### 1. 纯文字估价

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "帮我估一下这台 iPhone 13 128G"
```

### 2. 图片估价

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "帮我看看这个能卖多少" \
  --image "https://example.com/phone.jpg?sign=abc" \
  --image-media-id "oc_media_001"
```

使用本地文件（自动 base64 编码）：

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "帮我看看这个能卖多少" \
  --image "/path/to/local/image.jpg"
```

说明：
- `--image` 支持 URL 或本地文件路径；本地文件会自动 base64 编码为 data URI
- `--image-media-id` 可选，用于透传 OpenClaw 的媒体标识，便于排障和追踪
- 脚本会自动组装为 `attachments[].type=image`

### 3. 续接上一轮

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "128G 的，屏幕有轻微划痕" \
  --skill-token "<上一次返回的 skill_token>" \
  --session-id "<上一次返回的 session_id>"
```

### 4. 测试商品切换

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "换一个，帮我看看这台戴森吹风机" \
  --skill-token "<上一次返回的 skill_token>" \
  --session-id "<上一次返回的 session_id>"
```

## What to Check

- 首次请求是否自动返回 `skill_token`
- 同一商品补充信息时，`is_product_switched` 是否为 `false`
- 切换商品后，`is_product_switched` 是否为 `true`
- 返回里是否包含：
  - `session_id`
  - `valuation_context_id`
  - `recognized_item`
  - `valuation_result`
  - `missing_fields`
  - `clarification`
  - `reply`（完整估价报告文案）
  - `rate_limit_status`

## Reply Rules

- **如果响应里有 `reply` 字段且不为空，必须直接使用 `reply` 的内容展示给用户**，不要自行基于 JSON 数据生成文案
- `reply` 是后端 Step 5 报告生成模型产出的完整估价报告，包含价格、外观分级、注意事项等
- 只有当 `reply` 为空或 null 时（如识别不完整、需要澄清），才根据 `clarification` / `follow_up_question` 等字段引导用户

## Clarification Rules

- 如果响应里有 `clarification`，优先使用 `clarification`，不要自行生成澄清文案
- 当 `clarification.display_type == 2` 时，按结构化选项渲染给用户选择
- `clarification.core_attribute_options` 用于容量、颜色等核心属性澄清
- `clarification.model_option_groups` 用于型号候选澄清
- `follow_up_question` 只作为辅助提示，不是主协议
- 主链路默认使用自然语言续接，不要求额外拼接 `attrs` 或 `model_option`
- 不要自行发明脚本参数；只使用 `invoke_zhuanzhuan_recycle_skill.py --help` 中存在的参数

### 用户选择选项后的续接方式

- 推荐直接把用户选择转成自然语言文本续接，例如 `256g`、`512g`、`1tb`
- 只在确认是同一商品续聊时，才复用本地状态中的 `skill_token` 和 `session_id`
- 遇到新的独立估价请求，优先加 `--reset-state`
- `attrs` / `model_option` 仅作为补充能力，不是必须链路

### `attrs` 附件示例

```json
{
  "messages": [
    {
      "role": "user",
      "content": "我选 256G",
      "attachments": [
        {
          "type": "attrs",
          "payload": {
            "capacityId": "678742",
            "capacityIdName": "256G"
          }
        }
      ]
    }
  ]
}
```

### `model_option` 附件示例

```json
{
  "messages": [
    {
      "role": "user",
      "content": "我选这个型号",
      "attachments": [
        {
          "type": "model_option",
          "payload": {
            "selected_id": "1011385",
            "selected_name": "iPhone 17 Pro"
          }
        }
      ]
    }
  ]
}
```

## Common Flows

### 验证自动续接

1. 首次请求先传 `--reset-state`
2. 记录响应中的 `skill_token` 与 `session_id`
3. 第二轮直接补充文本属性，例如 `512g`
4. 检查是否仍为同一个 `session_id`

### 推荐续接命令

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "512g"
```

### 验证禁止自动续接

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "帮我估一下这台 iPhone" \
  --skill-token "<token>" \
  --allow-auto-resume false
```

### 强制新建 session

```bash
python3 {baseDir}/scripts/invoke_zhuanzhuan_recycle_skill.py \
  --text "重新开始，估一下这个" \
  --skill-token "<token>" \
  --force-new-session true
```

## Notes

- 如果返回 `TOKEN_DAILY_LIMIT_EXCEEDED` 或 `IP_DAILY_LIMIT_EXCEEDED`，先检查限流阈值
- 如果 `follow_up_question` 有内容，直接将 `follow_up_question` 的文本原样展示给用户，不要自行编造或替换
- 只有当价格为 0 且 `missing_fields` 为空且 `follow_up_question` 也为空时，才说明"当前暂时无法给出有效估价，可补充图片或稍后重试"
- 不要向用户输出 Apollo、cookie 池、下游报价接口、内部配置缺失等实现细节
- 若要切换环境，使用 `--base-url`
