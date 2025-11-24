import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from multiprocessing import Pool
from scipy.stats import t
from tqdm import tqdm

class FracND:
    class Worker:
        def __call__(self, window):
            window = window.squeeze()
            # Transform window to binary
            binary_window = np.where(window > 0, 1, 0)
            # Calculate whether the window is empty
            touched = 1 - np.all(binary_window == 0).astype(int)

            # Calculate the mass within the window
            mass = np.sum(window).astype(float)

            return touched, mass


    def __init__(self, max_box_size = None, min_box_size = 1, stride = 1, n_samples = 20, subsample = None, multiprocess = True, **kwargs):
        self.max_box_size = max_box_size
        self.min_box_size = min_box_size
        self.stride = stride
        if self.stride is None:
            print("Setting the step size to None will result in using normal box counting instead of sliding window box counting.")
        self.n_samples = n_samples
        self.subsample = subsample
        if subsample is not None:
            print("Subsampling is enabled. This will result in decreased accuracy.")
        self.multiprocess = multiprocess
        if not multiprocess:
            print("Multiprocessing is disabled. This will result in drastically slower calculations.")
        self.kwargs = kwargs
        if 'histogram' in self.kwargs:
            self.histogram = self.kwargs['histogram']
            if 'bins' in self.kwargs:
                self.bins = self.kwargs['bins']
            else:
                self.bins = 'auto'
        else:
            self.histogram = False


    def sliding_window_statistics(self, input_array, window_size, step_size):
        # Get the shape of the input array
        shape = input_array.shape

        # Calculate the number of windows in each dimension
        window_counts = [int((shape[i] - window_size) / step_size) + 1 for i in range(len(shape))]
        box_window_counts = [int((shape[i] - window_size) / window_size) + 1 for i in range(len(shape))]

        # Calculate the normalization factor
        if self.subsample is None:
            norm = np.prod(box_window_counts)/(np.prod(window_counts))
        else:
            # TODO: This is not a good approximation, look for a better one!
            norm = np.prod(box_window_counts)/(np.prod(window_counts)*self.subsample)

        # Declare the helper function to calculate the statistics for a single window
        window_func = self.Worker()

        # Create a pool of workers
        if self.multiprocess:
            pool = Pool()

        # Iterate over the windows
        res = []
        for index in np.ndindex(*window_counts):
            # Optional subsampling
            # Note, this will result in decreased accuracy
            if self.subsample is not None:
                smpl = np.random.binomial(1, self.subsample)
                # If the sample is 0, skip this window, speeding up the calculation
                if smpl == 0:
                    continue
            # Calculate the start and end indices of the window in each dimension
            start = [i * step_size for i in index]
            end = [i + window_size for i in start]
            # Extract the window from the input array
            window = input_array[tuple(map(slice, start, end))]
            # Apply the window function to the window and store the result
            if self.multiprocess:
                res.append(pool.apply_async(window_func, (window,)))
            else:
                res.append(window_func(window))

        # Close the pool and wait for all tasks to complete
        if self.multiprocess:
            pool.close()
            pool.join()
        # Get the results from the pool
        results = [r.get() for r in res]

        # split the results into touched, mass and lacunarity
        touched, mass = zip(*results)

        # Calculate the N from touched
        N = np.sum(touched)
        N = int(N * norm)

        mass = np.array(mass)
        mass /= np.sum(touched)
        if self.histogram:
            p,bins = np.histogram(mass, bins = self.bins, density=False)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            bin_centers = bin_centers[p != 0]
            p = p[p != 0]
            p = p.astype(float)
            p /= np.sum(p)
        else:
            # If histogram is not enabled, use the unique values of mass as the bins
            bin_centers, p = np.unique(mass, return_counts=True)
            bin_centers = bin_centers[p != 0]
            p = p[p != 0]
            p = p.astype(float)
            p /= np.sum(p)

        mean = np.sum(p*bin_centers)
        var = np.sum(p*(bin_centers - mean)**2)
        lacunarity = var/mean**2 + 1

        return N, lacunarity


    def linear_fit(self, scales, vals, invert_scales = True):
        scales = np.array([np.min(scales[vals == v]) for v in np.unique(vals)])
        vals = np.unique(vals)
        vals = vals[vals > 0]
        scales = scales[:len(vals)]
        if invert_scales:
            scales = 1/scales
        popt, pcov = np.polyfit(np.log(scales), np.log(vals), 1, cov=True)
        return popt, pcov


    def __call__(self,input_array):
        # TODO: Normalize the input array to [0,1] if it is not already
        # Check that the input array is empty
        if np.all(input_array == 0):
            raise ValueError("The input array is empty. Please provide a non-empty array.")
        # Determine the scales to measure on
        if self.max_box_size is None:
            # Default max size is the largest power of 2 that fits in the smallest dimension of the array:
            self.max_box_size = int(np.floor(np.log2(np.min(input_array.shape))))
        self.scales = np.floor(np.logspace(self.max_box_size, self.min_box_size, num=self.n_samples, base=2))
        self.scales = np.unique(self.scales)  # Remove duplicates that could occur as a result of the floor
        # Count the number of boxes touched
        self.Ns = []
        self.lacunarity_spectrum = []

        # Loop over all scales
        for scale in tqdm(self.scales):
            if self.stride is None:
                # Revert to box counting if stride is not specified
                step_size = int(scale)
            else:
                step_size = int(self.stride)
            N, lacunarity = self.sliding_window_statistics(input_array, int(scale), step_size)
            self.Ns.append(N)
            self.lacunarity_spectrum.append(lacunarity)

        self.Ns = np.array(self.Ns)
        self.lacunarity_spectrum = np.array(self.lacunarity_spectrum)

        # Fit the FD
        self.popt, self.pcov = self.linear_fit(self.scales, self.Ns)
        self.FD = self.popt[0]
        # Fit the lacunarity spectrum
        self.ls_popt, self.ls_pcov = self.linear_fit(self.scales, self.lacunarity_spectrum, invert_scales=False)
        self.LD = self.ls_popt[0]


    def lacunarity_statistics(self):
        return np.min(self.lacunarity_spectrum), np.max(self.lacunarity_spectrum), np.mean(self.lacunarity_spectrum), np.std(self.lacunarity_spectrum)


    def plot_FD(self, ci=95, show_plot = True, filename=None):
        scales = np.array([np.min(self.scales[self.Ns == x]) for x in np.unique(self.Ns)])
        Ns = np.unique(self.Ns)
        #Ns = Ns[Ns > 0]
        #scales = scales[:len(Ns)]
        # Calculate the confidence intervals
        slope_err, intercept_err = np.sqrt(np.diag(self.pcov))
        alpha = 1 - ci / 100
        t_value = t.ppf(1 - alpha / 2, df=len(scales) - 2)
        slope_err *= t_value
        intercept_err *= t_value
        fig, ax = plt.subplots(figsize = (8,6))
        sns.regplot(x=np.log(1/scales), y=np.log(Ns), ci=ci,
                    line_kws={'color': 'black', 'linestyle': '--', 'label': "y={0:.3f}±{1:.3f}x+{2:.3f}±{3:.3f}".format(self.popt[0], slope_err, self.popt[1], intercept_err)},
                    scatter_kws={'color': 'teal', 'label': 'Measured ratios'},
                    ax=ax)
        ax.scatter(np.log(1/scales), np.log(Ns), c = "teal", label = "Measured ratios")
        ax.set_ylabel("$\log N(\epsilon)$")
        ax.set_xlabel("$\log 1/ \epsilon$")
        plt.grid(True)
        ax.legend()
        if show_plot:
            plt.show()
        if filename is not None:
            plt.savefig(filename)
        if show_plot == False and filename is None:
            plt.close()


    def plot_lacunarity(self, ci = 95, show_plot = True, filename=None):
        scales = np.array([np.min(self.scales[self.lacunarity_spectrum == x]) for x in np.unique(self.lacunarity_spectrum)])
        lacunarity_spectrum = np.unique(self.lacunarity_spectrum)
        lacunarity_spectrum = lacunarity_spectrum[lacunarity_spectrum > 0]
        scales = scales[:len(lacunarity_spectrum)]
        # Calculate the confidence intervals
        slope_err, intercept_err = np.sqrt(np.diag(self.pcov))
        alpha = 1 - ci / 100
        t_value = t.ppf(1 - alpha / 2, df=len(scales) - 2)
        slope_err *= t_value
        intercept_err *= t_value
        fig, ax = plt.subplots(figsize = (8,6))
        sns.regplot(x=np.log(scales), y=np.log(lacunarity_spectrum), ci=ci,
                    line_kws={'color': 'black', 'linestyle': '--', 'label': "y={0:.3f}±{1:.3f}x+{2:.3f}±{3:.3f}".format(self.ls_popt[0], slope_err, self.ls_popt[1], intercept_err)},
                    scatter_kws={'color': 'teal', 'label': 'Measured ratios'},
                    ax=ax)
        ax.scatter(np.log(scales), np.log(lacunarity_spectrum), c = "teal", label = "Lacunarity")
        ax.set_ylabel("$\log \lambda(\epsilon)$")
        ax.set_xlabel("$\log \epsilon$")
        plt.grid(True)
        plt.legend()
        if show_plot:
            plt.show()
        if filename is not None:
            plt.savefig(filename)
        if show_plot == False and filename is None:
            plt.close()


