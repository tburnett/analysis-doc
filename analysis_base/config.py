"""
Configuration information


"""

import os, glob
import numpy as np
import pylab as plt

from . import analysis_base


class Configuration(analysis_base.AnalysisBase):
    """Configuration information
    """

    def setup(self,**kw):
        self.plotfolder='config'
        
    def make_config(self):
        """Configuration and log files from the processing of this model
        %(html)s
        """
        self.html =''
        config_files = glob.glob('../*.json') + glob.glob('*.json') + glob.glob('*.txt')
        for filename in config_files:
            if not os.path.exists(filename): continue
            self.html += '<h4>{}</h4>\n<pre>{}</pre>'.format(filename, open(filename).read())
        return None

    def all_plots(self):
        self.runfigures([self.make_config,])
