#!/usr/bin/env python3
"""
增强版分层抽象可视化系统
演示如何生成精美的可视化图片
"""

import asyncio
import json
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


# ============== 第一层：增强版原子渲染层 ==============

class EnhancedAtomicRenderer:
    """
    增强版原子渲染层：支持渐变、动画、阴影等高级效果
    """
    
    SUPPORTED_ELEMENTS = {
        "circle", "ellipse", "rectangle", "line", 
        "arrow", "text", "polygon", "path", "group"
    }
    
    def render(self, composition: Dict) -> str:
        """渲染组合方案"""
        svg_parts = [
            '<svg viewBox="0 0 1000 700" xmlns="http://www.w3.org/2000/svg">',
            '<!-- Enhanced Layered Visualization System -->',
            self.render_defs(composition.get("defs", [])),
        ]
        
        # 背景渐变
        if composition.get("background"):
            svg_parts.append(self.render_background(composition["background"]))
        
        for element in composition.get("elements", []):
            svg_element = self.render_element(element)
            svg_parts.append(svg_element)
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def render_defs(self, defs: List[Dict]) -> str:
        """渲染定义区域（渐变、滤镜等）"""
        if not defs:
            return ""
        
        parts = ["<defs>"]
        for d in defs:
            if d["type"] == "linearGradient":
                parts.append(self.render_linear_gradient(d))
            elif d["type"] == "radialGradient":
                parts.append(self.render_radial_gradient(d))
            elif d["type"] == "filter":
                parts.append(self.render_filter(d))
        parts.append("</defs>")
        return "\n".join(parts)
    
    def render_linear_gradient(self, params: Dict) -> str:
        """渲染线性渐变"""
        id_ = params["id"]
        stops = params.get("stops", [])
        attrs = [f'id="{id_}"']
        if "x1" in params:
            attrs.append(f'x1="{params["x1"]}"')
        if "y1" in params:
            attrs.append(f'y1="{params["y1"]}"')
        if "x2" in params:
            attrs.append(f'x2="{params["x2"]}"')
        if "y2" in params:
            attrs.append(f'y2="{params["y2"]}"')
        
        stop_parts = []
        for s in stops:
            offset = s.get("offset", "0%")
            color = s.get("color", "#000")
            stop_parts.append(f'<stop offset="{offset}" stop-color="{color}"/>')
        
        return f'<linearGradient {" ".join(attrs)}>\n' + "\n".join(stop_parts) + '\n</linearGradient>'
    
    def render_radial_gradient(self, params: Dict) -> str:
        """渲染径向渐变"""
        id_ = params["id"]
        stops = params.get("stops", [])
        
        stop_parts = []
        for s in stops:
            offset = s.get("offset", "0%")
            color = s.get("color", "#000")
            stop_parts.append(f'<stop offset="{offset}" stop-color="{color}"/>')
        
        return f'<radialGradient id="{id_}">\n' + "\n".join(stop_parts) + '\n</radialGradient>'
    
    def render_filter(self, params: Dict) -> str:
        """渲染滤镜"""
        id_ = params["id"]
        filter_type = params.get("filter_type", "shadow")
        
        if filter_type == "shadow":
            return f'''<filter id="{id_}" x="-50%" y="-50%" width="200%" height="200%">
    <feDropShadow dx="2" dy="4" stdDeviation="3" flood-opacity="0.3"/>
  </filter>'''
        return ""
    
    def render_background(self, bg: Dict) -> str:
        """渲染背景"""
        if bg.get("gradient"):
            return f'<rect width="100%" height="100%" fill="url(#{bg["gradient"]})"/>'
        elif bg.get("color"):
            return f'<rect width="100%" height="100%" fill="{bg["color"]}"/>'
        return ""
    
    def render_element(self, element: Dict) -> str:
        """渲染单个元素"""
        element_type = element["type"]
        params = element.get("params", {})
        style = element.get("style", {})
        animation = element.get("animation", {})
        
        renderers = {
            "circle": self.render_circle,
            "ellipse": self.render_ellipse,
            "rectangle": self.render_rectangle,
            "arrow": self.render_arrow,
            "text": self.render_text,
            "path": self.render_path,
            "group": self.render_group,
        }
        
        base_svg = renderers.get(element_type, lambda p: "")(params)
        
        # 添加动画
        if animation and element_type in ["circle", "ellipse", "rectangle"]:
            base_svg = self.add_animation(base_svg, animation, element_type, params)
        
        return base_svg
    
    def render_circle(self, params: Dict) -> str:
        """渲染圆形"""
        cx = params.get("cx", 0)
        cy = params.get("cy", 0)
        r = params.get("r", 10)
        fill = params.get("fill", "#000")
        stroke = params.get("stroke", "")
        stroke_width = params.get("stroke_width", 0)
        filter_ = params.get("filter", "")
        opacity = params.get("opacity", 1)
        
        attrs = [f'cx="{cx}"', f'cy="{cy}"', f'r="{r}"']
        if fill.startswith("url("):
            attrs.append(f'fill="{fill}"')
        else:
            attrs.append(f'fill="{fill}"')
        if stroke:
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width}"')
        if filter_:
            attrs.append(f'filter="url(#{filter_})"')
        if opacity < 1:
            attrs.append(f'opacity="{opacity}"')
        
        return f'<circle {" ".join(attrs)}/>'
    
    def render_ellipse(self, params: Dict) -> str:
        """渲染椭圆"""
        cx = params.get("cx", 0)
        cy = params.get("cy", 0)
        rx = params.get("rx", 10)
        ry = params.get("ry", 10)
        fill = params.get("fill", "#000")
        stroke = params.get("stroke", "")
        filter_ = params.get("filter", "")
        
        attrs = [f'cx="{cx}"', f'cy="{cy}"', f'rx="{rx}"', f'ry="{ry}"', f'fill="{fill}"']
        if stroke:
            attrs.append(f'stroke="{stroke}"')
        if filter_:
            attrs.append(f'filter="url(#{filter_})"')
        
        return f'<ellipse {" ".join(attrs)}/>'
    
    def render_rectangle(self, params: Dict) -> str:
        """渲染矩形"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        width = params.get("width", 100)
        height = params.get("height", 100)
        fill = params.get("fill", "#000")
        rx = params.get("rx", 0)
        filter_ = params.get("filter", "")
        
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{width}"', f'height="{height}"', f'fill="{fill}"']
        if rx > 0:
            attrs.append(f'rx="{rx}"')
        if filter_:
            attrs.append(f'filter="url(#{filter_})"')
        
        return f'<rect {" ".join(attrs)}/>'
    
    def render_arrow(self, params: Dict) -> str:
        """渲染带动画的箭头"""
        x1 = params.get("x1", 0)
        y1 = params.get("y1", 0)
        x2 = params.get("x2", 0)
        y2 = params.get("y2", 0)
        stroke = params.get("stroke", "#666")
        stroke_width = params.get("stroke_width", 2)
        animated = params.get("animated", False)
        label = params.get("label", "")
        
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_length = 10
        arrow_angle = math.pi / 6
        
        x3 = x2 - arrow_length * math.cos(angle - arrow_angle)
        y3 = y2 - arrow_length * math.sin(angle - arrow_angle)
        x4 = x2 - arrow_length * math.cos(angle + arrow_angle)
        y4 = y2 - arrow_length * math.sin(angle + arrow_angle)
        
        if animated:
            return f'''<g>
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}" stroke-dasharray="5,5">
        <animate attributeName="stroke-dashoffset" from="0" to="10" dur="1s" repeatCount="indefinite"/>
    </line>
    <polygon points="{x2},{y2} {x3},{y3} {x4},{y4}" fill="{stroke}"/>
</g>'''
        else:
            return f'''<g>
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}"/>
    <polygon points="{x2},{y2} {x3},{y3} {x4},{y4}" fill="{stroke}"/>
</g>'''
    
    def render_text(self, params: Dict) -> str:
        """渲染文本"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        content = params.get("content", "")
        font_size = params.get("font_size", 16)
        fill = params.get("fill", "#000")
        text_anchor = params.get("text_anchor", "start")
        font_weight = params.get("font_weight", "normal")
        
        attrs = [f'x="{x}"', f'y="{y}"', f'font-size="{font_size}"', 
                f'fill="{fill}"', f'text-anchor="{text_anchor}"']
        if font_weight != "normal":
            attrs.append(f'font-weight="{font_weight}"')
        
        return f'<text {" ".join(attrs)}>{content}</text>'
    
    def render_path(self, params: Dict) -> str:
        """渲染路径"""
        d = params.get("d", "")
        stroke = params.get("stroke", "#000")
        stroke_width = params.get("stroke_width", 2)
        fill = params.get("fill", "none")
        animated = params.get("animated", False)
        
        attrs = [f'd="{d}"', f'stroke="{stroke}"', f'stroke-width="{stroke_width}"', f'fill="{fill}"']
        
        if animated:
            return f'<path {" ".join(attrs)} stroke-dasharray="8,4"><animate attributeName="stroke-dashoffset" from="0" to="12" dur="1.5s" repeatCount="indefinite"/></path>'
        return f'<path {" ".join(attrs)}/>'
    
    def render_group(self, params: Dict) -> str:
        """渲染分组"""
        transform = params.get("transform", "")
        elements = params.get("elements", [])
        
        parts = ["<g"]
        if transform:
            parts.append(f' transform="{transform}"')
        parts.append(">")
        
        for elem in elements:
            parts.append(self.render_element(elem))
        
        parts.append("</g>")
        return "\n".join(parts)
    
    def add_animation(self, svg: str, animation: Dict, element_type: str, params: Dict) -> str:
        """添加动画效果"""
        anim_type = animation.get("type", "pulse")
        
        if anim_type == "pulse" and element_type == "circle":
            r = params.get("r", 10)
            r_max = r * 1.2
            return svg.replace('/>', f'''>
    <animate attributeName="r" values="{r};{r_max};{r}" dur="2s" repeatCount="indefinite"/>
</circle>''')
        
        return svg


