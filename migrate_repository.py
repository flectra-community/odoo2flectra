# !/usr/bin/env python3
import argparse
import time

from migrator.migrator import *

if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser(description='Migrate Odoo repositories to Flectra')
    parser.add_argument('--name', help='Name of Repository')
    parser.add_argument('--company', default='Jamotion GmbH', help='Name of Repository')
    parser.add_argument('--contributor', default='Jamotion <info@jamotion.ch>', help='Name of Repository')
    parser.add_argument('--src', default='./odoo', help='Path to odoo repository')
    parser.add_argument('--dest', default='./flectra', help='Path to flectra repository')
    parser.add_argument('--debug', default=False, action='store_true', help='Loglevel: DEBUG')

    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    logging.basicConfig(
            level=log_level,
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S'
    )
    _logger = logging.getLogger(__name__)
    _logger.info('Starting module migration')

    if not os.path.exists(args.src):
        _logger.error('Source folder %s not found!', args.src)
        exit(1)

    if not os.path.exists(args.dest):
        _logger.debug('Creating destination folder %s', args.dest)
        os.mkdir(args.dest)

    repo_src_path = os.path.abspath(args.src)
    repo_dst_path = os.path.abspath(args.dest)
    migrator = RepoMigrator(args.name, repo_src_path, repo_dst_path, args.company, args.contributor)
    migrator.migrate()
    migrator.generate_gitlab_ci()

    _logger.info('Module migration finished')
    _logger.info('Migration took {0} second'.format(time.time() - start_time))
