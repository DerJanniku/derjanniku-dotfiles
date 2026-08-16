#!/usr/bin/env bash
# Lightweight Cava visualizer stream for Waybar (Multi-Monitor safe)

bar=" ▂▃▄▅▆▇█"
dict="s/;//g"
bar_len=${#bar}

for ((i=0; i<bar_len; i++)); do
    dict="$dict;s/$i/${bar:$i:1}/g"
done

config_file="/tmp/waybar_cava_config_$$"
cat > "$config_file" << 'CONFIG'
[general]
bars = 8
sleep_timer = 2
[input]
method = pulse
source = auto
[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7
CONFIG

trap "rm -f $config_file" EXIT
cava -p "$config_file" 2>/dev/null | sed -u "$dict"
