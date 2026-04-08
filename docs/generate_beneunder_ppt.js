const pptxgen = require("pptxgenjs");

// 创建演示文稿
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "AI Assistant";
pres.title = "蕉下公司调研报告";

// 配色方案 - Forest & Moss (户外主题)
const colors = {
  primary: "2C5F2D",      // 森林绿
  secondary: "97BC62",    // 苔藓绿
  accent: "F5F5F5",       // 奶白色
  dark: "1A1A1A",         // 深色文字
  light: "FFFFFF",        // 白色
  gradient1: "667eea",    // 渐变色1
  gradient2: "764ba2"     // 渐变色2
};

// ==================== 封面页 ====================
let slide1 = pres.addSlide();
slide1.background = { color: colors.primary };

// 添加装饰形状
slide1.addShape(pres.shapes.OVAL, {
  x: -1,
  y: -1,
  w: 3,
  h: 3,
  fill: { color: colors.secondary, transparency: 30 }
});

slide1.addShape(pres.shapes.OVAL, {
  x: 8,
  y: 3,
  w: 3,
  h: 3,
  fill: { color: colors.secondary, transparency: 30 }
});

// 主标题
slide1.addText("🌿 蕉下 Beneunder", {
  x: 0.5,
  y: 2,
  w: 9,
  h: 1,
  fontSize: 54,
  fontFace: "Arial",
  color: colors.light,
  bold: true,
  align: "center"
});

// 副标题
slide1.addText("轻量化户外生活方式品牌调研报告", {
  x: 0.5,
  y: 3.2,
  w: 9,
  h: 0.5,
  fontSize: 28,
  fontFace: "Arial",
  color: colors.accent,
  align: "center"
});

// 底部信息
slide1.addText("2025年4月", {
  x: 0.5,
  y: 5,
  w: 9,
  h: 0.3,
  fontSize: 14,
  fontFace: "Arial",
  color: colors.accent,
  align: "center"
});

// ==================== 目录页 ====================
let slide2 = pres.addSlide();
slide2.background = { color: colors.light };

slide2.addText("📋 报告目录", {
  x: 0.5,
  y: 0.3,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

const tocItems = [
  { icon: "📊", title: "公司概览", desc: "基本信息与核心数据" },
  { icon: "📅", title: "发展历程", desc: "从创立到现在的关键里程碑" },
  { icon: "🎒", title: "主要产品", desc: "四大产品线详细介绍" },
  { icon: "🎯", title: "战略布局", desc: "品牌定位与渠道策略" },
  { icon: "💡", title: "商业模式", desc: "运营模式与面临挑战" }
];

tocItems.forEach((item, index) => {
  const y = 1.5 + index * 0.85;
  
  // 左侧数字圆圈
  slide2.addShape(pres.shapes.OVAL, {
    x: 0.5,
    y: y,
    w: 0.5,
    h: 0.5,
    fill: { color: colors.primary },
    line: { color: colors.primary }
  });
  
  slide2.addText((index + 1).toString(), {
    x: 0.5,
    y: y,
    w: 0.5,
    h: 0.5,
    fontSize: 20,
    fontFace: "Arial",
    color: colors.light,
    bold: true,
    align: "center",
    valign: "middle"
  });
  
  // 标题
  slide2.addText(`${item.icon} ${item.title}`, {
    x: 1.2,
    y: y,
    w: 4,
    h: 0.3,
    fontSize: 20,
    fontFace: "Arial",
    color: colors.dark,
    bold: true
  });
  
  // 描述
  slide2.addText(item.desc, {
    x: 1.2,
    y: y + 0.3,
    w: 8,
    h: 0.3,
    fontSize: 14,
    fontFace: "Arial",
    color: "666666"
  });
});

// ==================== 公司概览 ====================
let slide3 = pres.addSlide();
slide3.background = { color: colors.light };

// 标题
slide3.addText("📊 公司概览", {
  x: 0.5,
  y: 0.3,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

// 核心信息卡片
slide3.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.5,
  y: 1.3,
  w: 9,
  h: 1.5,
  fill: { color: colors.primary },
  rectRadius: 0.1
});

slide3.addText("蕉下(Beneunder)是由深圳减字科技有限公司于2013年创立的轻量化户外生活方式品牌,致力于为消费者提供高品质的户外防护产品。", {
  x: 0.7,
  y: 1.5,
  w: 8.6,
  h: 1.1,
  fontSize: 18,
  fontFace: "Arial",
  color: colors.light,
  align: "left",
  valign: "middle"
});

// 数据卡片
const statsData = [
  { number: "2013", label: "创立年份" },
  { number: "10+", label: "发展年限" },
  { number: "300+", label: "线下门店" },
  { number: "No.1", label: "防晒类目" }
];

statsData.forEach((stat, index) => {
  const x = 0.5 + index * 2.3;
  
  slide3.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x,
    y: 3.1,
    w: 2.1,
    h: 1.2,
    fill: { color: colors.secondary },
    rectRadius: 0.08
  });
  
  slide3.addText(stat.number, {
    x: x,
    y: 3.2,
    w: 2.1,
    h: 0.6,
    fontSize: 32,
    fontFace: "Arial",
    color: colors.light,
    bold: true,
    align: "center"
  });
  
  slide3.addText(stat.label, {
    x: x,
    y: 3.8,
    w: 2.1,
    h: 0.4,
    fontSize: 14,
    fontFace: "Arial",
    color: colors.light,
    align: "center"
  });
});