# ============== 第二层：智能组合决策层 ==============

class SmartComposer:
    """
    智能组合决策层：根据语义图自动选择最佳布局
    """
    
    def __init__(self):
        self.renderer = EnhancedAtomicRenderer()
    
    async def compose(self, semantic_graph: Dict) -> Dict:
        """生成精美的组合方案"""
        graph_type = semantic_graph.get("type", "unknown")
        
        # 根据类型选择布局策略
        if graph_type == "process":
            return self.compose_process_layout(semantic_graph)
        else:
            return self.compose_default_layout(semantic_graph)
    
    def compose_process_layout(self, semantic_graph: Dict) -> Dict:
        """流程图布局：输入-处理-输出 三层结构"""
        entities = semantic_graph.get("entities", [])
        relations = semantic_graph.get("relations", [])
        
        composition = {
            "defs": [
                # 背景渐变
                {
                    "type": "linearGradient",
                    "id": "bgGradient",
                    "x1": "0%", "y1": "0%", "x2": "100%", "y2": "100%",
                    "stops": [
                        {"offset": "0%", "color": "#667eea"},
                        {"offset": "100%", "color": "#764ba2"}
                    ]
                },
                # 太阳渐变
                {
                    "type": "radialGradient",
                    "id": "sunGradient",
                    "stops": [
                        {"offset": "0%", "color": "#ffeb3b"},
                        {"offset": "100%", "color": "#ffa000"}
                    ]
                },
                # 叶片渐变
                {
                    "type": "radialGradient",
                    "id": "leafGradient",
                    "stops": [
                        {"offset": "0%", "color": "#81c784"},
                        {"offset": "100%", "color": "#4caf50"}
                    ]
                },
                # 阴影滤镜
                {
                    "type": "filter",
                    "id": "shadow",
                    "filter_type": "shadow"
                }
            ],
            "background": {"gradient": "bgGradient"},
            "elements": []
        }
        
        # 分类实体
        inputs = []
        outputs = []
        processors = []
        
        for entity in entities:
            if entity.get("type") in ["能量源", "物质"]:
                inputs.append(entity)
            elif entity.get("type") == "产物":
                outputs.append(entity)
            elif entity.get("type") in ["器官", "细胞器"]:
                processors.append(entity)
        
        # 布局坐标
        # 输入区域（左侧上方）
        input_y_start = 150
        for i, entity in enumerate(inputs):
            x = 120
            y = input_y_start + i * 100
            self.add_entity_element(composition, entity, x, y, "input")
        
        # 处理区域（中心）
        if processors:
            processor = processors[0]
            x, y = 500, 350
            self.add_processor_element(composition, processor, x, y)
        
        # 输出区域（右侧下方）
        output_y_start = 150
        for i, entity in enumerate(outputs):
            x = 880
            y = output_y_start + i * 120
            self.add_entity_element(composition, entity, x, y, "output")
        
        # 添加连接箭头
        self.add_connection_arrows(composition, inputs, processors, outputs)
        
        # 添加标题
        composition["elements"].insert(0, {
            "type": "text",
            "params": {
                "x": 500, "y": 50,
                "content": semantic_graph.get("title", "流程图"),
                "font_size": 28,
                "fill": "#ffffff",
                "text_anchor": "middle",
                "font_weight": "bold"
            }
        })
        
        # 添加化学方程式
        if semantic_graph.get("equation"):
            composition["elements"].append({
                "type": "rectangle",
                "params": {
                    "x": 250, "y": 620,
                    "width": 500, "height": 50,
                    "fill": "#f5f5f5",
                    "rx": 10
                }
            })
            composition["elements"].append({
                "type": "text",
                "params": {
                    "x": 500, "y": 652,
                    "content": semantic_graph["equation"],
                    "font_size": 18,
                    "fill": "#333",
                    "text_anchor": "middle",
                    "font_weight": "bold"
                }
            })
        
        return composition
    
    def add_entity_element(self, composition: Dict, entity: Dict, x: float, y: float, category: str):
        """添加实体元素"""
        importance = entity.get("importance", 3)
        radius = 35 + importance * 5
        
        # 选择颜色和渐变
        fill = self.get_fill_for_entity(entity, category)
        
        # 添加圆形
        composition["elements"].append({
            "type": "circle",
            "params": {
                "cx": x, "cy": y, "r": radius,
                "fill": fill,
                "filter": "shadow"
            },
            "animation": {"type": "pulse"} if category == "input" else {}
        })
        
        # 添加文本
        composition["elements"].append({
            "type": "text",
            "params": {
                "x": x,
                "y": y + 5,
                "content": entity["name"],
                "font_size": 16,
                "fill": "#ffffff" if category != "input" or entity["name"] in ["太阳"] else "#333",
                "text_anchor": "middle",
                "font_weight": "bold"
            }
        })
        
        # 添加说明
        if entity.get("attributes"):
            label = "、".join(entity["attributes"][:2])
            composition["elements"].append({
                "type": "text",
                "params": {
                    "x": x,
                    "y": y + radius + 20,
                    "content": label,
                    "font_size": 11,
                    "fill": "#666",
                    "text_anchor": "middle"
                }
            })
    
    def add_processor_element(self, composition: Dict, entity: Dict, x: float, y: float):
        """添加处理元素（核心）"""
        # 添加大型椭圆
        composition["elements"].append({
            "type": "ellipse",
            "params": {
                "cx": x, "cy": y,
                "rx": 140, "ry": 100,
                "fill": "url(#leafGradient)",
                "stroke": "#2e7d32",
                "filter": "shadow"
            }
        })
        
        # 添加文本
        composition["elements"].append({
            "type": "text",
            "params": {
                "x": x,
                "y": y - 10,
                "content": "🍃",
                "font_size": 40,
                "fill": "#ffffff",
                "text_anchor": "middle"
            }
        })
        
        composition["elements"].append({
            "type": "text",
            "params": {
                "x": x,
                "y": y + 30,
                "content": entity["name"],
                "font_size": 22,
                "fill": "#ffffff",
                "text_anchor": "middle",
                "font_weight": "bold"
            }
        })
        
        # 添加说明
        if entity.get("attributes"):
            label = " | ".join(entity["attributes"])
            composition["elements"].append({
                "type": "text",
                "params": {
                    "x": x,
                    "y": y + 60,
                    "content": label,
                    "font_size": 12,
                    "fill": "#e8f5e9",
                    "text_anchor": "middle"
                }
            })
    
    def add_connection_arrows(self, composition: Dict, inputs: List, processors: List, outputs: List):
        """添加连接箭头"""
        if not processors:
            return
        
        proc_x, proc_y = 500, 350
        
        # 输入 → 处理
        for i, entity in enumerate(inputs):
            start_x = 120
            start_y = 150 + i * 100
            end_x = proc_x - 140
            end_y = proc_y
            
            # 使用曲线
            composition["elements"].append({
                "type": "path",
                "params": {
                    "d": f"M {start_x + 45} {start_y} Q {(start_x + end_x) / 2} {start_y} {end_x} {end_y}",
                    "stroke": self.get_arrow_color(entity),
                    "stroke_width": 3,
                    "animated": True
                }
            })
        
        # 处理 → 输出
        for i, entity in enumerate(outputs):
            start_x = proc_x + 140
            start_y = proc_y
            end_x = 880
            end_y = 150 + i * 120
            
            composition["elements"].append({
                "type": "path",
                "params": {
                    "d": f"M {start_x} {start_y} Q {(start_x + end_x) / 2} {end_y} {end_x - 45} {end_y}",
                    "stroke": self.get_arrow_color(entity),
                    "stroke_width": 3,
                    "animated": True
                }
            })
    
    def get_fill_for_entity(self, entity: Dict, category: str) -> str:
        """获取实体填充颜色"""
        name = entity.get("name", "")
        
        if name == "太阳":
            return "url(#sunGradient)"
        elif name == "叶片":
            return "url(#leafGradient)"
        elif category == "output":
            return "#4caf50" if "O₂" in name else "#e91e63"
        elif category == "input":
            return "#2196f3" if "H₂O" in name else "#9e9e9e"
        
        return "#2196f3"
    
    def get_arrow_color(self, entity: Dict) -> str:
        """获取箭头颜色"""
        name = entity.get("name", "")
        if "太阳" in name:
            return "#ff9800"
        elif "O₂" in name:
            return "#4caf50"
        elif "葡萄糖" in name:
            return "#e91e63"
        return "#666"
    
    def compose_default_layout(self, semantic_graph: Dict) -> Dict:
        """默认布局"""
        return {
            "defs": [],
            "elements": [
                {
                    "type": "text",
                    "params": {
                        "x": 500, "y": 300,
                        "content": "暂不支持此类型的可视化",
                        "font_size": 20,
                        "fill": "#666",
                        "text_anchor": "middle"
                    }
                }
            ]
        }


