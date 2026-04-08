# 真实书皮照片集成指南

## 方法一:使用真实图片文件

### 1. 准备图片

将教材封面图片放入 `/public/images/books/` 目录:

```
public/images/books/
├── 初一-人教版-数学.jpg
├── 初二-人教版-数学.jpg
├── 初三-人教版-数学.jpg
├── 高一-人教版-数学.jpg
├── 高二-人教版-数学.jpg
└── 高三-人教版-数学.jpg
```

### 2. 修改组件代码

在 `AdminCourses.tsx` 中修改书籍渲染部分:

```tsx
<div 
  className="book-spine"
  style={{
    backgroundImage: `url(/images/books/${encodeURIComponent(book.grade + '-' + book.editions[0]?.edition + '-' + book.editions[0]?.subjects[0]?.subject)}.jpg)`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  }}
>
  <div className="book-texture"></div>
  {/* ... 其他内容 */}
</div>
```

### 3. 添加渐变遮罩

在 CSS 中添加半透明遮罩,让文字更清晰:

```css
.book-spine.has-image::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(0, 0, 0, 0.3) 0%,
    rgba(0, 0, 0, 0.5) 100%
  );
  z-index: 1;
}

.book-spine.has-image > * {
  position: relative;
  z-index: 2;
}
```

## 方法二:使用在线图片

### 1. 定义图片映射

在 `AdminCourses.tsx` 中添加:

```tsx
const bookImages: Record<string, string> = {
  '初一': 'https://example.com/images/grade7.jpg',
  '初二': 'https://example.com/images/grade8.jpg',
  '初三': 'https://example.com/images/grade9.jpg',
  '高一': 'https://example.com/images/grade10.jpg',
  '高二': 'https://example.com/images/grade11.jpg',
  '高三': 'https://example.com/images/grade12.jpg',
};
```

### 2. 应用到书籍

```tsx
<div 
  className="book-spine has-image"
  style={{
    backgroundImage: bookImages[book.grade] 
      ? `url(${bookImages[book.grade]})` 
      : undefined,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  }}
>
```

## 方法三:使用 Canvas 生成书皮

### 1. 创建动态书皮组件

```tsx
const BookCover: React.FC<{ grade: string; color: string }> = ({ grade, color }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // 绘制渐变背景
    const gradient = ctx.createLinearGradient(0, 0, 160, 200);
    gradient.addColorStop(0, color);
    gradient.addColorStop(1, shadeColor(color, -20));
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 160, 200);
    
    // 绘制装饰线
    ctx.strokeStyle = 'rgba(255, 215, 0, 0.5)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(10, 20);
    ctx.lineTo(10, 180);
    ctx.stroke();
    
    // 绘制文字
    ctx.fillStyle = 'white';
    ctx.font = 'bold 18px SimSun';
    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
    ctx.shadowBlur = 4;
    
    // 垂直文字
    const chars = grade.split('');
    chars.forEach((char, i) => {
      ctx.fillText(char, 80, 50 + i * 25);
    });
  }, [grade, color]);
  
  return <canvas ref={canvasRef} width={160} height={200} />;
};
```

## 推荐方案

当前实现使用了纯 CSS 方案,已经提供了很好的视觉效果:

✅ **优点**:
- 无需额外图片资源
- 加载速度快
- 可维护性好
- 动态颜色调整
- 支持主题切换

🎨 **效果**:
- 真实的木纹书架
- 3D书籍效果
- 书脊装饰线条
- 悬停翻书动画
- 展开详情面板

## 进一步优化建议

1. **添加光影效果**: 使用 CSS 滤镜模拟真实光照
2. **磨损效果**: 添加轻微的磨损纹理
3. **书脊厚度**: 根据章节数量调整书籍厚度
4. **个性化封面**: 为不同科目使用不同的设计模板

## 示例图片来源

如果需要真实教材封面,可以从以下渠道获取(注意版权):

1. **出版社官网**: 人民教育出版社、北师大出版社等
2. **教育部教材目录**: http://www.moe.gov.cn/
3. **自制封面**: 使用设计工具自己制作教材封面

---

当前实现的纯 CSS 效果已经非常逼真,建议先使用当前方案,后续根据需要再集成真实图片。
