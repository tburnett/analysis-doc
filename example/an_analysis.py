"""
"""
import  pickle
from analysis_base import analysis_base
import pylab as plt
import numpy as np
from scipy import stats

class Demo(analysis_base.AnalysisBase):
    """Demo analysis
    This class docstring is used to annotate the document.
    <br>The offset for this analysis is %(offset)s.
    """

    def setup(self, **kw):
        self.plotfolder='demo' # where to save documents
        dataset = self.config['dataset']
        self.data = pickle.load(open(dataset))
        self.offset = self.config['offset']

    def plot_hist(self):
        """A simple plot, with caption
        Histogram of data, and an overlay that depends on the model
        """
        fig, ax = plt.subplots( figsize=(4,4))
        # generate the histogram
        bins = np.linspace(-4,4,41); binsize= bins[1]-bins[0]
        ax.hist(self.data, bins=bins, histtype='step', label='data')
        #overplot a Gaussian, offset by the "offset" paramet
        c = len(self.data)*binsize
        x = np.linspace(-4,4,100)
        ax.plot(x, stats.norm.pdf(x-self.offset)*c, 
            color='red', label='plot')
        
        ax.legend(); ax.grid()
        return fig

    def text(self):
        """Some text
        Showing how to add text, just the function docstring.
        This turns into HTML. <br> %(test)s
        """
        self.test = 'The offset used for the overplot is {}'.\
            format(self.offset)
        
    def all_plots(self):
        # specify the functions of this class that will be used 
        # to generate output for the document
        self.runfigures([self.plot_hist, self.text,])
        