import sys
import os

# Voeg de hoofdmap (Airline_planning) toe aan sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test of het werkt
from utils.file_utils import load_excel
from utils.distance_calculations import calculate_distance
