"""
日志工具模块

功能：
- 统一的日志配置
- 文件和控制台双输出
- 支持日志轮转
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(level: str = "INFO", 
                log_file: str = None,
                log_format: str = None) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径
        log_format: 日志格式
    
    Returns:
        配置好的logger
    """
    # 获取根logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 清除已有handlers
    logger.handlers.clear()
    
    # 默认格式
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"✅ 日志系统初始化完成，级别: {level}")
    
    return logger
