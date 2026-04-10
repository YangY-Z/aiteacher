#!/usr/bin/env python3
"""
电磁感应模板扩展演示
展示如何用模板驱动方案生成复杂物理场景图片
"""

import json
import math

class ElectromagneticInductionTemplate:
    """电磁感应专用模板"""
    
    def render(self, params: dict) -> str:
        """渲染电磁感应图"""
        title = params.get("title", "电磁感应现象")
        magnet_position = params.get("magnet_position", "entering")  # entering, inside, leaving
        coil_turns = params.get("coil_turns", 5)
        show_magnetic_field = params.get("show_magnetic_field", True)
        show_current = params.get("show_current", True)
        show_formula = params.get("show_formula", True)
        
        width = 900
        height = 600
        
        # 生成磁场线
        magnetic_field_lines = self._generate_magnetic_field(magnet_position, show_magnetic_field)
        
        # 生成线圈
        coil_svg = self._generate_coil(coil_turns, width, height)
        
        # 生成电流指示
        current_indicator = self._generate_current_indicator(magnet_position, show_current)
        
        # 生成公式框
        formula_box = self._generate_formula_box(show_formula)
        
        # 生成磁铁
        magnet_svg = self._generate_magnet(magnet_position)
        
        # 组装完整SVG
        svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <!-- 渐变定义 -->
        <linearGradient id="magnet_n" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#E53935"/>
            <stop offset="100%" style="stop-color:#EF5350"/>
        </linearGradient>
        <linearGradient id="magnet_s" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#1E88E5"/>
            <stop offset="100%" style="stop-color:#42A5F5"/>
        </linearGradient>
        <linearGradient id="coil_grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#FFA726"/>
            <stop offset="100%" style="stop-color:#FB8C00"/>
        </linearGradient>
        
        <!-- 箭头标记 -->
        <marker id="arrow_red" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#E53935"/>
        </marker>
        <marker id="arrow_blue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#1E88E5"/>
        </marker>
        <marker id="arrow_green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <polygon points="0 0, 10 3, 0 6" fill="#43A047"/>
        </marker>
        
        <!-- 发光效果 -->
        <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        
        <!-- 磁场线动画 -->
        <style>
            @keyframes flow {{
                0% {{ stroke-dashoffset: 20; }}
                100% {{ stroke-dashoffset: 0; }}
            }}
            .field-line {{
                stroke-dasharray: 5,5;
                animation: flow 1s linear infinite;
            }}
        </style>
    </defs>
    
    <!-- 背景 -->
    <rect width="{width}" height="{height}" fill="#FAFAFA"/>
    
    <!-- 标题 -->
    <text x="{width/2}" y="50" text-anchor="middle" fill="#333" font-size="28" font-weight="bold">
        {title}
    </text>
    
    <!-- 磁场线 -->
    {magnetic_field_lines}
    
    <!-- 线圈 -->
    {coil_svg}
    
    <!-- 磁铁 -->
    {magnet_svg}
    
    <!-- 电流指示器 -->
    {current_indicator}
    
    <!-- 公式框 -->
    {formula_box}
    
    <!-- 图例 -->
    <g transform="translate(680, 450)">
        <rect x="0" y="0" width="200" height="120" rx="10" fill="white" stroke="#DDD" stroke-width="2"/>
        <text x="100" y="25" text-anchor="middle" fill="#333" font-size="14" font-weight="bold">图例说明</text>
        
        <rect x="20" y="40" width="30" height="15" fill="url(#magnet_n)"/>
        <text x="60" y="52" fill="#666" font-size="12">N极（北极）</text>
        
        <rect x="20" y="65" width="30" height="15" fill="url(#magnet_s)"/>
        <text x="60" y="77" fill="#666" font-size="12">S极（南极）</text>
        
        <circle cx="35" cy="100" r="8" fill="none" stroke="#43A047" stroke-width="2"/>
        <text x="60" y="104" fill="#666" font-size="12">感应电流</text>
    </g>
