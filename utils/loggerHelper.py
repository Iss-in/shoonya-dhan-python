#!/usr/bin/env python
import logging

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format_error = "%(levelname)s: %(asctime)s (%(filename)s :%(lineno)d) %(message)s"
    format = "%(levelname)s: %(asctime)s %(message)s"
    format = "%(levelname)s: %(message)s"

    # FORMATS = {
    #     logging.DEBUG: grey + format + reset,
    #     logging.INFO: grey + format + reset,
    #     logging.WARNING: yellow + format + reset,
    #     logging.ERROR: red + format_error + reset,
    #     logging.CRITICAL: bold_red + format_error + reset
    # }

    FORMATS = {
        logging.DEBUG: format,
        logging.INFO: format,
        logging.WARNING: format,
        logging.ERROR: format_error,
        logging.CRITICAL: format_error
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


def setup_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    log_setup.setLevel(level)

    # formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('%(filename)s: %(levelname)s: %(asctime)s %(message)s', datefmt='%H:%M:%S')

    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)

    # fileHandler.setLevel(logging.DEBUG)
    # fileHandler.setFormatter(CustomFormatter())
    # streamHandler = logging.StreamHandler()
    # streamHandler.setFormatter(formatter)
    log_setup.addHandler(fileHandler)
    # log_setup.setLevel(logging.DEBUG)

    # log_setup.addHandler(streamHandler)

    return log_setup


def logger(msg, level, logfile):
    if logfile == 'one': log = logging.getLogger('log_one')
    if logfile == 'two': log = logging.getLogger('log_two')
    if level == 'info': log.info(msg)
    if level == 'warning': log.warning(msg)
    if level == 'error': log.error(msg)


