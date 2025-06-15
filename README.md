# Data Center Monitoring System

A real-time monitoring system for data center hard drives, tracking vibration, temperature, and power metrics to detect anomalies and prevent failures.

## Features

- Real-time monitoring of rack metrics:
  - Temperature
  - Vibration
  - Power consumption
- Interactive dashboard with rack status map
- Anomaly detection with configurable thresholds
- Alert history tracking
- Repair and replacement management
- Visual indicators for rack health status

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/datacenter-monitor.git
cd datacenter-monitor
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:8050
```

## Monitoring Thresholds

The system uses the following default thresholds:

- Temperature:
  - Warning: 40°C
  - Critical: 45°C
- Vibration:
  - Warning: 0.8g
  - Critical: 1.2g
- Power:
  - Warning: 1200W
  - Critical: 1500W

A rack is flagged for replacement if it receives 3 or more critical alerts within a 24-hour period.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 