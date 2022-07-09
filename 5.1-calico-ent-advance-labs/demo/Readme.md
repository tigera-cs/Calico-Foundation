# Calico-ent-lab

Download and unzip 5.1-calico-advanced-labs.zip file.

sudo chmod +x ~/labs-master/demo/setup.sh ~/labs-master/demo/jack_access.sh

sudo chmod +x ~/labs-master/demo/configs/switch_lab*

cd ~/labs-master/demo

sudo ./setup.sh

sudo cp -r ~/labs-master/demo/configs/labs ~

sudo cp ~/labs-master/demo/configs/switch_lab1.sh /usr/local/bin/lab1

sudo cp ~/labs-master/demo/configs/switch_lab2.sh /usr/local/bin/lab2

sudo cp ~/labs-master/demo/configs/switch_lab3.sh /usr/local/bin/lab3

sudo chmod +x /usr/local/bin/lab1

sudo chmod +x /usr/local/bin/lab2

sudo chmod +x /usr/local/bin/lab3


# Run the followings to set up the labs: 

./lab1 set_up

./lab2 set_up

./lab3 set_up



