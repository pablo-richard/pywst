# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np

class WST:
    """
    Wavelet Scattering Transform (WST) class contains the output of the WST of an image or a batch of images.
    This contains the corresponding coefficients and helps to handle and to plot these coefficients.
    """
    
    def __init__ (self, J, L, coeffs, index = None, cplx = False):
        """
        

        Parameters
        ----------
        J : int
            Number of dyadic scales.
        L : int
            Number of angles between 0 and pi.
        coeffs : array
            WST coefficients. 1D, 2D, 3D, 4D arrays are valid depending whether
            we have local coefficients or not, whether we are dealing with the WST
            of a batch of images or not.
        index : array, optional
            Index of the coefficients stored in coeffs. The default is None.
        cplx : bool, optional
            Are these coefficients computed from complex images? The default is False.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.J = J
        self.L = L
        self.cplx = cplx
        
        # Number of coefficients
        self.nbM0 = 1
        self.nbM1 = J * L * (1 + cplx)
        self.nbM2 = J * (J - 1) * L * L * (1 + cplx) // 2
        
        self.coeffs = coeffs
        self.coeffsCov = None
        
        # Check if we are dealing with a batch of images coefficients or not, and if we have local coefficients or not.
        if coeffs.ndim == 1:
            self.batch = False; self.local = False
        elif coeffs.ndim == 2:
            self.batch = True; self.local = False
        elif coeffs.ndim == 3:
            self.batch = False; self.local = True
        elif coeffs.ndim == 4:
            self.batch = True; self.local = True
        else:
            raise Exception ("Bad input shape.")
        
        # Reordering and definition of the current index
        if index is not None:
            self.reorder (index)
        self.index = np.zeros ((5, self.nbM0 + self.nbM1 + self.nbM2))
        cnt = 1
        for j1 in range (J):
            for theta1 in range (L * (1 + cplx)):
                self.index [:, cnt] = [1, j1, theta1, 0, 0]
                cnt += 1
        for j1 in range (J):
            for theta1 in range (L * (1 + cplx)):
                for j2 in range (j1 + 1, J):
                    for theta2 in range (L):
                        self.index [:, cnt] = [2, j1, theta1, j2, theta2]
                        cnt += 1
                        
        # Normalization initialization
        self.normalized = False
        self.log2Vals = False
        
        # Plot design parameters
        self._xticks, self._xticksMinor, self._xticklabels, self._xticklabelsMinor, self._tickAlignment = [], [], [], [], []
        cnt = 1
        for j1 in range (J):
            self._xticks.append (cnt + L * (1 + cplx) // 2) # Tick at the middle
            self._xticklabels.append ("$j_1 = " + str (j1) + "$")
            self._tickAlignment.append (0.0)
            cnt += L * (1 + cplx)
        for j1 in range (J - 1):
            for theta1 in range (L * (1 + cplx)):
                for j2 in range (j1 + 1, J):
                    self._xticksMinor.append (cnt + L // 2)
                    self._xticklabelsMinor.append ("$j_2 = " + str (j2) + "$")
                    self._tickAlignment.append (-0.1)
                    cnt += L
            self._xticks.append (cnt - L * L * (1 + cplx) * (J - j1 - 1) // 2)
            self._xticklabels.append ("$j_1 = " + str (j1) + "$")
            self._tickAlignment.append (0.0)
                
    def reorder (self, index):
        """
        Reorder coefficients (self.coeffs) to the standard lexicographical order (j1, theta1, j2, theta2) (ScatNet order).
        Index parameter specifies the current order.

        Parameters
        ----------
        index : array
            DESCRIPTION.

        Returns
        -------
        None.

        """
        coeffsCopy = self.coeffs.copy ()
        
        # Lexicographical order
        reorderIndex = np.lexsort (index [::-1, :])

        # Reorder
        for i in range (coeffsCopy.shape [0]):
            self.coeffs [i, ...] = coeffsCopy [reorderIndex [i], ...]
                
    def _filterArgs (self, **kwargs):
        filtering = np.ones (self.index.shape [1], np.bool)
        for key, value in kwargs.items ():
            if key == "layer":
                filtering = np.logical_and (filtering, self.index [0] == value)
            elif key == "j1":
                filtering = np.logical_and (filtering, self.index [1] == value)
            elif key == "theta1":
                filtering = np.logical_and (filtering, self.index [2] == value)
            elif key == "j2":
                filtering = np.logical_and (filtering, self.index [3] == value)
            elif key == "theta2":
                filtering = np.logical_and (filtering, self.index [4] == value)
        return filtering
            
    def getCoeffs (self, **kwargs):
        """
        Return the selected coefficients.

        Parameters
        ----------
        layer : int, optional
            Selection of the layer of coefficients (0, 1 or 2). The default is all layers.
        j1 : int, optional
            Selection of a specific j_1 values. The default is all j_1 values.
        theta1 : int, optional
            Selection of a specific theta_1 values. The default is all theta_1 values.
        j2 : int, optional
            Selection of a specific j_2 values. The default is all j_2 values.
        theta2 : int, optional
            Selection of a specific theta_2 values. The default is all theta_2 values.        

        Returns
        -------
        array
            Array of the coefficients.
        array
            Index of the coefficients.

        """
        filtering = self._filterArgs (**kwargs)
        return self.coeffs [filtering, ...], self.index [:, filtering]
        
    def normalize (self, log2 = True):
        if self.coeffsCov is not None:
            print ("Warning! The covariance matrix has been computed before the normalization and will not be updated.")
        
        if not self.normalized:
            coeffsCopy = self.coeffs.copy ()
            cnt = 1
            for j1 in range (self.J):
                self.coeffs [cnt:cnt + self.L * (1 + self.cplx), ...] /= coeffsCopy [:1, ...]
                cnt += self.L * (1 + self.cplx)
            for j1 in range (self.J):
                for theta1 in range (self.L * (1 + self.cplx)):
                    index = 1 + j1 * self.L * (1 + self.cplx) + theta1
                    self.coeffs [cnt:cnt + self.L * (self.J - j1 - 1), ...] /= coeffsCopy [index:index + 1, ...]
                    cnt += self.L * (self.J - j1 - 1)
            self.normalized = True
        
        if not self.log2Vals:
            if log2:
                self.coeffs = np.log2 (self.coeffs)
                self.log2Vals = True
                
    def average (self):
        if self.batch or self.local: # We need multiple samples to average
            coeffsCopy = self.coeffs.copy ()
            coeffsCopy = coeffsCopy.reshape ((coeffsCopy.shape [0], -1))
            coeffsCov = np.cov (coeffsCopy) / coeffsCopy.shape [-1]
            
            self.coeffs = coeffsCopy.mean (axis = -1)
            self.coeffsCov = coeffsCov
            self.coeffsCovNbSamples = coeffsCopy.shape [-1] # Keep in memory the number of samples used to compute the sample covariance matrix.
            
            self.batch = False
            self.local = False
        
    def getCoeffsCov (self, autoRemoveOffDiagonalCoeffs = True, **args):
        filtering = self._filterArgs (**args)
        if self.coeffsCov is None:
            print ("Warning! Covariance matrix is None.")
            return np.eye (np.sum (filtering)), self.index [:, filtering]
        else:
            dim = np.sum (filtering)
            covM = self.coeffsCov [np.outer (filtering, filtering)].reshape (dim, dim)
            # If demanded, remove off diagonal coefficients when we have too few samples to get a definite sample covariance matrix.
            if self.coeffsCovNbSamples < dim + 1 and autoRemoveOffDiagonalCoeffs: # We typically expect definite sample covariance matrix when coeffsCovNbSamples >= dim + 1.
                print ("Warning! Removing off diagonal coefficients of the sample covariance matrix (only " + str (self.coeffsCovNbSamples) + " samples for dimension " + str (dim) + ").")
                covM = np.diag (np.diag (covM))
            return covM, self.index [:, filtering]
        
    def _plot (self, axis, x, y, ylabel, legend = "", err = None, j1Ticks = True):
        # Plot
        axis.plot (x, y, '-',  markersize = 2, label = legend)
        if err is not None:
            axis.fill_between (x, y - err, y + err, alpha = 0.2)
        
        # Ticks and grid parameters
        axis.set_ylabel (ylabel)
        if j1Ticks:
            axis.set_xticks (self._xticks)
            axis.set_xticklabels (self._xticklabels)
        else:
            axis.set_xticks ([])
            axis.set_xticklabels ([], visible = False)
        axis.set_xticks (self._xticksMinor, minor = True)
        axis.set_xticklabels (self._xticklabelsMinor, minor = True)
        for t, y in zip (axis.get_xticklabels (), self._tickAlignment):
            t.set_y (y)
        axis.grid (False, axis = 'x')
        axis.grid (False, axis = 'x', which = 'minor')
        axis.tick_params (axis = 'x', which = 'minor', direction = 'out', length = 5)
        axis.tick_params (axis = 'x', which = 'major', bottom = False, top = False)
        axis.set_xlim (x.min () - 1, x.max () + 1)
        axis.margins (0.2)
        
        # Plot separators
        cnt = 1
        for j1 in range (self.J):
            axis.axvline (cnt, color = 'black', alpha = 0.5, linestyle = 'dashed')
            cnt += self.L * (1 + self.cplx)
        for j1 in range (self.J):
            axis.axvline (cnt, color = 'black', alpha = 0.5, linestyle = 'dashed')
            for theta1 in range (self.L * (1 + self.cplx)):
                if theta1 >= 1:
                    axis.axvline (cnt, color = 'black', alpha = 0.2, linestyle = 'dashed')
                for j2 in range (j1 + 1, self.J):
                    if j2 > j1 + 1:
                        axis.axvline (cnt, color = 'black', alpha = 0.1, linestyle = ':')
                    cnt += self.L
        axis.axvline (cnt, color = 'black', alpha = 0.5, linestyle = 'dashed')
            
        if legend != "":
            axis.legend ()
        
    def plot (self, layer = None, j1 = None, title = "WST"):
        xValues = np.array (range (self.nbM0 + self.nbM1 + self.nbM2))

        locShape = self.coeffs.shape [1:]
   
        if layer is None or layer == 1:
            if j1 is None:
                xSelection = self._filterArgs (layer = 1)
            else:
                xSelection = self._filterArgs (layer = 1, j1 = j1)
                
            # ylabel design
            ylabel = "$" + self.log2Vals * "\log_2(" + self.normalized * "\widebar{" + "S" + self.normalized * "}" + "_1" + self.log2Vals * ")" + "$"
            
            fig = plt.figure ()
            ax = fig.add_subplot (1,1,1)
            for locIndex in np.ndindex (locShape):
                coeffs = self.coeffs [tuple ([xSelection]) + locIndex]
                if self.coeffsCov is None:
                    coeffsErr = None
                else:
                    coeffsErr = np.sqrt (self.coeffsCov.diagonal ()[tuple ([xSelection]) + locIndex])
                self._plot (ax, xValues [xSelection], coeffs, ylabel, legend = locIndex, err = coeffsErr)
            plt.subplots_adjust (bottom = 0.2)
            plt.title (title + " - m = 1")
            plt.show ()
        if layer is None or layer == 2:
            if j1 is None:
                xSelection = self._filterArgs (layer = 2)
            else:
                xSelection = self._filterArgs (layer = 2, j1 = j1)
            # ylabel design
            ylabel = "$" + self.log2Vals * "\log_2(" + self.normalized * "\widebar{" + "S" + self.normalized * "}" + "_2" + self.log2Vals * ")" + "$"
            
            fig = plt.figure (figsize = (30, 5))
            ax = fig.add_subplot (1,1,1)
            for locIndex in np.ndindex (locShape):
                coeffs = self.coeffs [tuple ([xSelection]) + locIndex]
                if self.coeffsCov is None:
                    coeffsErr = None
                else:
                    coeffsErr = np.sqrt (self.coeffsCov.diagonal ()[tuple ([xSelection]) + locIndex])
                self._plot (ax, xValues [xSelection], coeffs, ylabel, legend = locIndex, err = coeffsErr)
            plt.subplots_adjust (bottom = 0.2)
            plt.title (title + " - m = 2")
            plt.tight_layout (rect=[0, 0.03, 1, 0.95])
            plt.show ()
