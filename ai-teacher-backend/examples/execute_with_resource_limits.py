"""
Python限制执行示例 - 轻量级沙箱方案

这个示例展示了如何在不使用Docker的情况下，通过Python的资源限制来安全地执行代码。

适用场景:
- 开发环境和快速原型验证
- 已信任的LLM生成的代码（通过了AST验证）
- 性能要求较高的场景

安全层级:
1. AST静态分析 - 验证代码结构
2. 资源限制 - CPU时间、内存使用
3. 超时控制 - 防止无限循环
4. 受限命名空间 - 控制可访问的模块和函数

警告: 这个方案的安全性低于Docker沙箱，不建议在生产环境中使用！
"""

import ast
import signal
import resource
import sys
import traceback
from contextlib import contextmanager
from typing import Any, Dict, Tuple, Optional


class RestrictedEnvironment:
    """受限的执行环境"""
    
    # 允许导入的模块白名单
    ALLOWED_MODULES = {
        'manim',
        'math',
        'numpy',
    }
    
    # 允许的内置函数白名单
    ALLOWED_BUILTINS = {
        'print', 'range', 'len', 'int', 'float', 'str', 'bool',
        'list', 'dict', 'tuple', 'set', 'frozenset',
        'abs', 'min', 'max', 'sum', 'round', 'pow',
        'True', 'False', 'None',
    }
    
    # 禁止的AST节点类型
    FORBIDDEN_NODES = {
        ast.Import,      # 禁止import语句
        ast.ImportFrom,  # 禁止from...import语句
        ast.Exec,        # 禁止exec
        ast.Eval,        # 禁止eval
    }


class ASTValidator(ast.NodeVisitor):
    """AST验证器"""
    
    def __init__(self, allowed_modules: set):
        self.allowed_modules = allowed_modules
        self.errors = []
    
    def visit_Import(self, node):
        """检查import语句"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name not in self.allowed_modules:
                self.errors.append(f"禁止导入模块: {module_name}")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """检查from...import语句"""
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name not in self.allowed_modules:
                self.errors.append(f"禁止导入模块: {module_name}")
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """检查函数调用"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in {'eval', 'exec', 'compile', '__import__'}:
                self.errors.append(f"禁止调用函数: {func_name}")
        self.generic_visit(node)


def validate_code(code: str, allowed_modules: set = None) -> Tuple[bool, str]:
    """
    验证代码安全性
    
    Args:
        code: 要验证的Python代码
        allowed_modules: 允许导入的模块集合
        
    Returns:
        (is_valid, error_message)
    """
    if allowed_modules is None:
        allowed_modules = RestrictedEnvironment.ALLOWED_MODULES
    
    try:
        # 解析AST
        tree = ast.parse(code)
        
        # 验证AST
        validator = ASTValidator(allowed_modules)
        validator.visit(tree)
        
        if validator.errors:
            return False, "; ".join(validator.errors)
        
        return True, ""
        
    except SyntaxError as e:
        return False, f"语法错误: {e}"


@contextmanager
def resource_limits(timeout_seconds: int = 30, memory_mb: int = 512):
    """
    资源限制上下文管理器
    
    Args:
        timeout_seconds: CPU时间限制（秒）
        memory_mb: 内存限制（MB）
    """
    # 设置CPU时间限制
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (timeout_seconds, timeout_seconds + 1)
    )
    
    # 设置内存限制
    memory_bytes = memory_mb * 1024 * 1024
    resource.setrlimit(
        resource.RLIMIT_AS,
        (memory_bytes, memory_bytes)
    )
    
    # 设置超时信号处理器
    def timeout_handler(signum, frame):
        raise TimeoutError(f"执行超时（{timeout_seconds}秒）")
    
    old_handler = signal.signal(signal.SIGXCPU, timeout_handler)
    
    try:
        yield
    finally:
        # 恢复原始信号处理器
        signal.signal(signal.SIGXCPU, old_handler)


