import os

from django.core.management.base import BaseCommand

from nbhosting import show_and_run

from nbh_main.settings import NBHROOT, logger

class Command(BaseCommand):

    help = """
rebuild nbhosting core images

note that pulling docker-stacks image from dockerhub is not taken care of by this command
"""
    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--dry_run", action='store_true', default=False,
            help="simply show what would be done")
        parser.add_argument(
            "name", nargs="*",
            help="typically 'scipy' or 'minimal', rebuild all if not provided")

    # typically name would be either 'scipy'
    # or any variation around it
    def build_core_image(self, name, dry_run):

        logger.info(f"{10*'='} rebuilding core image {name}")
        images_dir = NBHROOT / "images"
        # trim if needed
        name = name.replace(".Dockerfile", "")
        # search candidates
        candidates = list(images_dir.glob(f"*{name}*Dockerfile"))
        if len(candidates) != 1:
            logger.error(f"Found {len(candidates)} matches for {name} - skipped")
            return
        dockerfile = candidates[0]

        # maybe better use git ls-files *.sh ?
        scripts = [
            "common-nbhosting-prepare.sh",
            "start-in-dir-as-uid.sh",
            ]

        plain_name = str(dockerfile.name).replace(".Dockerfile", "")
        image_name = plain_name.replace("nbhosting-", "nbhosting/")


        work_dir = f"/tmp/core-{plain_name}"
        show_and_run(f"rm -rf {work_dir}; mkdir -p {work_dir}")
        show_and_run(f"cp {dockerfile} {work_dir}")
        for script in scripts:
            path = images_dir / script
            if not path.exists():
                logger.error(f"Could not spot script {script} for {name} - skipped")
                return
            show_and_run(f"cp {path} {work_dir}")
        show_and_run(f"cd {work_dir}; docker build -f {dockerfile.name} -t {image_name} .")

    def handle(self, *args, **kwargs):
        dry_run=kwargs['dry_run']
        names = kwargs['name']
        if not names:
            paths = (NBHROOT / "images").glob("nbhosting*.Dockerfile")
            names = [str(path.name) for path in paths]
            logger.info(f"{10*'='} found default names {names}")
        for name in names:
            self.build_core_image(name, dry_run)
