os:
  wget https://downloads.raspberrypi.org/raspbian_latest # https://www.raspberrypi.org/downloads/raspbian/
  dd bs=4M if=*.img of=/dev/mmcblk0 #https://www.raspberrypi.org/documentation/installation/installing-images/linux.md

  Username: pi
  Password: raspberry

  upgrade:
    sudo apt-get update -y
    sudo apt-get upgrade -y

    sudo apt-get install vim git

    /sbin/fdisk -lu 2016-05-27-raspbian-jessie.img
    sudo losetup -o 70254592  /dev/loop0 2016-05-27-raspbian-jessie.img #137216*512
    sudo mount /dev/loop0 img

    sudo umount img
    sudo losetup -d /dev/loop0

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
  ./mjpg_streamer -i "./input_uvc.so -n -f 30 -r 640x360" -o "./output_http.so -p 10088 -w /usr/local/www"
  http://192.168.1.71:10088/?action=stream

tools:
  fritzing
  intel xdk