def create_safe_namespace(allowed_modules: set = None) -> Dict[str, Any]:
    """
    创建安全的命名空间
    
    Args:
        allowed_modules: 允许的模块集合
        
    Returns:
        安全的全局命名空间字典
    """
    if allowed_modules is None:
        allowed_modules = RestrictedEnvironment.ALLOWED_MODULES
    
    # 构建受限的builtins
    safe_builtins = {
        name: __builtins__[name]
        for name in RestrictedEnvironment.ALLOWED_BUILTINS
        if name in __builtins__
    }
    
    # 构建命名空间
    namespace = {
        '__builtins__': safe_builtins,
    }
    
    # 添加允许的模块
    for module_name in allowed_modules:
        try:
            namespace[module_name] = __import__(module_name)
        except ImportError:
            pass  # 忽略无法导入的模块
    
    return namespace


def execute_with_limits(
    code: str,
    timeout_seconds: int = 30,
    memory_mb: int = 512,
    allowed_modules: set = None,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    在受限环境中执行代码
    
    Args:
        code: 要执行的Python代码
        timeout_seconds: 超时时间（秒）
        memory_mb: 内存限制（MB）
        allowed_modules: 允许的模块集合
        
    Returns:
        (success, result_dict, error_message)
    """
    # Step 1: 验证代码
    is_valid, error = validate_code(code, allowed_modules)
    if not is_valid:
        return False, None, f"代码验证失败: {error}"
    
    # Step 2: 创建安全命名空间
    namespace = create_safe_namespace(allowed_modules)
    
    # Step 3: 在资源限制下执行
    try:
        with resource_limits(timeout_seconds, memory_mb):
            exec(code, namespace)
        
        # 提取执行结果
        result = {
            'namespace': namespace,
            'success': True,
        }
        
        return True, result, ""
        
    except TimeoutError as e:
        return False, None, f"执行超时: {e}"
    
    except MemoryError:
        return False, None, "内存不足"
    
    except Exception as e:
        return False, None, f"执行错误: {e}\n{traceback.format_exc()}"


# 使用示例
if __name__ == "__main__":
    # 示例1: 安全的Manim代码
    safe_code = """
from manim import *

class AnimationScene(Scene):
    def construct(self):
        text = Text("Hello, AI Teacher!")
        self.play(Write(text))
        self.wait(2)
        
# 注意: 实际执行Manim需要完整的渲染环境
# 这里只是演示代码验证过程
print("代码验证通过")
"""
    
    print("=" * 60)
    print("测试1: 安全代码")
    print("=" * 60)
    success, result, error = execute_with_limits(safe_code)
    print(f"成功: {success}")
    if error:
        print(f"错误: {error}")
    print()
    
    # 示例2: 危险代码（尝试导入os模块）
    dangerous_code = """
import os
os.system("ls -la")
"""
    
    print("=" * 60)
    print("测试2: 危险代码（导入os）")
    print("=" * 60)
    success, result, error = execute_with_limits(dangerous_code)
    print(f"成功: {success}")
    print(f"错误: {error}")
    print()
    
    # 示例3: 危险代码（尝试使用eval）
    dangerous_code2 = """
result = eval("1 + 1")
print(result)
"""
    
    print("=" * 60)
    print("测试3: 危险代码（使用eval）")
    print("=" * 60)
    success, result, error = execute_with_limits(dangerous_code2)
    print(f"成功: {success}")
    print(f"错误: {error}")
    print()
    
    # 示例4: 内存限制测试（需要较大内存）
    memory_test_code = """
# 创建一个大列表，测试内存限制
large_list = [0] * (100 * 1024 * 1024)  # 约800MB
print("内存测试完成")
"""
    
    print("=" * 60)
    print("测试4: 内存限制（应该失败）")
    print("=" * 60)
    success, result, error = execute_with_limits(
        memory_test_code,
        memory_mb=100,  # 限制为100MB
    )
    print(f"成功: {success}")
    print(f"错误: {error}")
