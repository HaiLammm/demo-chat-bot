import logging
import os

def setup_logger():
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    handler = logging.FileHandler('logs/bot.log')
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
