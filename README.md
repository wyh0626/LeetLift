# LeetLift

> 赛博健身：每天早上随机推送一道算法题。再来一组 💪

LeetLift 使用 GitHub Actions 定时选题，通过 PushPlus 发送到邮箱、微信、App 或 ClawBot。它支持 LeetCode Hot 100 和全题库，默认不重复；完成后可以在推送中选择“会了 / 卡住 / 不会”，GitHub 会自动维护复习队列。

## 能做什么

- 每天北京时间 10:00 自动推送一道题
- `hot100` / `all` 两种题目范围
- 可按简单、中等、困难筛选，默认排除会员题
- 一轮内避免重复，全部练完后自动开始下一轮
- 推送包含题号、中英文标题、难度、知识点和 LeetCode 链接
- 通过预填 GitHub Issue 收集“会了 / 卡住 / 不会”反馈
- 到期复习题优先于新题，反馈 Issue 处理后自动关闭
- 纯 Python 标准库，无服务器、无数据库、无第三方包

## 成本

个人使用基本是 0 元：

- 公开仓库使用标准 GitHub 托管 Runner 不计费；私有仓库受账户 Actions 配额限制
- PushPlus 邮件等基础渠道可免费使用，一天一条远低于一般个人用量
- 题目数据来自力扣网页使用的公开 GraphQL 接口

PushPlus 的免费策略和 GitHub Actions 配额可能调整，请以各自官网当前说明为准。

## 一次性启用

### 1. 获取 PushPlus Token

1. 打开 [PushPlus](https://www.pushplus.plus/)，登录并关注其微信公众号。
2. 在个人中心复制你的用户 Token。
3. 在 `个人资料 → 邮箱` 中绑定并验证收件邮箱；邮件渠道不会读取仓库中的邮箱地址。
4. 不要把 Token 写进代码或 `config.json`。

### 2. 添加 GitHub Secret

进入仓库：

`Settings → Secrets and variables → Actions → New repository secret`

创建：

| Name | Value |
| --- | --- |
| `PUSHPLUS_TOKEN` | 你的 PushPlus 用户 Token |

### 3. 允许工作流回写状态

进入：

`Settings → Actions → General → Workflow permissions`

选择 `Read and write permissions`。此外请确认仓库已启用 Issues；反馈按钮依赖 GitHub Issue。

如果默认分支启用了“禁止直接提交”的保护规则，需要允许 `github-actions[bot]` 写入，或者为此仓库调整对应规则。`state.json` 必须能被工作流提交，才能跨天去重和记录复习计划。

### 4. 首次测试

进入 `Actions → Daily LeetLift → Run workflow`：

1. 先选择 `dry_run=true`，确认选题和 HTML 生成正常；这次不会推送。
2. 再选择 `dry_run=false`，确认已验证的邮箱收到消息。

定时工作流只会在默认分支上的 workflow 文件生效。

## 配置

编辑 [`config.json`](./config.json)：

```json
{
  "scope": "hot100",
  "difficulty": "all",
  "pushplus_channel": "mail",
  "exclude_paid": true,
  "prefer_review": true,
  "timezone": "Asia/Shanghai",
  "max_history": 365
}
```

| 字段 | 可选值 | 说明 |
| --- | --- | --- |
| `scope` | `hot100` / `all` | 每日默认选题范围 |
| `difficulty` | `all` / `easy` / `medium` / `hard` | 难度筛选 |
| `pushplus_channel` | `mail` / `wechat` / `app` / `clawbot` | PushPlus 发送渠道 |
| `exclude_paid` | `true` / `false` | 是否排除会员题 |
| `prefer_review` | `true` / `false` | 是否优先推送到期复习题 |
| `timezone` | IANA 时区名 | 反馈和历史记录使用的日期时区 |
| `max_history` | 大于等于 30 | `state.json` 最多保留多少条推送历史 |

手动运行工作流时，可以临时覆盖 `scope`，不会修改 `config.json`。

## 修改推送时间

默认配置位于 [`.github/workflows/daily.yml`](./.github/workflows/daily.yml)：

```yaml
on:
  schedule:
    - cron: "0 2 * * *"
```

GitHub cron 使用 UTC，`0 2 * * *` 对应北京时间每天 10:00。GitHub 定时任务可能有几分钟延迟，不适合要求准点到秒的场景。

常用时间：

| 北京时间 | UTC cron |
| --- | --- |
| 07:30 | `30 23 * * *` |
| 08:00 | `0 0 * * *` |
| 09:00 | `0 1 * * *` |
| 10:00 | `0 2 * * *` |

修改 cron 后提交到默认分支即可。

## 反馈与复习机制

PushPlus 邮件和服务号都是单向推送，因此这里采用零后端方案：

1. 在邮件或微信推送底部点击“会了 / 卡住 / 不会”。
2. 浏览器打开已经填好的 GitHub Issue。
3. 点击 `Submit new issue`。
4. `Record LeetLift Feedback` 工作流验证提交人是仓库 owner，更新 `state.json`，然后自动关闭 Issue。

复习间隔：

- 会了：逐步延长到 3、7、15、30、60、90 天
- 卡住：次日复习，并降低当前熟练等级
- 不会：次日复习，从第一级重新开始

这是两次点击方案，需要手机浏览器保持 GitHub 登录。如果以后需要真正的一键反馈，可以把链接替换为 Cloudflare Worker，但当前版本不需要部署任何后端。

## 本地运行

项目要求 Python 3.11+，没有依赖安装步骤。

```bash
python3 -m unittest discover -s tests -v
python3 -m leetlift daily --dry-run --repository wyh0626/LeetLift
```

真实推送：

```bash
PUSHPLUS_TOKEN="你的 token" python3 -m leetlift daily --repository wyh0626/LeetLift
```

不要把包含真实 Token 的 shell 历史、日志或截图提交到仓库。

## 项目结构

```text
.
├── .github/workflows/
│   ├── daily.yml       # 定时选题、推送、回写状态
│   └── feedback.yml    # 处理反馈 Issue、更新复习队列
├── leetlift/           # Python 标准库实现
├── tests/              # 单元测试
├── config.json         # 用户配置
└── state.json          # 去重、历史和复习状态
```

## 稳定性说明

LeetCode 没有为这个场景提供承诺稳定的公开 API；本项目调用的是其网页当前使用的 GraphQL 接口。如果字段将来变化，工作流会明确失败且不更新 `state.json`，不会把一次失败误记成已经推送。

PushPlus 请求使用官方消息接口的 `html` 模板。只有收到成功码后，LeetLift 才会保存当天状态。

## License

[MIT](./LICENSE)
