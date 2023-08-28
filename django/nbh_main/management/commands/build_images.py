from pathlib import Path

from django.core.management.base import BaseCommand

from nbhosting.utils import show_and_run

from nbh_main.settings import NBHROOT, logger

class Command(BaseCommand):

    help = """
rebuild nbhosting core images

"""
    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--dry-run", action='store_true', default=False,
            help="simply show what would be done")
        parser.add_argument(
            "-f", "--force", action='store_true', default=False,
            help="rebuild image unconditionnally")
        parser.add_argument(
            "-t", "--tag", default="latest",
            help="tag to use, typically 'latest' or 'nb6' - default is 'latest'"
        )
        parser.add_argument(
            "name", nargs="*",
            help="typically 'scipy' or 'minimal', rebuild all if not provided")

    # typically name would be either 'scipy'
    # or any variation around it
    def build_core_image(self, name, tag, dry_run, force):

        logger.info(f"{10*'='} rebuilding core image {name} for tag {tag}")
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
            "nbhosting-image-root.sh",
            "nbhosting-image-jovyan.sh",
            "start-in-dir-as-uid.sh",
        ]

        plain_name = str(dockerfile.name).replace(".Dockerfile", "")
        image_name = plain_name.replace("nbhosting-", "nbhosting/")


        work_dir = Path(f"/tmp/core-image-{plain_name}-{tag}")
        patched_dockerfile = work_dir / dockerfile.name
        show_and_run(f"rm -rf {work_dir}; mkdir -p {work_dir}", dry_run=dry_run)
        show_and_run(f"sed -e s/@TAG@/{tag}/ {dockerfile} > {patched_dockerfile}", dry_run=dry_run)
        for script in scripts:
            path = images_dir / script
            if not path.exists():
                logger.error(f"Could not spot script {script} for {name} - skipped")
                return
            show_and_run(f"cp {path} {work_dir}", dry_run=dry_run)
        force_tag = "" if not force else "--no-cache"
        build_command = f"cd {work_dir}; "
        build_command += f"podman build {force_tag}"
        build_command += f" -f {dockerfile.name} -t {image_name}:{tag} ."
        show_and_run(build_command, dry_run=dry_run)

    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']
        force = kwargs['force']
        tag = kwargs['tag']
        names = kwargs['name']
        if not names:
            paths = (NBHROOT / "images").glob("nbhosting*.Dockerfile")
            names = [str(path.name) for path in paths]
            logger.info(f"{10*'='} found default names {names}")
        for name in names:
            self.build_core_image(name, tag, dry_run, force)
