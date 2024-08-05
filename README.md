<p align="center">
  <a>
    <img src="https://raw.githubusercontent.com/keefo/klipper_config_switcher/main/screenshot.jpg" alt="Klipper Config Switcher" height="220">
    <h1 align="center">Klipper Config Switcher</h1>
  </a>
</p>

## Overview

The `klipper_config_switcher` is a custom Klipper plugin that allows users to switch between different printer configurations easily. This plugin is useful for those who need to switch between different setup configurations, such as day and night profiles, with a simple G-code command.

## Features
- Switch between day and night configuration files.
- Validate the configuration switch using MD5 checksum.
- Restart the Klipper firmware after a successful configuration switch.
- Check the current configuration file in use.

## Installation

### Prerequisites

- Klipper firmware installed and running on your 3D printer.
- Access to the Raspberry Pi or other control hardware running Klipper.

### Steps to Install

1. **Clone the Repository:**

```bash
cd ~/
git clone https://github.com/keefo/klipper_config_switcher.git
```

1. **Run install.sh**

```bash
cd ~/klipper_config_switcher
./install.sh
```

2. Add the Plugin config section to printer.cfg:

Open your printer.cfg file and add the following section:

```
[config_switcher]
day_config: ~/printer_data/config/printer_day.cfg
night_config: ~/printer_data/config/printer_night.cfg
```

You need to have these 2 files in your ~/printer_data/config folder.

3. Add update manager in moonraker

If you are using moonraker, you can add this section to moonraker.conf file

```
[update_manager klipper_config_switcher]
type: git_repo
path: ~/klipper_config_switcher
origin: https://github.com/keefo/klipper_config_switcher.git
managed_services: klipper
primary_branch: main
```

## Usage

To switch between configurations, use the SWITCH_CONFIG G-code command:

```
SWITCH_CONFIG CONFIG=day
```

```
SWITCH_CONFIG CONFIG=night
```

Check current config

```
CHECK_CONFIG
```

With mainsail you should be able to turn them into buttons and add to your dashboard.
