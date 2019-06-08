import os
from nbh_main.settings import logger

# helper
def show_and_run(command, *, dry_run=False):
    if not dry_run:
        logger.info(f"# {command}")
        os.system(command)
    else:
        logger.info(f"(DRY-RUN) # {command}")


