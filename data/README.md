# Data

Place the processed dataset here (not committed to git):

    data/energy_consumption.csv

Expected columns (used exactly as-is, no renaming):

    timestamp, energy_kwh, Global_reactive_power, Voltage,
    Global_intensity, Sub_metering_1, Sub_metering_2, Sub_metering_3

Timestamp format `YYYY-MM-DD HH:MM:SS`, 1-minute frequency, target `energy_kwh`.
Row count, ranges and gaps are validated in the Colab notebook, not assumed here.
