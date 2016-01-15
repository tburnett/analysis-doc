"""
Base class for model analysis

"""

import os, sys, pickle, glob, zipfile, time, re, json
import numpy as np
import pylab as plt
#from mpl_toolkits.axes_grid import axes_grid, axes_size, Divider, make_axes_locatable

from . import _html

class FloatFormat(): #simple formatting functor for to_html!
    def __init__(self, n): self.fmt = '%%.%df' % n
    def __call__(self, x): return self.fmt % x
    
def html_table( df, columns={}, name='temp', heading='', href=True, 
        href_pattern='sedfig/%s_sed*.jpg',
        href_cols=[],
        maxlines=10, **kw):
    """ utility to create and reformat a pandas-generated html table
    df : a DataFrame
    columns : dict
        keys are column names
        items - comma-delimited string, first field the title to use instead of the column name, rest an explanation
    href : bool
         if True, replace index names with link to sedrec
    href_pattern : str
    maxlines : int
        maximum number of lines to return as an HTML table; if length of the table is greater, 
    """
    t = heading+'\n'+df.to_html(**kw)
    t = t.replace('<td><strong>', '<td class="index"><strong>') #what pandas generates for index column
    # this for later version
    t = re.sub(r'<tr>\s*<th>(.+)</th>', lambda x: '<tr>\n\t<th class="index">'+x.group(1)+'</th>', t) 
    
    # modify columns headings: search for each name in the heading dict
    for h, item in columns.items():
        try:
            newhead,title=item.split(',',1)
        except: 
            print '***fail to parse html_table data:',item
            continue
        t = t.replace('>'+h+'<', ' title="%s">%s<'% (title, newhead if newhead!='' else h))
    
    def repit(s, t):
        for n in s:
            fnpat = href_pattern %  n.replace(' ','_').replace('+','p') 
            q = glob.glob(fnpat)
            if len(q) !=1: 
                print '**File %s not found' % fnpat
                continue
            i = t.find(n+'<')
            assert i>0, 'pattern not found for %s' % n
            t = t.replace(n+'<', '<a href="../../%s">%s<' %(q[0],n))
        return t

    if href:
        t =repit( df.index, t)
    for hcol in href_cols:
        t=repit( df[hcol].values, t)
        
    if len(df)<maxlines or name=='temp':
        return t
    # long table: make document and return link to it
    tt = _html.menu_header % dict(name=name)
    filename = name+'.htm'
    open(filename, 'w').write(tt+'\n<body>\n'+t+'\n</body>')
    print 'wrote file %s' % filename
    
    return '<a href="%s?skipDecoration">%s</a>' % ( filename.split('/')[-1], heading)
    

