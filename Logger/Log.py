import logging
import pathlib


parent_path = pathlib.Path(__file__).parent.parent


class Log():
    def __init__(self) -> None:
        error_formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        info_formatter = logging.Formatter(
            fmt="%(asctime)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        error_handler = logging.FileHandler(parent_path / "log/error.log")
        info_handler = logging.FileHandler(parent_path / "log/info.log")

        error_handler.setFormatter(error_formatter)
        info_handler.setFormatter(info_formatter)

        self.error_logger = logging.getLogger('WarningsAndAbove')
        self.info_logger = logging.getLogger('Info')

        self.error_logger.setLevel(logging.WARNING)
        self.info_logger.setLevel(logging.INFO)

        self.error_logger.addHandler(error_handler)
        self.info_logger.addHandler(info_handler)

    def error(self, msg: str) -> None:
        self.error_logger.error(msg)

    def warning(self, msg: str) -> None:
        self.error_logger.warning(msg)

    def critical(self, msg: str) -> None:
        self.error_logger.critical(msg)

    def info(self, msg: str) -> None:
        self.info_logger.info(msg)


if __name__ == '__main__':
    logger = Log()
    logger.error('Test error')
    logger.warning('Test warning')
    logger.critical('Test critical')
    logger.info('Test info')
