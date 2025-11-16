# update_vectorstore.py
from rag.vectorstore import update_vectorstore
from utils.logger import setup_logger
import sys

if __name__ == "__main__":
    logger = setup_logger()
    try:
        logger.info("Bắt đầu cập nhật vector store...")
        update_vectorstore()
        logger.info("Cập nhật vector store thành công!")
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật vector store: {str(e)}")
        sys.exit(1)