# ============== 第三层：语义理解层（增强版）==============

class EnhancedSemanticAnalyzer:
    """
    增强版语义理解层
    """
    
    async def analyze(self, natural_language: str) -> Dict:
        """分析自然语言"""
        if "光合作用" in natural_language:
            return {
                "type": "process",
                "title": "🌿 光合作用过程",
                "entities": [
                    {"name": "太阳", "type": "能量源", "attributes": ["光能"], "importance": 5},
                    {"name": "CO₂", "type": "物质", "attributes": ["碳源"], "importance": 4},
                    {"name": "H₂O", "type": "物质", "attributes": ["氢源", "氧源"], "importance": 4},
                    {"name": "叶片", "type": "器官", "attributes": ["叶绿体", "气孔"], "importance": 5},
                    {"name": "O₂", "type": "产物", "attributes": ["氧气"], "importance": 3},
                    {"name": "葡萄糖", "type": "产物", "attributes": ["有机物"], "importance": 5}
                ],
                "relations": [
                    {"from": "太阳", "to": "叶片", "label": "光能"},
                    {"from": "CO₂", "to": "叶片", "label": "通过气孔"},
                    {"from": "H₂O", "to": "叶片", "label": "根部吸收"},
                    {"from": "叶片", "to": "O₂", "label": "释放"},
                    {"from": "叶片", "to": "葡萄糖", "label": "生成"}
                ],
                "equation": "6CO₂ + 6H₂O + 光能 → C₆H₁₂O₆ + 6O₂"
            }
        else:
            return {"type": "unknown"}


# ============== 完整系统 ==============

class EnhancedLayeredSystem:
    """增强版分层可视化系统"""
    
    def __init__(self):
        self.analyzer = EnhancedSemanticAnalyzer()
        self.composer = SmartComposer()
        self.renderer = EnhancedAtomicRenderer()
    
    async def visualize(self, text: str) -> str:
        """完整流程"""
        print("🚀 开始生成精美可视化...")
        
        # 第一层：语义理解
        print("  📖 语义分析中...")
        semantic_graph = await self.analyzer.analyze(text)
        
        # 第二层：智能组合
        print("  🎨 组合设计中...")
        composition = await self.composer.compose(semantic_graph)
        
        # 第三层：原子渲染
        print("  ✨ 渲染输出中...")
        svg = self.renderer.render(composition)
        
        print("✅ 完成！")
        return svg


async def main():
    system = EnhancedLayeredSystem()
    svg = await system.visualize("请展示光合作用的过程")
    
    output_path = "/Users/zhaoyang/iFlow/aiteacher-2/enhanced_output.svg"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    
    print(f"\n📄 已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
