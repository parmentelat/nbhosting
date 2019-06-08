# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import sync_disk_to_database

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command lets you create a course from a git repo

    by default, the coursename is used as the docker image name, but you can use the -i option to declare that you'd prefer to use another image instead
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
