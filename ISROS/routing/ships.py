
class Ship:
    def __init__(self, name, average_speed_knots, max_dwt, fuel_consumption_rate, propeller_condition_factor=1.0):
        self.name = name
        self.average_speed_knots = average_speed_knots
        self.max_dwt = max_dwt
        self.fuel_consumption_rate = fuel_consumption_rate
        self.propeller_condition_factor = propeller_condition_factor

    def get_speed_adjustment_factor(self, load_percentage):

        if load_percentage < 0 or load_percentage > 100:
            raise ValueError("Load percentage must be between 0 and 100.")

        # 100% load results in a 10% reduction in speed
        speed_reduction = 0.1 * (load_percentage / 100)
        return 1 - speed_reduction

    def get_adjusted_speed_knots(self, load_percentage):
        adjustment_factor = self.get_speed_adjustment_factor(load_percentage)
        return self.average_speed_knots * adjustment_factor

    def get_adjusted_speed_kmh(self, load_percentage):
        adjusted_speed_knots = self.get_adjusted_speed_knots(load_percentage)
        return adjusted_speed_knots * 1.852  # Conversion factor from knots to km/h

    def get_fuel_consumption_per_hour(self, load_percentage):
        # Fuel consumption now also depends on the propeller condition
        speed_ratio = self.get_adjusted_speed_knots(load_percentage) / self.average_speed_knots
        fuel_consumption = self.fuel_consumption_rate * (speed_ratio ** 3) * (1 + load_percentage / 100) * self.propeller_condition_factor
        return fuel_consumption
    
    def get_fuel_consumption_per_nautical_mile(self, load_percentage):

        adjusted_speed_knots = self.get_adjusted_speed_knots(load_percentage)
        fuel_consumption_per_hour = self.get_fuel_consumption_per_hour(load_percentage)
        fuel_consumption_per_nautical_mile = fuel_consumption_per_hour / adjusted_speed_knots
        return fuel_consumption_per_nautical_mile
    
    def get_fuel_cost_per_nautical_mile(self, load_percentage, fuel_price_per_ton):

        fuel_consumption_per_nautical_mile = self.get_fuel_consumption_per_nautical_mile(load_percentage)
        cost_per_nautical_mile = fuel_consumption_per_nautical_mile * fuel_price_per_ton
        return cost_per_nautical_mile
    
    def get_consumption_and_cost_per_distance(self, load_percentage, fuel_price_per_ton, distance_nautical_miles=10):

        fuel_consumption_per_nautical_mile = self.get_fuel_consumption_per_nautical_mile(load_percentage)
        cost_per_nautical_mile = self.get_fuel_cost_per_nautical_mile(load_percentage, fuel_price_per_ton)

        fuel_consumption = fuel_consumption_per_nautical_mile * distance_nautical_miles
        cost = cost_per_nautical_mile * distance_nautical_miles

        return fuel_consumption, cost

class ContainerCargoShip(Ship):
    def __init__(self, propeller_condition_factor=1.0):
        super().__init__("Container Cargo Ship", 22, 182000, 100, propeller_condition_factor)

class CrudeOilTankerShip(Ship):
    def __init__(self, propeller_condition_factor=1.0):
        super().__init__("Crude Oil Tanker Ship", 13.5, 200000, 200, propeller_condition_factor)

class RoRoShip(Ship):
    def __init__(self, propeller_condition_factor=1.0):
        super().__init__("Ro-Ro Ship", 17.5, 10000, 60, propeller_condition_factor)
