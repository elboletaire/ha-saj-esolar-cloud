# 🌞 SAJ eSolar Cloud Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/elboletaire/ha-saj-esolar-cloud.svg)](https://github.com/elboletaire/ha-saj-esolar-cloud/releases)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A comprehensive Home Assistant integration for SAJ eSolar cloud service, providing detailed monitoring of H1 inverters with battery storage systems.

This integration is a complete rewrite focused on H1 inverters with battery storage, using the modern Elekeeper cloud API. The "Cloud" suffix denotes its cloud-based nature and distinguishes it from other SAJ eSolar integrations.
It started as a fork of [SAJeSolar](https://github.com/djansen1987/SAJeSolar) by @djansen1987, and has since been fully rewritten for current API behavior and hardware targets, so the current codebase no longer shares code with the original project.

## ✨ Key Features

- 🎛️ **Multi-Plant Support**: Monitor multiple solar installations from a single integration
- 🔋 **Individual Battery Monitoring**: Each battery appears as a separate device with comprehensive metrics
- 🏠 **System-Level Overview**: Inverter device provides aggregated system data
- 🌍 **Multi-Region Support**: EU, India, and China regions
- 🌐 **Bilingual Support**: English and Catalan translations
- 🔄 **Real-Time Data**: Automatic updates every 5 minutes
- 📊 **Rich Metrics**: 40+ sensors covering all aspects of your solar system

## 🏗️ Device Architecture

### 🏭 **Main Plant Device** (e.g., "P00266-23")
**System-level monitoring and aggregated data:**
- Total system capacity and power flows
- Operating modes and system status
- Environmental impact metrics
- Grid interaction and energy flows

### 🔋 **Individual Battery Devices** (e.g., "P00266-23 Battery 1", "P00266-23 Battery 2")
**Per-battery detailed monitoring:**
- Individual battery health and performance
- Temperature and voltage monitoring
- Charge/discharge cycles and energy flows
- Technical specifications and diagnostics

## 📊 Comprehensive Sensor Coverage

### ⚡ **Power & Energy Monitoring**
| Sensor | Description | Unit |
|--------|-------------|------|
| **Current Power** | Real-time solar generation | W |
| **PV Power** | Photovoltaic panel output | W |
| **Grid Power** | Grid import/export (±) | W |
| **Battery Power** | Battery charge/discharge (±) | W |
| **Output Power** | House consumption | W |
| **Total Load Power** | Total system load | W |

### 🔋 **Battery System Monitoring**
| Sensor | Description | Unit |
|--------|-------------|------|
| **Battery Capacity** | Total system capacity | kWh |
| **Usable Capacity** | Currently available energy | kWh |
| **Battery Current** | System current flow | A |
| **Battery Voltage** | System voltage | V |
| **Battery Remaining Time** | Estimated runtime | hours |
| **Operating Mode** | System operation mode | - |

### 📈 **Energy Statistics**
| Period | Generation | Consumption | Grid Import | Grid Export | Battery Charge | Battery Discharge |
|--------|------------|-------------|-------------|-------------|----------------|-------------------|
| **Today** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Month** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Year** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Total** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 🔋 **Individual Battery Sensors**
| Sensor | Description | Unit |
|--------|-------------|------|
| **Battery Level** | State of charge (SOC) | % |
| **Battery Health** | State of health (SOH) | % |
| **Battery Temperature** | Operating temperature | °C |
| **Battery Status** | Running state | - |
| **Battery Model** | Hardware model | - |
| **Battery Power** | Individual power flow | W |
| **Battery Current** | Individual current | A |
| **Battery Voltage** | Individual voltage | V |

### 🌍 **Environmental Impact**
| Sensor | Description | Unit |
|--------|-------------|------|
| **Trees Planted** | Environmental equivalent | count |
| **CO₂ Reduction** | Carbon footprint reduction | t |
| **Daily Trees Planted** | Today's environmental impact | count |
| **Daily CO₂ Reduction** | Today's carbon reduction | t |

### 🔄 **System Status & Directions**
| Sensor | Description | States |
|--------|-------------|--------|
| **PV Direction** | Solar panel flow | Importing/Standby/Exporting |
| **Grid Direction** | Grid interaction | Importing/Standby/Exporting |
| **Battery Direction** | Battery operation | Charging/Idle/Discharging |
| **Device Online** | System connectivity | Yes/No |
| **Last Update** | Data freshness | timestamp |

## 🚀 Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=elboletaire&repository=ha-saj-esolar-cloud&category=integration)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots menu in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/elboletaire/ha-saj-esolar-cloud`
6. Select category: "Integration"
7. Click "Add"
8. Find "SAJ eSolar Cloud" in the integrations list and install it
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/saj_esolar_cloud` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## ⚙️ Configuration

### Initial Setup

1. Go to Home Assistant's **Settings** > **Devices & Services**
2. Click the **"+ Add Integration"** button
3. Search for **"SAJ eSolar Cloud"**
4. Enter your eSolar Portal credentials:
   - **Username**: Your eSolar Portal username
   - **Password**: Your eSolar Portal password
   - **Region**: Select your region (EU, India, or China)

### Plant Selection

5. **Select Plants**: Choose which solar installations to monitor
   - ✅ Multi-select support for multiple plants
   - 🏭 Each plant becomes a separate device
   - 🔋 Individual batteries automatically detected

### Reconfiguration

- Use **"Configure"** button in the integration to modify monitored plants
- Add or remove plants without reinstalling the integration

## 🔧 Advanced Features

### 🔋 **Battery Health Calculation**
- Realistic health percentages based on degradation
- Formula: `Health = 100 - Degradation`
- Accounts for natural battery aging over time

### 📊 **Rich Sensor Attributes**
- **Operating Mode sensor**: Battery quantity, last update timestamp
- **Battery Model sensor**: Hardware/software versions, serial numbers, cluster IDs
- **Technical specifications**: Complete battery management system details

### 🌐 **Multi-Language Support**
- **English**: Complete translation coverage
- **Catalan**: Native Catalan terminology and expressions
- Proper technical terminology for solar/battery systems

### 🔄 **Smart Data Mapping**
- **System-level data**: Aggregated values for total system monitoring
- **Individual data**: Per-battery metrics for detailed analysis
- **Calculated values**: Intelligent distribution of system data across batteries

## 🛠️ Troubleshooting

### Common Issues

**No data showing:**
- Verify credentials are correct
- Check if your region is properly selected
- Ensure your inverter is online in the eSolar portal

**Missing batteries:**
- Battery devices appear automatically if detected
- Check if batteries are properly configured in eSolar portal
- Restart Home Assistant after battery installation

**Incorrect values:**
- Integration uses real-time API data
- Values may differ slightly from eSolar portal due to timing
- Check "Last Update" sensor for data freshness

## 📈 Energy Dashboard Integration

All sensors are properly configured for Home Assistant's Energy Dashboard:
- ✅ **Solar Production**: Today/Month/Year Generation
- ✅ **Grid Consumption**: Grid Import sensors
- ✅ **Grid Return**: Grid Export sensors
- ✅ **Battery Storage**: Battery Charge/Discharge sensors
- ✅ **Home Consumption**: Load consumption sensors

## 🤝 Support

For bugs, please [open an issue on GitHub](https://github.com/elboletaire/ha-saj-esolar-cloud/issues).

Please note: This is a personal project. While I welcome bug reports, I have limited time for feature requests and general support.

## Attribution

This project originated from [SAJeSolar](https://github.com/djansen1987/SAJeSolar) by @djansen1987. The current codebase is a full rewrite; this attribution reflects the project origin and early structure. Thanks for the original groundwork.

## 🙏 Credits

Vibe coded by **Òscar Casajuana** ([@elboletaire](https://github.com/elboletaire))

Special thanks to the Home Assistant community and SAJ Electric for their solar technology.

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**🌞 Happy Solar Monitoring! 🔋**

*Made with ❤️ for the Home Assistant community*

</div>