</svg>"""
        return svg
    
    def _generate_magnet(self, position: str) -> str:
        """生成磁铁"""
        # 根据位置调整磁铁坐标
        positions = {
            "entering": (200, 250),
            "inside": (350, 250),
            "leaving": (500, 250)
        }
        x, y = positions.get(position, (200, 250))
        
        return f"""
    <!-- 磁铁 -->
    <g transform="translate({x}, {y})">
        <!-- N极 -->
        <rect x="0" y="0" width="60" height="80" rx="5" fill="url(#magnet_n)" filter="url(#glow)">
            <animate attributeName="x" from="0" to="0" dur="2s" repeatCount="indefinite"/>
        </rect>
        <text x="30" y="50" text-anchor="middle" fill="white" font-size="28" font-weight="bold">N</text>
        
        <!-- S极 -->
        <rect x="60" y="0" width="60" height="80" rx="5" fill="url(#magnet_s)" filter="url(#glow)"/>
        <text x="90" y="50" text-anchor="middle" fill="white" font-size="28" font-weight="bold">S</text>
        
        <!-- 磁铁标识 -->
        <text x="60" y="100" text-anchor="middle" fill="#666" font-size="14">条形磁铁</text>
    </g>"""
    
    def _generate_magnetic_field(self, magnet_position: str, show: bool) -> str:
        """生成磁场线"""
        if not show:
            return ""
        
        # 根据磁铁位置调整磁场线
        offset_map = {"entering": 0, "inside": 150, "leaving": 300}
        offset = offset_map.get(magnet_position, 0)
        
        lines = []
        # 生成多条磁场线
        for i in range(5):
            y_offset = 200 + i * 30
            # 左侧磁场线（从N极出发）
            lines.append(f"""
    <path d="M {220 + offset} {y_offset} 
             Q {180 + offset} {y_offset - 40} {140 + offset} {y_offset - 20}
             Q {100 + offset} {y_offset} {140 + offset} {y_offset + 20}
             Q {180 + offset} {y_offset + 40} {220 + offset} {y_offset}" 
          fill="none" stroke="#E53935" stroke-width="2" class="field-line" opacity="0.6"/>""")
            
            # 右侧磁场线（进入S极）
            lines.append(f"""
    <path d="M {340 + offset} {y_offset} 
             Q {380 + offset} {y_offset - 40} {420 + offset} {y_offset - 20}
             Q {460 + offset} {y_offset} {420 + offset} {y_offset + 20}
             Q {380 + offset} {y_offset + 40} {340 + offset} {y_offset}" 
          fill="none" stroke="#1E88E5" stroke-width="2" class="field_line" opacity="0.6"/>""")
        
        return '\n'.join(lines)
    
    def _generate_coil(self, turns: int, width: int, height: int) -> str:
        """生成线圈"""
        coil_x = 550
        coil_y = 200
        coil_height = 200
        
        # 生成线圈环
        coil_paths = []
        for i in range(turns):
            y = coil_y + (i * coil_height / turns)
            coil_paths.append(f"""
    <ellipse cx="{coil_x}" cy="{y + 20}" rx="40" ry="15" 
             fill="none" stroke="url(#coil_grad)" stroke-width="4" opacity="0.8"/>""")
        
        # 连接线
        coil_paths.append(f"""
    <!-- 连接线 -->
    <line x1="{coil_x - 40}" y1="{coil_y + 20}" x2="{coil_x - 40}" y2="{coil_y + coil_height + 40}" 
          stroke="#FB8C00" stroke-width="3"/>
    <line x1="{coil_x + 40}" y1="{coil_y + 20}" x2="{coil_x + 40}" y2="{coil_y + coil_height + 40}" 
          stroke="#FB8C00" stroke-width="3"/>""")
        
        # 检流计符号
        coil_paths.append(f"""
    <!-- 检流计 -->
    <circle cx="{coil_x}" cy="{coil_y + coil_height + 70}" r="25" fill="white" stroke="#333" stroke-width="2"/>
    <text x="{coil_x}" y="{coil_y + coil_height + 75}" text-anchor="middle" fill="#333" font-size="12" font-weight="bold">G</text>
    <line x1="{coil_x - 40}" y1="{coil_y + coil_height + 40}" x2="{coil_x - 20}" y2="{coil_y + coil_height + 70}" 
          stroke="#FB8C00" stroke-width="3"/>
    <line x1="{coil_x + 40}" y1="{coil_y + coil_height + 40}" x2="{coil_x + 20}" y2="{coil_y + coil_height + 70}" 
          stroke="#FB8C00" stroke-width="3"/>""")
        
        return '\n'.join(coil_paths)
    
    def _generate_current_indicator(self, magnet_position: str, show: bool) -> str:
        """生成电流方向指示"""
        if not show:
            return ""
        
        # 根据磁铁运动方向决定电流方向
        # 进入：顺时针  离开：逆时针  内部：无
        if magnet_position == "inside":
            return """
    <text x="550" y="160" text-anchor="middle" fill="#43A047" font-size="16" font-weight="bold">
        磁通量不变，无感应电流
    </text>"""
        
        direction_text = "顺时针" if magnet_position == "entering" else "逆时针"
        arrow_direction = "→" if magnet_position == "entering" else "←"
        
        return f"""
    <!-- 电流方向指示 -->
    <g transform="translate(550, 150)">
        <circle cx="0" cy="0" r="30" fill="none" stroke="#43A047" stroke-width="3">
            <animate attributeName="stroke-opacity" values="1;0.5;1" dur="1.5s" repeatCount="indefinite"/>
        </circle>
        <text x="0" y="-45" text-anchor="middle" fill="#43A047" font-size="14" font-weight="bold">
            感应电流
        </text>
        <text x="0" y="5" text-anchor="middle" fill="#43A047" font-size="20" font-weight="bold">
            {arrow_direction}
        </text>
        <text x="0" y="50" text-anchor="middle" fill="#666" font-size="12">
            {direction_text}方向
        </text>
    </g>"""
    
    def _generate_formula_box(self, show: bool) -> str:
        """生成公式框"""
        if not show:
            return ""
        
        return """
    <!-- 法拉第电磁感应定律 -->
    <g transform="translate(50, 480)">
        <rect x="0" y="0" width="280" height="100" rx="10" fill="white" stroke="#667eea" stroke-width="2"/>
        <text x="140" y="30" text-anchor="middle" fill="#667eea" font-size="16" font-weight="bold">
            法拉第电磁感应定律
        </text>
        <text x="140" y="60" text-anchor="middle" fill="#333" font-size="18" font-weight="bold">
            ε = -dΦ/dt
        </text>
        <text x="140" y="85" text-anchor="middle" fill="#666" font-size="12">
            感应电动势 = 磁通量变化率
        </text>
    </g>
    
    <!-- 楞次定律 -->
    <g transform="translate(360, 480)">
        <rect x="0" y="0" width="280" height="100" rx="10" fill="white" stroke="#E91E63" stroke-width="2"/>
        <text x="140" y="30" text-anchor="middle" fill="#E91E63" font-size="16" font-weight="bold">
            楞次定律
        </text>
        <text x="140" y="60" text-anchor="middle" fill="#333" font-size="14">
            感应电流方向总是阻碍
        </text>
        <text x="140" y="80" text-anchor="middle" fill="#333" font-size="14">
            引起感应电流的磁通量变化
        </text>
    </g>"""


def demo_electromagnetic_induction():
    """演示电磁感应场景的模板生成"""
    
    print("=" * 60)
    print("🧲 电磁感应模板扩展演示")
    print("=" * 60)
    
    template = ElectromagneticInductionTemplate()
    
    # 场景1: 磁铁进入线圈
    print("\n📍 场景1: 磁铁进入线圈")
    params1 = {
        "title": "电磁感应 - 磁铁进入线圈",
        "magnet_position": "entering",
        "coil_turns": 6,
        "show_magnetic_field": True,
        "show_current": True,
        "show_formula": True
    }
    
    print("\n📋 LLM 输出的参数：")
    print(json.dumps(params1, ensure_ascii=False, indent=2))
    
    svg1 = template.render(params1)
    with open("em_induction_entering.svg", "w", encoding="utf-8") as f:
        f.write(svg1)
    print("✅ 已生成: em_induction_entering.svg")
    
    # 场景2: 磁铁在线圈内静止
    print("\n" + "=" * 60)
    print("📍 场景2: 磁铁在线圈内静止")
    params2 = {
        "title": "电磁感应 - 磁铁静止在线圈内",
        "magnet_position": "inside",
        "coil_turns": 6,
        "show_magnetic_field": True,
        "show_current": True,
        "show_formula": True
    }
    
    print("\n📋 LLM 输出的参数：")
    print(json.dumps(params2, ensure_ascii=False, indent=2))
    
    svg2 = template.render(params2)
    with open("em_induction_inside.svg", "w", encoding="utf-8") as f:
        f.write(svg2)
    print("✅ 已生成: em_induction_inside.svg")
    
    # 场景3: 磁铁离开线圈
    print("\n" + "=" * 60)
    print("📍 场景3: 磁铁离开线圈")
    params3 = {
        "title": "电磁感应 - 磁铁离开线圈",
        "magnet_position": "leaving",
        "coil_turns": 6,
        "show_magnetic_field": True,
        "show_current": True,
        "show_formula": True
    }
    
    print("\n📋 LLM 输出的参数：")
    print(json.dumps(params3, ensure_ascii=False, indent=2))
    
    svg3 = template.render(params3)
    with open("em_induction_leaving.svg", "w", encoding="utf-8") as f:
        f.write(svg3)
    print("✅ 已生成: em_induction_leaving.svg")
    
    print("\n" + "=" * 60)
    print("✨ 模板扩展总结")
    print("=" * 60)
    print("✅ 复杂场景也能优雅处理")
    print("✅ 参数化控制：磁铁位置、线圈匝数、显示选项")
    print("✅ 视觉效果专业：渐变、动画、发光效果")
    print("✅ 物理准确性：电流方向符合楞次定律")
    print("✅ 教学友好：包含公式框和图例说明")
    print("=" * 60)


if __name__ == "__main__":
    demo_electromagnetic_induction()
