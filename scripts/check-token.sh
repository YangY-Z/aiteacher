#!/bin/bash
# token 监控脚本
# 用法：./check-token.sh

DAYS=7
LIMIT=1000000

echo "📊 查询过去 ${DAYS} 天的 token 用量..."

# 调用 get_token_usage (需要你有相应的 CLI 工具)
# 这里是示例，实际需要对接你的 token 查询 API
USAGE=$(curl -s "YOUR_API_ENDPOINT/token-usage?days=${DAYS}" | jq '.total_tokens')

if [ -z "$USAGE" ]; then
    echo "❌ 无法获取 token 用量"
    exit 1
fi

REMAINING=$((LIMIT - USAGE))
PERCENT=$((USAGE * 100 / LIMIT))

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "已用：${USAGE} / ${LIMIT}"
echo "剩余：${REMAINING}"
echo "进度：${PERCENT}%"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $PERCENT -ge 90 ]; then
    echo "⚠️  警告：用量已超过 90%！"
    echo "建议切换到备用模型："
    echo "  1. qwen3.5-122b-a10b (推荐)"
    echo "  2. qwen3.5-35b-a3b"
    echo "  3. qwen3-max"
    exit 2
elif [ $PERCENT -ge 75 ]; then
    echo "⚡ 注意：用量已超过 75%"
    exit 1
else
    echo "✅ 用量正常"
    exit 0
fi