def greyscale_to_binary(array, levels = 255):
    """
    Converts a greyscale image to a binary image by adding a new dimension to the array
    :param array:
    :param levels:
    :return:
    """
    array = (array - np.min(array)) / (np.max(array) - np.min(array))
    array = (array * levels).astype(int)

    array_shape = array.shape
    max_pixel_value = np.max(array)

    # Calculate the new shape for the binary array
    binary_shape = array_shape + (max_pixel_value + 1,)

    # Create a binary array with the new shape
    binary_array = np.zeros(binary_shape, dtype=np.uint8)

    # Set the corresponding element to 1 based on the pixel value in the original image
    indices = np.indices(array_shape)
    indices_flat = indices.reshape(len(array_shape), -1)

    pixel_values = array[tuple(indices_flat)]
    binary_indices = tuple(np.concatenate((indices_flat, pixel_values[np.newaxis]), axis=0))
    binary_array[binary_indices] = 1

    return binary_array


def crop_segmentation(array, return_indices = False):
    '''
    Crop a segmentation to the smallest possible size.
    :param array:
    :param return_indices:
    :return:
    '''
    # Get the indices of non-zero elements
    nonzero = np.nonzero(array)
    # Get the minimum and maximum indices in each dimension
    minima = np.min(nonzero, axis=1)
    maxima = np.max(nonzero, axis=1) + 1  # We add 1 because Python slices are exclusive at the top
    cropped_array = array[minima[0]:maxima[0], minima[1]:maxima[1], minima[2]:maxima[2]]
    if return_indices:
        return cropped_array, minima, maxima
    else:
        return cropped_array


def crop_image(array, minima, maxima):
    '''
    Crop an image to the specified minima and maxima obtained from crop_segmentation
    :param array:
    :param minima:
    :param maxima:
    :return:
    '''
    cropped_array = array[minima[0]:maxima[0], minima[1]:maxima[1], minima[2]:maxima[2]]
    return cropped_array

