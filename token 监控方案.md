# Token 监控与模型切换方案

## ⚠️ 重要说明

**我无法创建自动切换模型的 skill**，因为：
1. skill 是平台级功能，需平台开发者实现
2. 我无法访问模型配置或 API 权限
3. 我无法设置自动化触发器

---

## ✅ 可行方案

### 方案 1：手动查询（推荐）

使用内置工具查询 token 用量：

```
get_token_usage --days 7
```

**阈值建议**：
| 用量 | 操作 |
|------|------|
| 75% | ⚡ 注意，准备切换 |
| 90% | ⚠️ 警告，立即切换 |
| 95% | 🚨 紧急，必须切换 |

---

### 方案 2：本地脚本监控

已创建脚本：`/app/working/aiteacher/scripts/check-token.sh`

**使用方式**：
```bash
chmod +x check-token.sh
./check-token.sh
```

**需要配置**：
- 替换 `YOUR_API_ENDPOINT` 为你的 token 查询 API
- 设置 crontab 定时运行

---

### 方案 3：Crontab 定时检查

```bash
# 每小时检查一次
0 * * * * /app/working/aiteacher/scripts/check-token.sh >> /var/log/token-monitor.log 2>&1
```

---

## 🔄 备用模型优先级

根据性价比和性能推荐：

| 优先级 | 模型 | 适用场景 |
|--------|------|---------|
| 1 | qwen3.5-122b-a10b | 复杂分析任务 |
| 2 | qwen3.5-35b-a3b | 日常对话 |
| 3 | qwen3-max | 高质量输出 |
| 4 | qwen3.5-27b | 简单任务 |
| 5 | qwen3.5-397b-a17b | 超复杂任务 |

---

## 💡 节省 Token 建议

1. **用 iflow 代替直接提问**
   ```
   ❌ 直接问："分析这个代码..."
   ✅ 用 iflow: iflow "分析代码" --timeout 60
   ```

2. **任务分拆**
   ```
   大任务 → 拆成 3-5 个小任务 → 逐个执行
   ```

3. **复用结果**
   ```
   iflow "分析..." > result.md
   后续直接读取 result.md
   ```

4. **减少上下文**
   - 只发送必要信息
   - 用文件引用代替大段内容

---

## 📊 当前 Token 查询

可以直接问我：
```
"查询过去 7 天的 token 用量"
```

我会调用 `get_token_usage` 工具帮你查询。

---

*创建时间：2026 年 3 月 24 日*
