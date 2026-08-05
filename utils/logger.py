import sys
from pathlib import Path

from loguru import logger


def setup_logging():
	logger.remove()

	log_path = Path("logs")
	log_path.mkdir(exist_ok=True)

	logger.add(
		sys.stdout,
		colorize=True,
		format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
		       "<level>{level: <8}</level> | "
		       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
		       "<level>{message}</level>",
		level="DEBUG"
	)

	logger.add(
		log_path / "app.log",
		rotation="10 MB",
		retention="14 days",
		compression="zip",
		format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
		level="INFO"
	)

	logger.add(
		log_path / "error.log",
		rotation="10 MB",
		retention="30 days",
		compression="zip",
		format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
		level="ERROR"
	)

	logger.info("Логирование успешно настроено.")

setup_logging()