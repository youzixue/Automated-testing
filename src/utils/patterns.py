"""
设计模式基础接口。

定义常用设计模式的基础接口，如单例模式、工厂模式等。
这些接口可以被具体的实现类继承和实现。
"""

from typing import Dict, Type, TypeVar, Any

T = TypeVar('T')


class Singleton:
    """单例模式基类。
    
    确保一个类只有一个实例，并提供全局访问点。
    所有需要单例特性的类都应继承此类。
    
    示例:
        class MySingletonClass(Singleton):
            pass
            
        # 无论创建多少次，都是同一实例
        instance1 = MySingletonClass()
        instance2 = MySingletonClass()
        assert instance1 is instance2
    """
    
    _instances: Dict[Type, Any] = {}
    _initialized_instances: Dict[Type, bool] = {}

    def __new__(cls, *args, **kwargs):
        """创建或返回类的单例实例。
        
        Args:
            *args: 传递给原始__init__方法的位置参数
            **kwargs: 传递给原始__init__方法的关键字参数
            
        Returns:
            类的单例实例
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
    
    def __init__(self, *args, **kwargs):
        """初始化单例实例。
        
        只在第一次创建实例时执行初始化。
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        cls = self.__class__
        if cls not in cls._initialized_instances:
            # 调用实际的初始化逻辑（如果子类定义了 __init__）
            cls._initialized_instances[cls] = True
