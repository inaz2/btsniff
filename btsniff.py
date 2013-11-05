#!/usr/bin/env python

import os
import sys
import time
import libtorrent as lt
from base64 import b32encode

lt.alert.category_t.dht_notification = 0x400    # monkey patching


class Btsniff:
    def __init__(self):
        self.ses = None
        self.serial = 0L
        self.info_hashes = {}

    def start(self, torrent_file, port=6881):
        if not os.path.isdir('log'):
            os.mkdir('log')

        self.ses = lt.session()
        self.ses.set_alert_mask(lt.alert.category_t.status_notification | lt.alert.category_t.dht_notification)

        self.ses.listen_on(port, port)
        self.ses.start_dht()
        self.ses.add_dht_router("router.bittorrent.com", 6881)
        self.ses.add_dht_router("router.utorrent.com", 6881)
        self.ses.add_dht_router("router.bitcomet.com", 6881)

        info = lt.torrent_info(torrent_file)
        h = self.ses.add_torrent({'ti': info, 'save_path': './'})

        while not h.is_seed():
            alert = self.ses.pop_alert()
            while alert is not None:
                self.handle_alert(alert)
                alert = self.ses.pop_alert()
            time.sleep(0.1)

        self.ses.remove_torrent(h)

        while True:
            alert = self.ses.pop_alert()
            while alert is not None:
                self.handle_alert(alert)
                alert = self.ses.pop_alert()
            time.sleep(0.1)

    def handle_alert(self, alert):
        alert_type = type(alert).__name__
        print "[%s] %s" % (alert_type, alert.message())

        if alert_type == 'dht_get_peers_alert':
            try:
                info_hash = str(alert.info_hash)
            except:
                return

            self.serial += 1
            if not info_hash in self.info_hashes:
                self.info_hashes[info_hash] = {'serial': self.serial, 'unixtime': time.time()}
            else:
                return

            h = self.ses.add_torrent({'info_hash': alert.info_hash, 'save_path': './'})
            h.queue_position_top()
        elif alert_type == 'metadata_received_alert':
            h = alert.handle
            info_hash = str(h.info_hash())
            if h.is_valid():
                ti = h.get_torrent_info()
                serial = self.info_hashes[info_hash]['serial']
                unixtime = self.info_hashes[info_hash]['unixtime']
                line = '\t'.join([
                        str(serial),
                        time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(unixtime)), 
                        info_hash, 
                        str(ti.total_size()), 
                        str(ti.num_files()), 
                        ti.name(), 
                        ti.comment(), 
                        ti.creator(), 
                ])
                fpath = time.strftime('log/btsniff-%Y%m%d.log', time.localtime(unixtime))
                with open(fpath, 'a') as f:
                    print >>f, line
                    f.flush()
                self.ses.remove_torrent(h, 1) # session::delete_files


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: python %s TORRENT_FILE" % sys.argv[0]
        sys.exit(1)
    torrent_file = sys.argv[1]

    btsniff = Btsniff()
    btsniff.start(torrent_file)
