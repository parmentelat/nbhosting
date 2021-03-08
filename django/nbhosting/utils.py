import subprocess
from nbh_main.settings import logger

# helper
def show_and_run(command, *, dry_run=False):
    if not dry_run:
        logger.info(f"# {command}")
        completed = subprocess.run(command, shell=True)
        return completed.returncode == 0
    else:
        logger.info(f"(DRY-RUN) # {command}")
        return False