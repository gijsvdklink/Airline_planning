import pandas as pd

def load_excel(file_path, **kwargs):
    """
    Laad een Excel-bestand en geef extra parameters door aan pandas.read_excel.
    """
    return pd.read_excel(file_path, **kwargs)
