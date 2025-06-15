import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import deque

class AnomalyDetector:
    def __init__(self):
        # Thresholds for different metrics
        self.thresholds = {
            'temperature': {'warning': 42, 'critical': 45},  # in Celsius
            'vibration': {'warning': 0.8, 'critical': 1.2},  # in g
            'power': {'warning': 1200, 'critical': 1500}     # in Watts
        }
        
        # Store alert history for each rack
        self.alert_history: Dict[str, List[Tuple[datetime, str]]] = {}
        
        # Store metric history for prediction
        self.metric_history: Dict[str, Dict[str, deque]] = {}
        
        # Store prediction status
        self.predictions: Dict[str, Dict] = {}
        
        # Failure prediction thresholds
        self.prediction_thresholds = {
            'alert_frequency': 3,  # alerts per hour
            'trend_threshold': 0.7,  # positive trend threshold
            'history_hours': 4  # hours of history to analyze
        }
    
    def initialize_rack_history(self, rack_id: str):
        """Initialize history storage for a new rack."""
        if rack_id not in self.metric_history:
            self.metric_history[rack_id] = {
                'temperature': deque(maxlen=240),  # 4 hours of minute data
                'vibration': deque(maxlen=240),
                'power': deque(maxlen=240),
                'timestamps': deque(maxlen=240)
            }
        if rack_id not in self.alert_history:
            self.alert_history[rack_id] = []
        if rack_id not in self.predictions:
            self.predictions[rack_id] = {
                'status': 'normal',
                'confidence': 0.0,
                'predicted_failure_time': None,
                'reasons': []
            }
    
    def analyze_trend(self, values: List[float]) -> float:
        """Analyze trend in metric values."""
        if len(values) < 30:  # Need at least 30 minutes of data
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # Normalize slope to a -1 to 1 scale
        max_slope = np.std(y) / len(y)
        normalized_slope = np.clip(slope / max_slope, -1, 1)
        
        return normalized_slope
    
    def predict_failures(self, rack_id: str) -> Dict:
        """Predict potential failures based on metric history."""
        if len(self.metric_history[rack_id]['timestamps']) < 60:  # Need at least 1 hour of data
            return self.predictions[rack_id]
        
        # Analyze trends
        temp_trend = self.analyze_trend(list(self.metric_history[rack_id]['temperature']))
        vib_trend = self.analyze_trend(list(self.metric_history[rack_id]['vibration']))
        power_trend = self.analyze_trend(list(self.metric_history[rack_id]['power']))
        
        # Count recent alerts
        recent_alerts = len([
            alert for alert in self.alert_history[rack_id]
            if alert[0] > datetime.now() - timedelta(hours=1)
        ])
        
        # Calculate prediction confidence
        confidence = 0.0
        reasons = []
        
        if temp_trend > self.prediction_thresholds['trend_threshold']:
            confidence += 0.3
            reasons.append("Rising temperature trend")
        
        if vib_trend > self.prediction_thresholds['trend_threshold']:
            confidence += 0.3
            reasons.append("Increasing vibration levels")
        
        if power_trend > self.prediction_thresholds['trend_threshold']:
            confidence += 0.2
            reasons.append("Growing power consumption")
        
        if recent_alerts >= self.prediction_thresholds['alert_frequency']:
            confidence += 0.2
            reasons.append(f"High alert frequency ({recent_alerts} in last hour)")
        
        # Update prediction status
        prediction_status = 'normal'
        predicted_failure_time = None
        
        if confidence >= 0.8:
            prediction_status = 'critical'
            predicted_failure_time = datetime.now() + timedelta(minutes=30)
        elif confidence >= 0.5:
            prediction_status = 'warning'
            predicted_failure_time = datetime.now() + timedelta(hours=2)
        
        self.predictions[rack_id] = {
            'status': prediction_status,
            'confidence': confidence,
            'predicted_failure_time': predicted_failure_time,
            'reasons': reasons
        }
        
        return self.predictions[rack_id]
    
    def analyze_rack(self, rack_id: str, temperature: float, vibration: float, power: float) -> dict:
        """Analyze the current state of a rack based on its sensor readings."""
        current_time = datetime.now()
        
        # Initialize history for new racks
        self.initialize_rack_history(rack_id)
        
        # Update metric history
        self.metric_history[rack_id]['temperature'].append(temperature)
        self.metric_history[rack_id]['vibration'].append(vibration)
        self.metric_history[rack_id]['power'].append(power)
        self.metric_history[rack_id]['timestamps'].append(current_time)
        
        # Check immediate thresholds
        temp_status = 'normal'
        vib_status = 'normal'
        power_status = 'normal'
        
        if temperature >= self.thresholds['temperature']['critical']:
            temp_status = 'critical'
        elif temperature >= self.thresholds['temperature']['warning']:
            temp_status = 'warning'
            
        if vibration >= self.thresholds['vibration']['critical']:
            vib_status = 'critical'
        elif vibration >= self.thresholds['vibration']['warning']:
            vib_status = 'warning'
            
        if power >= self.thresholds['power']['critical']:
            power_status = 'critical'
        elif power >= self.thresholds['power']['warning']:
            power_status = 'warning'
        
        # Update alert history if not normal
        current_status = 'normal'
        if any(s == 'critical' for s in [temp_status, vib_status, power_status]):
            current_status = 'critical'
            self.alert_history[rack_id].append((current_time, 'critical'))
        elif any(s == 'warning' for s in [temp_status, vib_status, power_status]):
            current_status = 'warning'
            self.alert_history[rack_id].append((current_time, 'warning'))
        
        # Clean up old alerts (older than 24 hours)
        cutoff_time = current_time - timedelta(hours=24)
        self.alert_history[rack_id] = [
            alert for alert in self.alert_history[rack_id]
            if alert[0] > cutoff_time
        ]
        
        # Get prediction
        prediction = self.predict_failures(rack_id)
        
        return {
            'status': current_status,
            'prediction': prediction,
            'metrics': {
                'temperature': {'value': temperature, 'status': temp_status},
                'vibration': {'value': vibration, 'status': vib_status},
                'power': {'value': power, 'status': power_status}
            },
            'alert_count': len(self.alert_history[rack_id])
        }
    
    def get_alert_history(self, rack_id: str) -> List[Tuple[datetime, str]]:
        """Get the alert history for a specific rack."""
        return self.alert_history.get(rack_id, []) 