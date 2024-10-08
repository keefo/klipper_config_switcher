#!/bin/bash

SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"
KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_CONFIG="${HOME}/printer_data/config/moonraker.conf"
MOONRAKER_FALLBACK="${HOME}/klipper_config/moonraker.conf"
NUM_INSTALLS=0

# Force script to exit if an error occurs
set -e

# Step 1: Check for root user
verify_ready()
{
    # check for root user
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
    # output used number of installs
    if [[ $NUM_INSTALLS == 0 ]]; then
	    echo "Defaulted to one klipper install, if more than one instance, use -n"
    else
	    echo "Number of Installs Selected: $NUM_INSTALLS"
    fi
    # Fall back to old config
    if [ ! -f "$MOONRAKER_CONFIG" ]; then
        echo "${MOONRAKER_CONFIG} does not exist. Falling back to ${MOONRAKER_FALLBACK}"
        MOONRAKER_CONFIG="$MOONRAKER_FALLBACK"
    fi
}

# Step 2:  Verify Klipper has been installed
check_klipper()
{
    if [[ $NUM_INSTALLS == 0 ]]; then
        if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
            echo "Klipper service found!"
        else
            echo "Klipper service not found, please install Klipper first"
            exit -1
        fi
    else
		for (( klip = 1; klip<=$NUM_INSTALLS; klip++ )); do
			if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper-$klip.service")" ]; then
				echo "klipper-$klip.service found!"
			else
				echo "klipper-$klip.service NOT found, please ensure you've entered the correct number of klipper instances you're running!"
				exit -1
			fi			
		done	
	fi
}

# Step 3: Check folders
check_requirements()
{
    if [ ! -d "${KLIPPER_PATH}/klippy/extras/" ]; then
        echo "Error: Klipper not found in directory: ${KLIPPER_PATH}. Exiting.."
        exit -1
    fi
    echo "Klipper found at ${KLIPPER_PATH}"

    if [ ! -f "$MOONRAKER_CONFIG" ]; then
        echo "Error: Moonraker configuration not found: ${MOONRAKER_CONFIG}. Exiting.."
        exit -1
    fi
    echo "Moonraker configuration found at ${MOONRAKER_CONFIG}"
}

# Step 4: Link extension to Klipper
link_extension()
{
    echo -n "Linking extension to Klipper... "
    ln -sf "${SRCDIR}/config_switcher.py" "${KLIPPER_PATH}/klippy/extras/config_switcher.py"
    echo "[OK]"
}

# Step 5: Restarting Klipper
restart_klipper()
{
    if [[ $NUM_INSTALLS == 0 ]]; then
        echo -n "Restarting Klipper... "
        sudo systemctl restart klipper
        echo "[OK]"
    else
	    for (( klip = 1; klip<=$NUM_INSTALLS; klip++)); do
            echo -n "Restarting Klipper-$klip... "
            sudo systemctl restart klipper-$klip
            echo "[OK]"
	    done
    fi
}

uinstall()
{
    if [ -f "${KLIPPER_PATH}/klippy/extras/config_switcher.py" ]; then
        echo -n "Uninstalling config_switcher... "
        rm -f "${KLIPPER_PATH}/klippy/extras/config_switcher.py"
        rm -f "${KLIPPER_PATH}/klippy/extras/config_switcher.pyc"
        echo "[OK]"
        echo "You can now remove the \"[update_manager config_switcher]\" section in your moonraker.conf and delete this directory."
        echo "You also need to remove the \"[config_switcher]\" section in your Klipper configuration..."
    else
        echo -n "${KLIPPER_PATH}/klippy/extras/config_switcher.py not found. Is it installed? "
        echo "[FAILED]"
    fi
}

usage()
{
    echo "Usage: $(basename $0) [-k <Klipper path>] [-m <Moonraker config file>] [-n <number klipper instances>] [-u]" 1>&2;
    exit 1;
}

# Command parsing
while getopts ":k:m:n:uh" OPTION; do
    case "$OPTION" in
        k) KLIPPER_PATH="$OPTARG" ;;
        m) MOONRAKER_CONFIG="$OPTARG" ;;
        n) NUM_INSTALLS="$OPTARG" ;;
        u) UNINSTALL=1 ;;
        h | ?) usage ;;
    esac
done

# Fall back to old config
if [ ! -f "$MOONRAKER_CONFIG" ]; then
    echo "${MOONRAKER_CONFIG} does not exist. Falling back to ${MOONRAKER_FALLBACK}"
    MOONRAKER_CONFIG="$MOONRAKER_FALLBACK"
fi

# Run steps
verify_ready
check_klipper
check_requirements
if [ ! $UNINSTALL ]; then
    link_extension
else
    uinstall
fi
restart_klipper
