#!/usr/bin/python
#
# Copyright (c) Elliot Peele <elliot@bentlogic.net>
#

import re
import os
import sys
import errno
import shutil
import logging

log = logging.getLogger('sort_video')

class Indexer(object):
    # Broadchurch.1x08.HDTVxx264-FoV.mp4
    # Broadchurch.S01E06.PROPER.HDTV.x264-TLA.mp4
    # Castle.2009.S06E08.HDTV.x264-LOL.mp4
    # The.Colbert.Report.2014.03.31.Biz.Stone.HDTV.x264-2HD.mp4
    # How.I.Met.Your.Mother.S09E23-E24.HDTV.x264-EXCELLENCE.mp4
    FILE_RE = re.compile('(.*)([Ss](\d+)[Ee](\d+)(|-[Ee]\d+)|(\d+)x(\d+)).*')
    YEAR_RE = re.compile('(.*)\.(\d+)\.(\d+)\.(\d+)\..*')

    INDEX_PATH = '/mnt/primary/Primary/Deluge/sorted'

    def index(self, torrent_id, torrent_name, torrent_path):
        log.info('indexing %s %s %s', torrent_id, torrent_name, torrent_path)
        if os.path.isdir(torrent_path):
            self.indexdir(torrent_path)

        info = self._matchFile(os.path.basename(torrent_path))
        if not info:
            log.error('could not match %s', torrent_path)
            return
        showName, seasonNum, episodeNum = info

        showName = showName.rstrip('.')

        log.info('found %s %s %s', showName, seasonNum, episodeNum)

        showPath = os.path.join(self.INDEX_PATH, showName)
        if not os.path.exists(showPath):
            log.debug('creating path %s', showPath)
            os.mkdir(showPath)
            pass

        seasonPath = os.path.join(showPath, 'Season %s' % seasonNum)
        if not os.path.exists(seasonPath):
            log.debug('creating path %s', seasonPath)
            os.mkdir(seasonPath)
            pass

        episodePath = os.path.join(seasonPath, os.path.basename(torrent_path))

        if os.path.exists(episodePath):
            log.info('episode already indexed %s', episodePath)
            return True

        try:
            log.debug('linking %s -> %s', torrent_path, episodePath)
            os.link(torrent_path, episodePath)
        except OSError, e:
            if e.errno != errno.EXDEV:
                log.exception(e)
                raise
            log.debug('link failed, copying %s -> %s', torrent_path,
                    episodePath)
            shutil.copy(torrent_path, episodePath)

        return True

    def indexdir(self, path):
        for dirpath, dirnames, filenames in os.walk(path):
            for fn in filenames:
                self.index(None, None, os.path.join(dirpath, fn))

    def _matchFile(self, path):
        m = self.FILE_RE.match(os.path.basename(path))
        if not m:
            log.info('could not find match, trying datestamp')
            return self._matchFileByYear(path)

        groups = m.groups()
        if not ((groups[2] and groups[3]) or (groups[5] and groups[6])):
            log.warn('didn\'t find season and episode: %s', path)
            return False

        showName = groups[0]
        seasonNum, episodeNum = groups[2], groups[3]
        if not seasonNum and not episodeNum:
            seasonNum, episodeNum = groups[5], groups[6]

        return showName, seasonNum, episodeNum

    def _matchFileByYear(self, path):
        m = self.YEAR_RE.match(os.path.basename(path))
        if not m:
            log.warn('skipping %s, no match', path)
            return False

        groups = m.groups()
        showName = groups[0]
        seasonNum = groups[1]
        episodeNum = '%s%s' % (groups[2], groups[3])

        return showName, seasonNum, episodeNum


def usage(args):
    print >>sys.stderr, 'usage: %s <torrent id> <torrent name> <torrent path>' % args[0]
    return 1

def main(args):
    if len(args) != 4:
        return usage(args)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
            filename='/var/lib/deluge/video_indexer.log')
    log.setLevel(logging.DEBUG)

    torrent_id = args[1]
    torrent_name = args[2]
    torrent_path = args[3]

    indexer = Indexer()
    indexer.index(torrent_id, torrent_name, torrent_path)

    return 0

def main2(args):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
    log.setLevel(logging.DEBUG)

    if len(args) != 2:
        print >>sys.stderr, 'usage: %s <media path>' % args[0]
        return 1

    sourcePath = args[1]

    indexer = Indexer()
    indexer.indexdir(sourcePath)

    return 0 

if __name__ == '__main__':
    sys.exit(main(sys.argv))