// 详细信息网格
const infoItems = [
  { label: "🏢 公司全称", value: "深圳减字科技有限公司" },
  { label: "👨‍💼 创始人", value: "马龙 (CEO) & 林泽 (总裁)" },
  { label: "📍 总部位置", value: "深圳市南山区" },
  { label: "🎯 品牌定位", value: "轻量化户外生活方式品牌" }
];

infoItems.forEach((item, index) => {
  const x = 0.5 + (index % 2) * 4.7;
  const y = 4.5 + Math.floor(index / 2) * 0.7;
  
  slide3.addText(item.label, {
    x: x,
    y: y,
    w: 4.5,
    h: 0.3,
    fontSize: 12,
    fontFace: "Arial",
    color: "999999"
  });
  
  slide3.addText(item.value, {
    x: x,
    y: y + 0.28,
    w: 4.5,
    h: 0.35,
    fontSize: 16,
    fontFace: "Arial",
    color: colors.dark,
    bold: true
  });
});

// ==================== 发展历程 ====================
let slide4 = pres.addSlide();
slide4.background = { color: colors.light };

slide4.addText("📅 发展历程", {
  x: 0.5,
  y: 0.3,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

// 时间轴
const timeline = [
  { year: "2013", event: "品牌创立,推出首款双层小黑伞" },
  { year: "2016", event: "上海开设首家线下直营店" },
  { year: "2017", event: "胶囊伞爆款上市,产品爆发期" },
  { year: "2022", event: "冲击IPO,递交招股书" },
  { year: "2023", event: "品牌升级,官宣周杰伦代言" },
  { year: "2024-25", event: "深化转型,拓展户外场景" }
];

// 绘制时间轴线条
slide4.addShape(pres.shapes.LINE, {
  x: 1.3,
  y: 1.5,
  w: 0,
  h: 3.8,
  line: { color: colors.primary, width: 3 }
});

timeline.forEach((item, index) => {
  const y = 1.6 + index * 0.65;
  
  // 时间点圆圈
  slide4.addShape(pres.shapes.OVAL, {
    x: 1.1,
    y: y,
    w: 0.4,
    h: 0.4,
    fill: { color: colors.primary },
    line: { color: colors.light, width: 2 }
  });
  
  // 年份
  slide4.addText(item.year, {
    x: 1.6,
    y: y,
    w: 1.5,
    h: 0.4,
    fontSize: 18,
    fontFace: "Arial",
    color: colors.primary,
    bold: true,
    valign: "middle"
  });
  
  // 事件描述
  slide4.addText(item.event, {
    x: 3.2,
    y: y,
    w: 6.3,
    h: 0.4,
    fontSize: 16,
    fontFace: "Arial",
    color: colors.dark,
    valign: "middle"
  });
});

// ==================== 主要产品 ====================
let slide5 = pres.addSlide();
slide5.background = { color: colors.light };

slide5.addText("🎒 主要产品线", {
  x: 0.5,
  y: 0.3,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

const products = [
  { icon: "☂️", name: "防晒伞系列", desc: "品牌起家产品,双层小黑伞、胶囊伞等,采用L.R.C科技防晒涂层" },
  { icon: "👕", name: "防晒服饰", desc: "专业防晒服饰系列,防晒衣、防晒帽等,满足多场景需求" },
  { icon: "🎒", name: "户外装备", desc: "户外背包、折叠椅、野餐垫等轻量化户外装备" },
  { icon: "🧢", name: "防护配件", desc: "防晒帽、墨镜、冰袖等防护配件,完善产品矩阵" }
];

products.forEach((product, index) => {
  const x = 0.5 + (index % 2) * 4.7;
  const y = 1.3 + Math.floor(index / 2) * 2.1;
  
  // 产品卡片
  slide5.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x,
    y: y,
    w: 4.5,
    h: 1.9,
    fill: { color: colors.accent },
    line: { color: colors.secondary, width: 2 },
    rectRadius: 0.1,
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.1 }
  });
  
  // 图标背景
  slide5.addShape(pres.shapes.OVAL, {
    x: x + 0.2,
    y: y + 0.2,
    w: 0.7,
    h: 0.7,
    fill: { color: colors.secondary }
  });
  
  // 图标
  slide5.addText(product.icon, {
    x: x + 0.2,
    y: y + 0.2,
    w: 0.7,
    h: 0.7,
    fontSize: 28,
    align: "center",
    valign: "middle"
  });
  
  // 产品名称
  slide5.addText(product.name, {
    x: x + 1.1,
    y: y + 0.3,
    w: 3.2,
    h: 0.5,
    fontSize: 20,
    fontFace: "Arial",
    color: colors.dark,
    bold: true
  });
  
  // 产品描述
  slide5.addText(product.desc, {
    x: x + 0.2,
    y: y + 1,
    w: 4.1,
    h: 0.7,
    fontSize: 14,
    fontFace: "Arial",
    color: "666666"
  });
});

// ==================== 战略布局 ====================
let slide6 = pres.addSlide();
slide6.background = { color: colors.light };

slide6.addText("🎯 战略布局", {
  x: 0.5,
  y: 0.3,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

const strategies = [
  { title: "📍 品牌定位升级", content: "从'防晒专家'升级为'轻量化户外生活方式品牌',突破单一品类限制" },
  { title: "🛒 全渠道策略", content: "线上天猫为核心,配合京东、小程序;线下开设近300家门店" },
  { title: "👥 DTC模式", content: "直连消费者,数据驱动产品开发,快速响应市场需求" },
  { title: "🤝 明星代言", content: "2023年官宣周杰伦代言,拓展品牌认知度和影响力" }
];

strategies.forEach((strategy, index) => {
  const y = 1.3 + index * 1.1;
  
  // 左侧装饰条
  slide6.addShape(pres.shapes.RECTANGLE, {
    x: 0.5,
    y: y,
    w: 0.08,
    h: 0.9,
    fill: { color: colors.primary }
  });
  
  // 内容卡片
  slide6.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7,
    y: y,
    w: 8.8,
    h: 0.9,
    fill: { color: colors.accent },
    rectRadius: 0.08,
    shadow: { type: "outer", color: "000000", blur: 3, offset: 1, angle: 135, opacity: 0.08 }
  });
  
  // 标题
  slide6.addText(strategy.title, {
    x: 0.9,
    y: y + 0.1,
    w: 8.4,
    h: 0.35,
    fontSize: 18,
    fontFace: "Arial",
    color: colors.primary,
    bold: true
  });
  
  // 内容
  slide6.addText(strategy.content, {
    x: 0.9,
    y: y + 0.45,
    w: 8.4,
    h: 0.35,
    fontSize: 14,
    fontFace: "Arial",
    color: "666666"
  });
});

// ==================== 商业模式 ====================
let slide7 = pres.addSlide();
slide7.background = { color: colors.light };

slide7.addText("💡 商业模式", {
  x: 0.5,
  y: 0.3,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

// 商业模式卡片
const businessModels = [
  { label: "🏭 生产模式", value: "OEM代工生产" },
  { label: "🛍️ 销售模式", value: "线上线下全渠道" },
  { label: "📱 营销模式", value: "社交媒体+KOL" },
  { label: "🎯 用户群体", value: "年轻女性为主" }
];

businessModels.forEach((model, index) => {
  const x = 0.5 + (index % 2) * 4.7;
  const y = 1.3 + Math.floor(index / 2) * 1.3;
  
  slide7.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x,
    y: y,
    w: 4.5,
    h: 1.1,
    fill: { color: colors.secondary },
    rectRadius: 0.1
  });
  
  slide7.addText(model.label, {
    x: x + 0.2,
    y: y + 0.15,
    w: 4.1,
    h: 0.4,
    fontSize: 14,
    fontFace: "Arial",
    color: colors.light
  });
  
  slide7.addText(model.value, {
    x: x + 0.2,
    y: y + 0.55,
    w: 4.1,
    h: 0.45,
    fontSize: 20,
    fontFace: "Arial",
    color: colors.light,
    bold: true
  });
});

// 面临挑战
slide7.addText("⚠️ 面临挑战", {
  x: 0.5,
  y: 3.9,
  w: 9,
  h: 0.5,
  fontSize: 20,
  fontFace: "Arial",
  color: colors.primary,
  bold: true
});

const challenges = [
  "竞争加剧:传统品牌和新兴品牌纷纷进入防晒市场",
  "产品同质化:防晒产品技术壁垒相对较低,易被模仿",
  "营销依赖:高度依赖社交媒体营销,获客成本上升",
  "转型压力:从防晒到全户外场景的认知转变需要时间"
];

challenges.forEach((challenge, index) => {
  slide7.addText(`• ${challenge}`, {
    x: 0.7,
    y: 4.4 + index * 0.35,
    w: 8.8,
    h: 0.3,
    fontSize: 14,
    fontFace: "Arial",
    color: colors.dark
  });
});

// ==================== 总结页 ====================
let slide8 = pres.addSlide();
slide8.background = { color: colors.primary };

// 装饰元素
slide8.addShape(pres.shapes.OVAL, {
  x: 7,
  y: -1,
  w: 4,
  h: 4,
  fill: { color: colors.secondary, transparency: 30 }
});

slide8.addShape(pres.shapes.OVAL, {
  x: -1,
  y: 3,
  w: 3,
  h: 3,
  fill: { color: colors.secondary, transparency: 30 }
});

slide8.addText("📋 总结", {
  x: 0.5,
  y: 1.5,
  w: 9,
  h: 0.8,
  fontSize: 40,
  fontFace: "Arial",
  color: colors.light,
  bold: true,
  align: "center"
});

slide8.addText([
  { text: "蕉下从2013年创立至今,凭借创新的防晒产品定位和精准的营销策略,\n", options: { breakLine: true } },
  { text: "在短短十年内成为防晒类目的领导品牌。\n\n", options: { breakLine: true } },
  { text: "面对市场竞争和转型挑战,蕉下正在从'小防晒'向'大户外'升级,\n", options: { breakLine: true } },
  { text: "探索更广阔的市场空间和增长曲线。", options: { breakLine: true } }
], {
  x: 1,
  y: 2.5,
  w: 8,
  h: 2,
  fontSize: 18,
  fontFace: "Arial",
  color: colors.accent,
  align: "center",
  lineSpacing: 28
});

slide8.addText("🌿 蕉下 · 让人们随时随地享受户外的快乐", {
  x: 0.5,
  y: 4.8,
  w: 9,
  h: 0.5,
  fontSize: 16,
  fontFace: "Arial",
  color: colors.accent,
  align: "center",
  italic: true
});

// 保存文件
pres.writeFile({ fileName: "蕉下公司调研报告.pptx" })
  .then(fileName => {
    console.log(`✅ PPT已成功创建: ${fileName}`);
  })
  .catch(err => {
    console.error("❌ 创建PPT时出错:", err);
  });
