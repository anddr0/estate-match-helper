import sys
from pathlib import Path

from loguru import logger

# Абсолютный путь к корню проекта (на уровень выше директории utils)
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"


def setup_logging() -> None:
	logger.remove()

	LOGS_DIR.mkdir(parents=True, exist_ok=True)

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
		LOGS_DIR / "app.log",
		rotation="10 MB",
		retention="14 days",
		compression="zip",
		format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
		level="INFO",
		encoding="utf-8"
	)

	logger.add(
		LOGS_DIR / "error.log",
		rotation="10 MB",
		retention="30 days",
		compression="zip",
		format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
		level="ERROR",
		encoding="utf-8"
	)

	logger.info("Логирование успешно настроено.")
