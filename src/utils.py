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