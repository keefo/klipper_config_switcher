import logging
import os
import shutil
import hashlib
import asyncio
import time

class ConfigSwitcher:
    def __init__(self, config):
        logging.info("switcher  ConfigSwitcher initialized")
        
        self.save_config_marker = "#*# <---------------------- SAVE_CONFIG ---------------------->"
        
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('SWITCH_CONFIG', self.cmd_SWITCH_CONFIG)
        self.gcode.register_command('CHECK_CONFIG', self.cmd_CHECK_CONFIG)

        # Load configuration values
        self.day_config = os.path.expanduser(config.get('day_config'))
        self.night_config = os.path.expanduser(config.get('night_config'))
        logging.info(f"Day config: {self.day_config}")
        logging.info(f"Night config: {self.night_config}")
        
        # sync SAVE_CONFIG section to other configs
        save_part = self.extract_config_content(os.path.expanduser('~/printer_data/config/printer.cfg'))
        self.replace_config_content(self.day_config, save_part)
        self.replace_config_content(self.night_config, save_part)
        
        
    def replace_config_content(self, file_path, new_content):
        lines = []
        save_config_found = False
        with open(file_path, 'r') as file:
            for line in file:
                if self.save_config_marker in line:
                    save_config_found = True
                    lines.append(line)
                    break
                lines.append(line)
        
        if save_config_found:
            lines.append(new_content)
            with open(file_path, 'w') as file:
                file.writelines(lines)
        else:
            raise ValueError("SAVE_CONFIG section not found in the file.")


    def extract_config_content(self, file_path):
        config_content = []
        save_config_found = False

        with open(file_path, 'r') as file:
            for line in file:
                if self.save_config_marker in line:
                    save_config_found = True
                    continue  # Skip the marker line
                if save_config_found:
                    config_content.append(line)

        return ''.join(config_content)

    def calculate_md5(self, file_path):
        """Calculate MD5 checksum of the given file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def cmd_SWITCH_CONFIG(self, gcmd):
        print_stats = self.printer.lookup_object('print_stats')
        eventtime = self.printer.get_reactor().monotonic()
        state = print_stats.get_status(eventtime)['state']
        if state not in ['standby', 'idle', 'idle_state', 'complete', 'cancelled']:
            gcmd.respond_info(f"Cannot switch config while printer is {state} state.")
            logging.info(f"Cannot switch config while printer is {state} state.")
            return
        
        config_name = gcmd.get('CONFIG', '').lower()  # Retrieve the CONFIG argument
        if config_name == 'day':
            source_config = self.day_config
        elif config_name == 'night':
            source_config = self.night_config
        else:
            destination = os.path.expanduser('~/printer_data/config/printer.cfg')
            if os.path.exists(destination):
                current_md5 = self.calculate_md5(destination)
                if current_md5 == self.calculate_md5(self.day_config):
                    source_config = self.night_config
                elif current_md5 == self.calculate_md5(self.night_config):
                    source_config = self.day_config
                else:
                    gcmd.respond_info("Current configuration does not match day_config or night_config")
                    return
            else:
                gcmd.respond_info("No configuration file found")
                return

        destination = os.path.expanduser('~/printer_data/config/printer.cfg')
        
        # Check if the destination file is already the same as the source file
        if os.path.exists(destination) and self.calculate_md5(source_config) == self.calculate_md5(destination):
            logging.info(f"Configuration already set to {config_name}, no switch needed")
            gcmd.respond_info(f"Configuration already set to {config_name}")
            return

        # Copy the configuration file to the printer.cfg location
        shutil.copy2(source_config, destination)

        # Calculate MD5 checksum after copying
        dest_md5 = self.calculate_md5(destination)

        if self.calculate_md5(source_config) == dest_md5:
            logging.info(f"Configuration successfully switched to {config_name}")
            gcmd.respond_info(f"Configuration switched to {config_name}, restart in 3s...")
            # Restart Klipper service
            # self.printer.reset()
            # Wait for 3 seconds before restarting
            time.sleep(3)
            # Send FIRMWARE_RESTART command to Klipper
            self.gcode.run_script_from_command("FIRMWARE_RESTART")
        else:
            logging.error(f"MD5 mismatch: Source != Destination")
            gcmd.respond_info(f"Configuration switch failed: MD5 mismatch")


    def cmd_CHECK_CONFIG(self, gcmd):
        """Check the current configuration file."""
        destination = os.path.expanduser('~/printer_data/config/printer.cfg')
        if os.path.exists(destination):
            current_md5 = self.calculate_md5(destination)
            if current_md5 == self.calculate_md5(self.day_config):
                gcmd.respond_info("Current configuration is day_config")
            elif current_md5 == self.calculate_md5(self.night_config):
                gcmd.respond_info("Current configuration is night_config")
            else:
                gcmd.respond_info("Current configuration does not match day_config or night_config")
        else:
            gcmd.respond_info("No configuration file found")

def load_config(config):
    return ConfigSwitcher(config)
