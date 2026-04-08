# 书籍封面图片说明

## 使用真实书皮图片

如需使用真实的教材封面图片,请将图片文件放置在此目录中:

### 命名规范

```
初一-人教版-数学.jpg
初二-人教版-数学.jpg
初三-人教版-数学.jpg
高一-人教版-数学.jpg
高二-人教版-数学.jpg
高三-人教版-数学.jpg
```

### 图片要求

- **格式**: JPG 或 PNG
- **尺寸**: 推荐 200x280px (保持教材封面的宽高比)
- **质量**: 优化后的图片,建议 < 100KB

### 如何启用

在 `AdminCourses.tsx` 中修改 `book-spine` 样式,添加背景图片:

\`\`\`css
.book-card[data-grade="初二"] .book-spine {
  background-image: url('/images/books/初二-人教版-数学.jpg');
  background-size: cover;
  background-position: center;
}
\`\`\`

### 示例代码

可以在 `AdminCourses.tsx` 中动态设置背景图片:

\`\`\`tsx
<div 
  className="book-spine"
  style={{
    backgroundImage: \`url(/images/books/\${book.grade}-\${edition.edition}-\${subject.subject}.jpg)\`
  }}
>
\`\`\`

### 免费图片资源

可以从以下网站获取教材封面:
1. 各出版社官网
2. 教育部教材目录
3. 注意版权问题,仅用于内部教学系统

## 当前效果

当前使用纯CSS渐变和纹理模拟书籍质感,包括:
- 🎨 渐变色书脊
- 📚 木纹书架背景
- 📖 3D翻书动画
- 🎯 书脊装饰线条
