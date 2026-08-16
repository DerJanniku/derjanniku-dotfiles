#!/usr/bin/env bash
# Cycles between relevant audio sinks and moves all active streams to the new default.

SINKS=(
    "alsa_output.usb-Logitech_PRO_X_Wireless_Gaming_Headset-00.analog-stereo"
    "alsa_output.pci-0000_0d_00.1.hdmi-stereo"
    "alsa_output.pci-0000_0f_00.4.pro-output-0"
)

SINK_LABELS=(
    "PRO X Headset"
    "M27Q2 (HDMI)"
    "ALC897 Analog"
)

current=$(pactl get-default-sink)

current_index=-1
for i in "${!SINKS[@]}"; do
    if [[ "${SINKS[$i]}" == "$current" ]]; then
        current_index=$i
        break
    fi
done

next_index=$(( (current_index + 1) % ${#SINKS[@]} ))
next_sink="${SINKS[$next_index]}"
next_label="${SINK_LABELS[$next_index]}"

pactl set-default-sink "$next_sink"

# Move all active sink inputs to the new default
pactl list sink-inputs short | awk '{print $1}' | while read -r input_id; do
    pactl move-sink-input "$input_id" "$next_sink"
done

notify-send -t 2500 -i audio-card "Audio Output" "$next_label" -h string:x-canonical-private-synchronous:audio-switch
