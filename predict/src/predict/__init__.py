import loguru

# TO REMOVE if we want to see the debug logs
loguru.logger.level("INFO")


def get_logger():
    return loguru.logger
