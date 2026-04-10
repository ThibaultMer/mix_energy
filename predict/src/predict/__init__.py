import loguru
import sys

# TO REMOVE if we want to see the debug logs
loguru.logger.level("INFO")


_LOGGER_CONFIGURED = False


def get_logger():
    global _LOGGER_CONFIGURED

    if not _LOGGER_CONFIGURED:
        # Send low-severity logs to stdout and real errors to stderr for Airflow UI.
        loguru.logger.remove()
        loguru.logger.add(
            sys.stdout,
            level="INFO",
            filter=lambda record: record["level"].no < 40,
        )
        loguru.logger.add(
            sys.stderr,
            level="ERROR",
            filter=lambda record: record["level"].no >= 40,
        )
        _LOGGER_CONFIGURED = True

    return loguru.logger
