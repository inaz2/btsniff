# btsniff

just a BitTorrent DHT Sniffer (based on python-libtorrent)

* http://www.slideshare.net/inaz2/20131006r02-sniffing-bittorrentdht


## Install prerequisites on Ubuntu

```
$ sudo apt-get install python-libtorrent
```

## Usage

First, prepare a torrent for joining the network.

```
$ wget http://releases.ubuntu.com/12.04/ubuntu-12.04.3-server-amd64.iso.torrent
```

Then, execute below. btsniff listens on tcp port 6881.

```
$ python btsniff.py ubuntu-12.04.3-server-amd64.iso.torrent
```

or

```
$ nohup python btsniff.py ubuntu-12.04.3-server-amd64.iso.torrent >/dev/null 2>&1 &
```
