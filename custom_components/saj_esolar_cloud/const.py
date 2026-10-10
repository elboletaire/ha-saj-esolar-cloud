"""Constants for the SAJ eSolar Cloud integration."""
from typing import Final

DOMAIN: Final = "saj_esolar_cloud"
MANUFACTURER: Final = "SAJ"
MODEL: Final = "H1"

# Region configuration
CONF_REGION: Final = "region"
CONF_MONITORED_PLANTS: Final = "monitored_plants"

# Regions and their base URLs
REGIONS = {
    "eu": "https://eop.saj-electric.com/dev-api/api/v1",
    "in": "https://iop.saj-electric.com/dev-api/api/v1",
    "cn": "https://op.saj-electric.cn/dev-api/api/v1"
}

# Update interval
UPDATE_INTERVAL: Final = 300  # 5 minutes

# Device info
DEVICE_INFO = {
    "identifiers": {(DOMAIN, "h1")},
    "name": "SAJ H1 Solar Inverter",
    "manufacturer": MANUFACTURER,
    "model": MODEL,
}

# Sensor definitions for H1 device
H1_SENSORS = {
    # Plant Detail Sensors
    "nowPower": {
        "name": "Current Power",
        "icon": "mdi:solar-power",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "todayElectricity": {
        "name": "Today Generation",
        "icon": "mdi:solar-power",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "monthElectricity": {
        "name": "Current Month Generation",
        "icon": "mdi:solar-power",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "yearElectricity": {
        "name": "Current Year Generation",
        "icon": "mdi:solar-power",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "totalElectricity": {
        "name": "Total Generation",
        "icon": "mdi:solar-power",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "totalConsumpElec": {
        "name": "Total Consumption",
        "icon": "mdi:home-lightning-bolt",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "totalBuyElec": {
        "name": "Total Grid Import",
        "icon": "mdi:transmission-tower-import",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "totalSellElec": {
        "name": "Total Grid Export",
        "icon": "mdi:transmission-tower-export",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "selfUseRate": {
        "name": "Self-Use Rate",
        "icon": "mdi:home-percent",
        "device_class": None,
        "state_class": "measurement",
        "unit": "%",
    },
    "totalPlantTreeNum": {
        "name": "Trees Planted",
        "icon": "mdi:tree",
        "device_class": None,
        "state_class": "total",
        "unit": None,
    },
    "totalReduceCo2": {
        "name": "CO₂ Reduction",
        "icon": "mdi:molecule-co2",
        "device_class": None,
        "state_class": "total",
        "unit": "t",
    },
    "dailyConsumption": {
        "name": "Today Consumption",
        "icon": "mdi:home-lightning-bolt",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "dailyGridImport": {
        "name": "Today Grid Import",
        "icon": "mdi:transmission-tower-import",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "dailyGridExport": {
        "name": "Today Grid Export",
        "icon": "mdi:transmission-tower-export",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "dailyBatteryCharge": {
        "name": "Today Battery Charge",
        "icon": "mdi:battery-charging",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "dailyBatteryDischarge": {
        "name": "Today Battery Discharge",
        "icon": "mdi:battery-minus",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "dailyTreesPlanted": {
        "name": "Today Trees Planted",
        "icon": "mdi:tree",
        "device_class": None,
        "state_class": "total",
        "unit": None,
    },
    "dailyReduceCo2": {
        "name": "Today CO2 Reduction",
        "icon": "mdi:molecule-co2",
        "device_class": None,
        "state_class": "total",
        "unit": "t",
    },
    "lastUploadTime": {
        "name": "Last Update",
        "icon": "mdi:clock",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
    },

    # Device Power Sensors
    "pvPower": {
        "name": "PV Power",
        "icon": "mdi:solar-power",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "gridPower": {
        "name": "Grid Power",
        "icon": "mdi:transmission-tower",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
        "description": "Positive when importing, negative when exporting",
    },
    "gridPowerAbsolute": {
        "name": "Grid Power Absolute",
        "icon": "mdi:transmission-tower",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "batteryPower": {
        "name": "Battery Power",
        "icon": "mdi:battery-charging",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
        "description": "Positive when discharging, negative when charging",
    },
    "batteryPowerAbsolute": {
        "name": "Battery Power Absolute",
        "icon": "mdi:battery-charging",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "outPower": {
        "name": "Output Power",
        "icon": "mdi:power-plug",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "totalLoadPower": {
        "name": "Total Load Power",
        "icon": "mdi:home-lightning-bolt",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "batCurr": {
        "name": "Battery Current",
        "icon": "mdi:current-dc",
        "device_class": None,
        "state_class": "measurement",
        "unit": "A",
    },
    "batEnergyPercent": {
        "name": "Battery Level",
        "icon": "mdi:battery",
        "device_class": "battery",
        "state_class": "measurement",
        "unit": "%",
    },
    "batCapcity": {
        "name": "Battery Capacity",
        "icon": "mdi:battery-charging-100",
        "device_class": "energy_storage",
        "state_class": None,
        "unit": "kWh",
    },
    "usableBatCapacity": {
        "name": "Usable Battery Capacity",
        "icon": "mdi:battery-charging-80",
        "device_class": "energy_storage",
        "state_class": "measurement",
        "unit": "kWh",
    },
    "batteryWorkTime": {
        "name": "Battery Remaining Time",
        "icon": "mdi:timer-outline",
        "device_class": "duration",
        "state_class": "measurement",
        "unit": "h",
    },
    "operatingMode": {
        "name": "Operating Mode",
        "icon": "mdi:cog",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "batVoltage": {
        "name": "Battery Voltage",
        "icon": "mdi:lightning-bolt",
        "device_class": "voltage",
        "state_class": "measurement",
        "unit": "V",
    },
    "batTemperature": {
        "name": "Battery Temperature",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
        "unit": "°C",
    },
    "pvDirection": {
        "name": "PV Direction",
        "icon": "mdi:solar-power",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "gridDirection": {
        "name": "Grid Direction",
        "icon": "mdi:transmission-tower",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "batteryDirection": {
        "name": "Battery Direction",
        "icon": "mdi:battery",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "outPutDirection": {
        "name": "Output Direction",
        "icon": "mdi:power-plug",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "isOnline": {
        "name": "Device Online",
        "icon": "mdi:power-plug",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "inverterStatus": {
        "name": "Inverter Status",
        "icon": "mdi:check-circle",
        "device_class": None,
        "state_class": None,
        "unit": None,
    }
}

# Direction states mapping
DIRECTION_STATES = {
    -1: "Importing",
    0: "Standby",
    1: "Exporting"
}

# Battery states mapping
BATTERY_STATES = {
    -1: "Charging",
    0: "Idle",
    1: "Discharging"
}

# New API endpoints for Elekeeper
ENDPOINTS = {
    "login": "/sys/login",
    "plant_list": "/monitor/plant/getEndUserPlantList",
    "plant_detail": "/monitor/plant/getOnePlantInfo",
    "device_list": "/monitor/device/getDeviceList",
    "device_info": "/monitor/device/getOneDeviceInfo",
    "battery_list": "/monitor/battery/getBatteryList",
    "battery_info": "/monitor/battery/getOneDeviceBatteryInfo",
    "battery_statistics": "/monitor/home/getHomeBatteryStatisticsData",
    "ems_list": "/monitor/plant/ems/getEmsListByPlant",
    "raw_data": "/monitor/deviceData/findRawdataPageList",
    "device_alarms": "/alarm/device/userAlarmPage"
}

# api/v2 endpoints (relative to the region base URL with /api/v2 instead of /api/v1)
ENDPOINTS_V2 = {
    "login": "/sys/user/login",
    "plant_capability": "/monitor/plant/getPlantCapability",
    "plant_statistics": "/monitor/plantHome/getPlantEnergyStatistics",
    "energy_flow": "/monitor/plantHome/getDeviceEnergyFlowDiagram",
}

# Battery sensor definitions for individual batteries
BATTERY_SENSORS = {
    "batSoc": {
        "name": "Battery Level",
        "icon": "mdi:battery",
        "device_class": "battery",
        "state_class": "measurement",
        "unit": "%",
    },
    "batTemperature": {
        "name": "Battery Temperature",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
        "unit": "°C",
    },
    "batSoh": {
        "name": "Battery Health",
        "icon": "mdi:battery-heart",
        "device_class": None,
        "state_class": "measurement",
        "unit": "%",
    },
    "runningState": {
        "name": "Battery Status",
        "icon": "mdi:battery-charging",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "batModel": {
        "name": "Battery Model",
        "icon": "mdi:information",
        "device_class": None,
        "state_class": None,
        "unit": None,
    },
    "batPower": {
        "name": "Battery Power",
        "icon": "mdi:battery-charging",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "batCurrent": {
        "name": "Battery Current",
        "icon": "mdi:current-dc",
        "device_class": "current",
        "state_class": "measurement",
        "unit": "A",
    },
    "batVoltage": {
        "name": "Battery Voltage",
        "icon": "mdi:lightning-bolt",
        "device_class": "voltage",
        "state_class": "measurement",
        "unit": "V",
    },
    "todayBatCharge": {
        "name": "Today Battery Charge",
        "icon": "mdi:battery-plus",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "todayBatDischarge": {
        "name": "Today Battery Discharge",
        "icon": "mdi:battery-minus",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "totalBatCharge": {
        "name": "Total Battery Charge",
        "icon": "mdi:battery-plus",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "totalBatDischarge": {
        "name": "Total Battery Discharge",
        "icon": "mdi:battery-minus",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
}
