#!/usr/bin/env python

import sys
import time
import chardet
import libtorrent as lt

def decode_string(s, encoding="utf8"):
    """
    Decodes a string and re-encodes it in utf8.  If it cannot decode using
    `:param:encoding` then it will try to detect the string encoding and
    decode it.

    :param s: string to decode
    :type s: string
    :keyword encoding: the encoding to use in the decoding
    :type encoding: string

    """
    try:
        s = s.decode(encoding).encode("utf8", "ignore")
    except UnicodeDecodeError:
        s = s.decode(chardet.detect(s)["encoding"], "ignore").encode("utf8", "ignore")
    return s

def utf8_encoded(s):
    """
    Returns a utf8 encoded string of s

    :param s: (unicode) string to (re-)encode
    :type s: basestring
    :returns: a utf8 encoded string of s
    :rtype: str

    """
    if isinstance(s, str):
        s = decode_string(s)
    elif isinstance(s, unicode):
        s = s.encode("utf8", "ignore")
    return s

def create_magnet_uri(infohash, name=None, trackers=[]):
    """
    Creates a magnet uri

    :param infohash: the info-hash of the torrent
    :type infohash: string
    :param name: the name of the torrent (optional)
    :type name: string
    :param trackers: the trackers to announce to (optional)
    :type trackers: list of strings

    :returns: a magnet uri string
    :rtype: string

    """
    from base64 import b32encode
    uri = "magnet:?xt=urn:btih:" + b32encode(infohash.decode("hex"))
    if name:
        uri = uri + "&dn=" + name
    if trackers:
        for t in trackers:
            uri = uri + "&tr=" + t
    return uri

def fsize(fsize_b):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f %s" % (fsize_kb, "KiB")
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f %s" % (fsize_mb, "MiB")
    fsize_gb = fsize_mb / 1024.0
    return "%.1f %s" % (fsize_gb, "GiB")


info_hashes = {}

def handle_alert(ses, alert):
    alert_type = type(alert).__name__
    if alert_type == 'dht_get_peers_alert':
        try:
            info_hash = str(alert.info_hash)
        except:
            return

        print >>sys.stderr, "received get_peers: %s" % info_hash
        if not info_hash in info_hashes:
            info_hashes[info_hash] = time.time()
        else:
            return

        trackers = [
            "udp://tracker.openbittorrent.com:80",
            "udp://tracker.publicbt.com:80",
            "udp://tracker.istole.it:6969",
            "udp://tracker.ccc.de:80",
            "udp://open.demonii.com:1337",
        ]
        uri = create_magnet_uri(infohash=info_hash, trackers=trackers)
        h = lt.add_magnet_uri(ses, utf8_encoded(uri), { 'save_path': './' })
        h.queue_position_top()
    elif alert_type == 'metadata_received_alert':
        h = alert.handle
        info_hash = str(h.info_hash())
        if h.is_valid():
            ti = h.get_torrent_info()
            seconds = info_hashes[info_hash]
            print '\t'.join([
                    time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(seconds)), 
                    info_hash, 
                    fsize(ti.total_size()), 
                    "%d files" % ti.num_files(), 
                    ti.name(), 
                    ti.comment(), 
                    ti.creator(), 
            ])
            sys.stdout.flush()
            ses.remove_torrent(h, 1) # session::delete_files


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: python %s TORRENT_FILE" % sys.argv[0]
        sys.exit(1)
    torrent_file = sys.argv[1]

    ses = lt.session()
    ses.set_alert_mask(lt.alert.category_t.status_notification | 0x400) # lt.alert.category_t.dht_notification

    ses.listen_on(6881, 6881)
    ses.start_dht()
    ses.add_dht_router("router.bittorrent.com", 6881)
    ses.add_dht_router("router.utorrent.com", 6881)
    ses.add_dht_router("router.bitcomet.com", 6881)

    info = lt.torrent_info(torrent_file)
    h = ses.add_torrent({'ti': info, 'save_path': './'})
    print >>sys.stderr, "starting: %s" % h.name()

    while not h.is_seed():
        alert = ses.pop_alert()
        while alert is not None:
            handle_alert(ses, alert)
            alert = ses.pop_alert()
        time.sleep(0.1)

    print >>sys.stderr, "completed: %s" % h.name()
    ses.remove_torrent(h)

    while True:
        alert = ses.pop_alert()
        while alert is not None:
            handle_alert(ses, alert)
            alert = ses.pop_alert()
        time.sleep(0.1)
