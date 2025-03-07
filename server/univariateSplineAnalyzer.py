import json
import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.integrate import simpson

class UnivariateSplineAnalyzer:
    def __init__(self, asset, timeline):
        self.asset = asset
        self.timeline = timeline
        self.data_points = self.load_data()
        self.update_analysis()  # Initial analysis after loading data

    def load_data(self):
        # Load data dynamically based on asset and timeline
        file_name = f'data/{self.asset}_{self.timeline}_strike_mark_data.json'
        try:
            with open(file_name, 'r') as f:
                data = json.load(f)
            return data.get("data", [])
        except FileNotFoundError:
            raise ValueError(f"Data file {file_name} not found")

    def update_analysis(self):
        # Extract x and y from data points
        if not self.data_points:
            return
        strike_prices, call_prices = zip(*self.data_points)
        self.strike_prices = np.array(strike_prices)
        self.call_prices = np.array(call_prices)

        risk_free_rate = 0.01
        time_to_expiry = 1 / 365  


        spline = UnivariateSpline(strike_prices, call_prices, k=3, s=1e-6)

        # Compute derivatives
        dC_dK = spline.derivative(1)(strike_prices)
        d2C_dK2 = spline.derivative(2)(strike_prices)

        # Risk-neutral PDF
        self.pdf = np.exp(risk_free_rate * time_to_expiry) * d2C_dK2

        # Force positivity
        self.pdf = np.clip(self.pdf, 0, None)

        # Normalize PDF
        total_area = simpson(self.pdf, x=strike_prices)
        self.pdf /= total_area

    def refresh_data(self):
        self.data_points = self.load_data()  
        self.update_analysis()

    def integrate_pdf(self, target_price):
        """
        Integrates the PDF over a specified range of strike prices.

        Parameters:
            strike_prices (array-like): The strike price points.
            pdf (array-like): The risk-neutral PDF values.
            lower_bound (float): The lower bound of integration.
            upper_bound (float): The upper bound of integration.

        Returns:
            float: The integrated probability over the range [lower_bound, upper_bound].
        """
        # Convert to numpy arrays
        self.strike_prices = np.array(self.strike_prices)
        self.pdf = np.array(self.pdf)

        # Mask the range of interest
        mask = (self.strike_prices >= 0) & (self.strike_prices <= target_price)
        selected_strike_prices = self.strike_prices[mask]
        selected_pdf = self.pdf[mask]

        # Integrate using Simpson's rule
        probability = simpson(selected_pdf, x=selected_strike_prices)
        return round(probability * 100, 2)

    def get_graph_data(self):
        return {
            "original_function": {
                "x": self.x_range.tolist(),
                "y": self.y_spline.tolist()
            },
            "first_derivative": {
                "x": self.x_range.tolist(),
                "y": self.y_spline_der1.tolist()
            },
            "second_derivative": {
                "x": self.x_range.tolist(),
                "y": self.y_spline_der2_clipped.tolist()
            }
        }
