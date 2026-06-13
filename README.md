# MySports Integration for Home Assistant

This custom integration for Home Assistant allows you to monitor studio utilization and course schedules from your MySports fitness studios directly within Home Assistant. Track how busy your gym is and never miss a class again!

![Version](https://img.shields.io/github/v/release/JonasJoKuJonas/homeassistant-MySports)
![Downloads](https://img.shields.io/github/downloads/JonasJoKuJonas/homeassistant-MySports/total)
![HACS Install Badge](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20installations&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.mysports.total)
[![Latest Release](https://img.shields.io/github/release-date/JonasJoKuJonas/homeassistant-MySports?style=flat&label=Latest%20Release)](https://github.com/JonasJoKuJonas/homeassistant-MySports/releases)
[![Open Issues](https://img.shields.io/github/issues/JonasJoKuJonas/homeassistant-MySports?style=flat&label=Open%20Issues)](https://github.com/JonasJoKuJonas/homeassistant-MySports/issues)

## Disclaimer

This integration uses the unofficial MySports API, not an official API. It may be subject to errors or changes in MySports' API structure that could affect functionality. Use this component at your own risk. The developers are not affiliated with MySports and are not liable for any damages resulting from its use.

## Features

- 📊 **Studio Utilization Sensors** - Real-time occupancy tracking for each of your studios
- 📅 **Course Calendars** - Automatic synchronization of all upcoming courses per studio
- ⚙️ **Configurable Update Intervals** - Separate intervals for utilization and calendar data
- 🏢 **Multi-Studio Support** - Works with all studios linked to your account

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JonasJoKuJonas&repository=homeassistant-MySports&category=Integration)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Click the badge above or navigate to HACS → Integrations → Custom Repositories
3. Click "Download" on the MySports integration
4. Restart Home Assistant

## Setup Instructions

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** and search for "MySports"
3. Enter your MySports credentials:
   - **Username**: Your MySports email address
   - **Password**: Your MySports password
4. Click **Submit**

The integration will automatically detect all studios linked to your account and create the corresponding entities.

## Available Entities

For each studio in your MySports account, the integration creates the following entities:

| Entity ID                | Type     | Description                                      |
| ------------------------ | -------- | ------------------------------------------------ |
| `sensor.<studio_name>`   | Sensor   | Current number of active check-ins at the studio |
| `calendar.<studio_name>` | Calendar | All upcoming courses for the studio              |

The calendar events include course name, start/end times (automatically converted to your timezone), location address, and booking availability status.

## Configuration Options

You can adjust the update intervals via **Settings** → **Devices & Services** → **MySports** → **Configure**:

| Option                   | Description                                      | Default | Minimum |
| ------------------------ | ------------------------------------------------ | ------- | ------- |
| `scan_interval`          | How often to update studio utilization (minutes) | 30      | 10      |
| `calendar_scan_interval` | How often to update course calendars (minutes)   | 360     | 30      |

## Supported Studios

The MySports integration works with any studio that uses the MySports/Magicline platform. The list below shows confirmed studios, but any studio connected to your MySports account can be used.

### MC Shape Studios (36 locations)

- MC Shape - Wetterfit GmbH
- MC Shape Aalen
- MC Shape Bernhausen
- MC Shape GmbH - Althengstett
- MC Shape GmbH - Dornstadt
- MC Shape GmbH - Horb
- MC Shape GmbH - Jettingen
- MC Shape GmbH - Kuppenheim
- MC Shape GmbH - Köngen
- MC Shape GmbH - Lauchhammer
- MC Shape GmbH - Markdorf
- MC Shape GmbH - Meckenbeuren
- MC Shape GmbH - Nagold
- MC Shape GmbH - Nersingen
- MC Shape GmbH - Radolfzell am Bodensee
- MC Shape GmbH - Salem
- MC Shape GmbH - Schramberg
- MC Shape GmbH - Stadtallendorf
- MC Shape GmbH - Vaihingen
- MC Shape GmbH - Überlingen
- MC Shape Headquarter
- MC Shape Herrenberg
- MC Shape Iffezheim
- MC Shape Metzingen
- MC Shape Meßkirch
- MC Shape Oberndorf
- MC Shape Pfalzgrafenweiler
- MC Shape Pfullendorf
- MC Shape Pfullingen
- MC Shape Rottenburg
- MC Shape Rottweil
- MC Shape Spaichingen
- MC Shape Sto
- MC Shape Tuttlingen
- MC Shape Tübingen
- MC Shape Villingen-Schwenningen

### Other Partner Studios

- **Athletics Burgdorf GmbH** - Burgdorf, Niedersachsen
- **Guengoer Fitness KG** - Köln, Nordrhein-Westfalen
- **Muscle Club Eisenach GmbH** - Eisenach, Thüringen

### Geographic Coverage (Germany)

| State               | Number of Studios |
| ------------------- | ----------------- |
| Baden-Württemberg   | 30+               |
| Bayern              | 1                 |
| Hessen              | 1                 |
| Niedersachsen       | 1                 |
| Nordrhein-Westfalen | 1                 |
| Thüringen           | 1                 |

> **Note**: This is not an exhaustive list. The integration automatically detects all studios linked to your MySports account, regardless of whether they appear in this list.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/Jonas_JoKu)
