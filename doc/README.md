os:
  wget https://downloads.raspberrypi.org/raspbian_latest # https://www.raspberrypi.org/downloads/raspbian/
  sudo dd bs=4M if=*.img of=/dev/mmcblk0 #https://www.raspberrypi.org/documentation/installation/installing-images/linux.md

  Username: pi
  Password: raspberry

  upgrade:
    sudo apt-get update -y
    sudo apt-get upgrade -y

    sudo apt-get install vim git

    /sbin/fdisk -lu 2016-05-27-raspbian-jessie.img
    sudo losetup -o 70254592 /dev/loop0 2016-05-27-raspbian-jessie.img #137216*512
    sudo mount /dev/loop0 img

    sudo umount img
    sudo losetup -d /dev/loop0

  backup:
    sudo dd bs=4M if=/dev/mmcblk0 | gzip > rasbian.img.gz
    gunzip --stdout rasbian.img.gz | sudo dd bs=4M of=/dev/mmcblk0

qemu: (http://embedonix.com/articles/linux/emulating-raspberry-pi-on-linux/)
  git clone https://github.com/dhruvvyas90/qemu-rpi-kernel.git
  qemu-system-arm -kernel qemu-rpi-kernel/kernel-qemu-4.4.12-jessie -cpu arm1176 -m 256 -M versatilepb -no-reboot -serial stdio -append "root=/dev/sda2 panic=1 rootfstype=ext4 rw" -hda 2016-05-27-raspbian-jessie.img

  /etc/ld.so.preload -> comment out the line inside

  /etc/udev/rules.d/90-qemu.rules
    KERNEL=="sda", SYMLINK+="mmcblk0"
    KERNEL=="sda?", SYMLINK+="mmcblk0p%n"
    KERNEL=="sda2", SYMLINK+="root"

run on startup: (https://www.raspberrypi.org/documentation/linux/usage/rc-local.md)
  /etc/rc.local
    * python /full/path/script.py &

  /etc/modules
    * add module on startup

wifi:
  mount /dev/mmcblk0 pi && cd pi
  sudo vim /etc/wpa_supplicant/wpa_supplicant.conf
  network={
      ssid="PlusNetWirelessDDBF02"
      psk="..."
  }
  sudo raspi-config # hostname

camera:
  sudo raspi-config # enable camera
  git clone https://github.com/SaintGimp/mjpg-streamer
  cd mjpg-streamer/mjpg-streamer
  sudo apt-get install libjpeg8-dev imagemagick libv4l-dev
  sudo ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h
  sudo make USE_LIBV4L2=true clean all
  sudo make install

  raspistill -o image.jpg

  sudo modprobe bcm2835-v4l2
  ./mjpg_streamer -i "./input_uvc.so -n -f 15 -r 640x360" -o "./output_http.so -p 10088 -w /usr/local/www"
  http://192.168.1.71:10088/?action=stream

  speed up:
    tmp storage (https://www.raspberrypi.org/forums/viewtopic.php?t=45178)
      /etc/default/tmpfs: RAMTMP=yes #mjpg_streamer -i 'input_file.so -f /tmp/mjpg -r'


tools:
  fritzing
  intel xdk
