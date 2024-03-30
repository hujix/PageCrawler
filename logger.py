import logging
import os
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def setup_custom_logger(name: str, max_bytes=1000000, backup_count=5):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)

    # 创建一个处理器，比如输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    os.makedirs('./logs', exist_ok=True)

    # 创建一个 RotatingFileHandler 处理器
    file_handler = RotatingFileHandler(f'./logs/extract.log', maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log


logger = setup_custom_logger("PageExtractor")
