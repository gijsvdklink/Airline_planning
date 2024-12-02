import numpy as np
from sklearn.linear_model import LinearRegression

def prepare_gravity_data(demand_data):
    """
    Bereidt de data voor door logaritmen toe te passen op de relevante kolommen.
    """
    # Logaritmen toepassen op de relevante kolommen
    demand_data['log_demand'] = np.log(demand_data['demand'])
    demand_data['log_pop'] = np.log(demand_data['pop_i'] * demand_data['pop_j'])
    demand_data['log_gdp'] = np.log(demand_data['GDP_i'] * demand_data['GDP_j'])
    demand_data['log_distance'] = np.log(demand_data['distance'])
    return demand_data

def calibrate_gravity_model(demand_data):
    """
    Kalibreert het gravity model en retourneert de parameters k, b1, b2, en b3.
    """
    # Input- en outputvariabelen voor regressie
    X = demand_data[['log_pop', 'log_gdp', 'log_distance']].values
    y = demand_data['log_demand'].values

    # Pas Ordinary Least Squares (OLS) toe
    model = LinearRegression()
    model.fit(X, y)

    # Haal de parameters op
    k = np.exp(model.intercept_)
    b1, b2, b3 = model.coef_
    return k, b1, b2, b3
