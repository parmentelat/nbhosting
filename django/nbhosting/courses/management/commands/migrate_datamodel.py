# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import sync_disk_to_database

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command is designed as a one-shot migration tool for courses, 
    from the pre-0.15 file-based format to the db-backed new format

    it will deal with all course known to nbhosting, and will populate the db
    from the contents of files. 

    the command won't delete any file, but show a list of the ones 
    that could be cleaned up later on.
    """

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        sync_disk_to_database(migrate_extras=True)
        logger.info("for now the old config files are still present")
        logger.info("you can clean them all manualy with")
        logger.info(f"ls {NBHROOT}/courses/*/.{{autopull,giturl,image,staff}}")
        logger.info(f"rm {NBHROOT}/courses/*/.{{autopull,giturl,image,staff}}")
        return 0