class AnalysisBase(object):
    """ basic class to handle data for diagnostics, collect code to make plots
    """
    def __init__(self, model_dir='.', **kwargs):
        """ model_dir: string
            points to a directory containing a config.json file, and perhaps other files
            
            Creates a folder 'plots' if it does not exist, 
        """
        # setup config dictionary with contents of both ../config.json and config.json
        assert os.path.exists('config.json'), 'File "config.json" no found in folder {}'.format(model_dir)
        self.config=json.load(open('config.json'))
        if os.path.exists('../config.json'):
            self.config.update(json.load(open('../config.json')))
            
        self.model_dir = os.path.expandvars(model_dir)
        if model_dir != '.': os.chdir(self.model_dir)
        self.skymodel = os.path.split(os.getcwd())[-1]
        self.setup(**kwargs)
        if not os.path.exists('plots'):
            os.mkdir('plots')
            print 'created folder "plots"'
        if hasattr(self, 'plotfolder'):
            self.plotfolder = os.path.join('plots', self.plotfolder)
            self.just_created = not os.path.exists(self.plotfolder) 
            if self.just_created:
               os.makedirs(self.plotfolder)
        else:
            raise Exception('Subclass %s of AnalysisBase did not create a "plotfolder" variable' % self.__class__.__name__)

    def setup(self, *args, **kwargs):
        assert False, 'Base class not implemented'
        
    def describe(self):
        return 'no description'
 
    def subplot_array( self, hsize, vsize=(1.0,), figsize=(10,10)):
        """ Use the axes_divider module to make a single row of plots
        hsize : list of floats
            horizontal spacing: alternates Scaled for plot, Fixed for between plots
        vsize : list of floats
            vertical spacing
            
        ref:   http://matplotlib.org/mpl_toolkits/axes_grid/users/axes_divider.html
        """
        nx = (len(hsize)+1)/2
        ny = (len(vsize)+1)/2
        fig, axx = plt.subplots(ny,nx,squeeze=False, figsize=figsize) # just to make the axes, will move them
        sizer = lambda x,i: axes_size.Scaled(x) if i%2==0 else axes_size.Fixed(x)
        horiz = [ sizer(h,i) for i,h in enumerate(hsize) ]
        vert  = [ sizer(v,i) for i,v in enumerate(vsize) ]
        divider = Divider(fig, (0.1, 0.1, 0.8, 0.8), horiz, vert, aspect=False)
        for i,ax in enumerate(axx.flatten()):
            iy = i//nx; ix = i%nx
            ax.set_axes_locator(divider.new_locator(nx=2*ix, ny=2*iy))
        return fig, axx
        
    def savefigure(self, name, func=None, title=None, caption=None, section='', ft='jpg', **kwargs):
        """ save a figure.
        name : string
            If name is the name of a function in the class, optionally define 
                the title as the first line, the caption the following lines
        func : executable function, or None
            if not None, run the func, use it to get docs
            If func creates a figure, it must return it
        Note that the docstring may have %(xxx)s, which will be replaced by attribute xxx.
        """
        if func is not None:
            fname = func.__name__
            try:
                fig=func(**kwargs)
            except Exception, msg:
                print '*** Failed to run function %s: "%s"' % (fname, msg)
                return '<h3>%s %s</h3> Failed to run function %s: "%s"' % (section, title, fname, msg)
        else: fname = name
        if hasattr(self, fname):
            try:
                doclines = ((eval('self.%s' % fname).__doc__%self.__dict__).split('\n'))
                doclines.append('')
                if caption is None:   caption = '\n<p>'+'\n'.join(doclines[1:])+'</p>\n'
                if title is None:     title = doclines[0]
            except Exception, msg:
                print '*** docstring processing problem: %s' % msg
        localfile = '%s_%s.%s' % (name, self.skymodel.replace('/','_'), ft)
        savefile = os.path.join(self.plotfolder,localfile)
        if title is None: title = name.replace('_', ' ')
        htmldoc = '<a id="%.0f"><h3>%s %s</h3></a> ' % (float(section), section, title)
        self.htmlmenu.item('<a href="index.html?skipDecoration#%.0f">%s</a>' % (float(section),title))
        if fig is not None:
            fig.set_facecolor('white') # important for copy and paste to Evernote
            fig.text(0.02, 0.02, self.skymodel, fontsize=8)
            savefig_kw=dict(dpi=60, bbox_inches='tight', bbox_extra_artists=fig.texts, pad_inches=0.5) 
            print 'Saving fig %s, ...' % (name, ),; sys.stdout.flush()
            plt.savefig(savefile, **savefig_kw)
            print 'to %s' % savefile
            htmldoc += '\n<img src="%s" />\n <br> %s '% (localfile, caption if caption is not None else '')
        elif caption is not None:
            htmldoc += '\n <br>  %s' % ( caption )
        return htmldoc

    def runfigures(self, functions, names=None,  **kwargs):
        """ 
        run the functions, create a web page containing them, and a menu file

        functions: list of bound functions 
        names: optional set of names to use instad of function names
        
        Expect to be called from all_plots, get a summary from its docstring if present, or the class docstring
        """
        if names is None:
            names=[None]*len(functions)
        class_name = self.__class__.__name__
        title = self.skymodel +'-'+class_name
        htmldoc = _html.header(title)
        htmldoc +='<body><h2>%(bodyhead)s</h2>'
        
        # start the menu
        self.htmlmenu = _html.DDmenu(name=self.plotfolder.split(os.sep)[-1], depth=4 )
        classdoc = self.__class__.__doc__
        headstring = classdoc.split('\n')[0] if classdoc is not None else ''
        if headstring=='': headstring = class_name
        self.htmlmenu.folder(id, href='index.html?skipDecoration', text=headstring, id=class_name)
 
        docstring = self.all_plots.__doc__
        if docstring is None: docstring = self.__doc__
        if docstring is not None: htmldoc+=docstring
        section = 0
        for function, name in zip(functions,names):
            section +=1
            fname = name if name is not None else function.__name__
            #htmlmenu.item('<a href="index.html#%d">%s</a>' % (section,fname))
            fig = self.savefigure(fname, function, section='%d.'%section, **kwargs)
            if fig is not None:
                htmldoc+='\n'+ fig
        htmldoc+= '\n<hr>\nPage generated %4d-%02d-%02d %02d:%02d:%02d on %s by %s'\
                % (tuple(time.localtime()[:6])+
                 (os.environ.get('HOSTNAME',os.environ.get('COMPUTERNAME','?')),
                  os.environ.get('USER',os.environ.get('USERNAME','?'))))
        htmldoc+='\n</body>'
        self.htmlmenu.save(os.path.join(self.plotfolder,'menu.html'))
        print 'saved local menu to %s' % os.path.join(self.plotfolder,'menu.html')
        
        t = os.getcwd().split(os.path.sep)[-3:]
        m = '<a href="../index.html?skipDecoration">%s</a>' % t[-1] # model name has uplink
        r = '<a href="../../../plot_index.html?skipDecoration">%s</a>' % t[-2] # to group of models 
        self.bodyhead='/'.join([r, m, os.path.split(self.plotfolder)[-1]])
        
        text= htmldoc
        try:
            text = htmldoc%self.__dict__
        except KeyError, msg:
            print '*** failed header generation %s- missing key: %s' % (title, msg)
        except TypeError, msg:
            print '*** TypeError with string "%s": %s' % (htmldoc, msg)
        open(os.path.join(self.plotfolder,'index.html'), 'w').write(text)
        print 'saved html doc to %s' %os.path.join(self.plotfolder,'index.html')
        h = _html.HTMLindex()
        h.create_menu()
        if self.just_created:
           h.update_top()
           
