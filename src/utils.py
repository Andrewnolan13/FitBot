import time
import numpy as np

class LinearRegression:
    def __init__(self, X: np.ndarray, y: np.ndarray):
        '''
        Parameters:
            X: np.ndarray
            y: np.ndarray
        Methods:
            fit -> None
            predict -> np.ndarray
        '''
        # Add intercept (bias) term
        self.X = np.hstack((np.ones((X.shape[0], 1)), X))
        self.y = y

    def fit(self) -> None:
        self.beta = np.linalg.inv(self.X.T @ self.X) @ self.X.T @ self.y

    def predict(self, X: np.ndarray) -> np.ndarray:
        # Add intercept (bias) term to input for predictions
        X = np.hstack((np.ones((X.shape[0], 1)), X))
        return X @ self.beta
    

def sleep(s:int)->None:
    '''
    This is interuptable
    '''
    t=0
    while t < s:
        time.sleep(1)
        t += 1

import psutil
import os

def get_python_image_name():
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            # Check if the process name contains 'python'
            if "python" in proc.info["name"].lower():
                return proc.info["name"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

# image_name = get_python_image_name()

def kill_python_processes():
    image_name = get_python_image_name()
    cmd = "taskkill /im {} /f".format(image_name)
    os.system(cmd)