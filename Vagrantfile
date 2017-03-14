# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
	config.vm.box = "bento/debian-8.7"
	config.vm.hostname = "neferset"
	config.vm.synced_folder ".", "/neferset"

	config.vm.provision "shell", inline: <<-SYSTEM
		apt-get update -q
		apt-get install -qy build-essential git wget curl python3 python3-pip \
		  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
		  python3-cairo python3-gi python3-gi-cairo gir1.2-pango-1.0
		pip3 install --upgrade pip setuptools
	SYSTEM

	config.vm.provision "shell", privileged: false, inline: <<-USER
		PROJECT_DIR="/neferset"

		cat <<-EOF >> "$HOME/.bashrc"
			alias python=python3
			alias pip=pip3
			cd $PROJECT_DIR
		EOF

		sudo pip install Pillow fire hearthstone
		$PROJECT_DIR/bootstrap.sh

		mkdir -p "$HOME/.config/fontconfig"
		mkdir -p "$HOME/fonts/cache"

		cat <<-EOF > "$HOME/.config/fontconfig/fonts.conf"
			<?xml version="1.0"?>
			<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
			<fontconfig>
			  <dir>$PROJECT_DIR/fonts</dir>
			  <cachedir>$HOME/fonts/cache</cachedir>
			  <config></config>
			</fontconfig>
		EOF
	USER
end
