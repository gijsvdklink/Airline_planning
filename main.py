# main.py

for i in range (10):

    print ('hoi')
from models.demand_forecast import load_data, calibrate_gravity_model

def main():
    # Step 1: Load the data
    pop_data, demand_data = load_data()

    # Step 2: Calibrate the gravity model
    model_params = calibrate_gravity_model(pop_data, demand_data)
    print(f"Model Parameters: {model_params}")

if __name__ == "__main__":
    main()
