import matplotlib
import matplotlib.colors
import matplotlib.image
import matplotlib.ticker
import re
import copy
import numpy
import math
import matplotlib.pyplot
import matplotlib.cm
import time

#Some of this code is pinched from Overview/DQMGui plotting

def text_size(string,fontsize,dpi=72):
    return 0.6*len(string)*(dpi/72.)*fontsize,1.4*(dpi/72.)*fontsize

class ElementBase:
    def __init__(self,element_name,element_type=None,allow_missing=True,default=None):
        self.element_name = element_name
        self.element_type = element_type
        self.allow_missing = allow_missing
        self.default = default
    def validate(self,input):
        if self.element_name in input:
            if not self.element_type==None:
                if not isinstance(input[self.element_name],self.element_type):
                    return False
            return self._validate(input)
        elif self.allow_missing:
            return True
        else:
            return False
    def _validate(self,input):
        return True
    def extract(self,input):
        if self.element_name in input:
            return input[self.element_name]
        else:
            return self.default

class ColourBase(ElementBase):
    def __init__(self,element_name,default='black'): #any colour you want, providing it's...
        ElementBase.__init__(self,element_name,(str,unicode),True,default)
    def extract(self,input):
        if self.element_name in input:
            c = input[self.element_name]
            match = re.match('^#?([0-9A-Fa-f]{6})$',c) 
            if match:
                return '#%s'%match.group(1)
            elif c in matplotlib.colors.cnames:
                return c
            else:
                return self.default
        else:
            return self.default
       
class IntBase(ElementBase):
    def __init__(self,element_name,min=None,max=None,allow_missing=True,default=None):
        ElementBase.__init__(self,element_name,(int,float),allow_missing,default)
        self.min = min
        self.max = max
    def extract(self,input):
        if self.element_name in input:
            val = int(input[self.element_name])
            if (not self.min==None) and val<self.min:
                val = self.min
            if (not self.max==None) and val>self.max:
                val = self.max
            return val
        else:
            return self.default
        
class FloatBase(ElementBase):
    def __init__(self,element_name,min=None,max=None,allow_missing=True,default=None):
        ElementBase.__init__(self,element_name,(int,float),allow_missing,default)
        self.min = min
        self.max = max
    def extract(self,input):
        if self.element_name in input:
            val = float(input[self.element_name])
            if (not self.min==None) and val<self.min:
                val = self.min
            if (not self.max==None) and val>self.max:
                val = self.max
            return val
        else:
            return self.default
            
class StringBase(ElementBase):
    def __init__(self,element_name,options=None,default=None):
        ElementBase.__init__(self,element_name,(str,unicode),True,default)
        self.options = options
    def extract(self,input):
        if self.element_name in input:
            val = input[self.element_name]
            if (not self.options==None) and (not val in self.options):
                val = self.default
            return val
        else:
            return self.default
        
class FontFamily(StringBase):
    def __init__(self,element_name,default='serif'):
        StringBase.__init__(self,element_name,('serif','sans-serif','monospace'),default)
        
class FontWeight(StringBase):
    def __init__(self,element_name,default='normal'):
        StringBase.__init__(self,element_name,('light','normal','bold'),default)

class ColourMap(StringBase):
    def __init__(self,element_name,default='Accent'):
        ElementBase.__init__(self,element_name,(str,unicode),True,default)
    def extract(self,input):
        if self.element_name in input:
            val = input[self.element_name]
            if matplotlib.cm.get_cmap(val):
                return matplotlib.cm.get_cmap(val)
        return matplotlib.cm.get_cmap(self.default)
               
class FontSize(ElementBase):
    def __init__(self,element_name,default=None):
        ElementBase.__init__(self,element_name,(str,unicode,int),True,default)
    def extract(self,input):
        if self.element_name in input:
            val = input[self.element_name]
            if isinstance(val,int):
                if not (val>0 and val<100):
                    val = self.default
            else:
                if not (val in ('xx-small','x-small','small','medium','large','x-large','xx-large')):
                    val = self.default
            return val
        else:
            return self.default        
        
class ListElementBase(ElementBase):
    def __init__(self,element_name,list_element_type=None,item_validator=None,min_elements=None,max_elements=None,allow_missing=True,default=None):
        ElementBase.__init__(self,element_name,(list,tuple),allow_missing,copy.deepcopy(default))
        self.list_element_type=list_element_type
        self.min_elements = min_elements
        self.max_elements = max_elements
        self.item_validator = item_validator
        if self.item_validator:
            self.item_validator.element_name = 'listitem'
    def validate(self,input):
        if ElementBase.validate(self,input):
            if not self.list_element_type==None:
                if not all([isinstance(item,self.list_element_type) for item in input[self.element_name]]):
                    return False
            if not self.item_validator==None:
                if not all([self.item_validator.validate({'listitem':item}) for item in input[self.element_name]]):
                    return False
            if not self.min_elements==None:
                if len(input[self.element_name])<self.min_elements:
                    return False
            if not self.max_elements==None:
                if len(input[self.element_name])>self.max_elements:
                    return False
            return True
        else:
            return False
    def extract(self,input):
        if self.element_name in input:
            if not self.item_validator==None:
                return [self.item_validator.extract({'listitem':item}) for item in input[self.element_name]]
            else:
                return input[self.element_name]
        else:
            return self.default
        
class DictElementBase(ElementBase):
    def __init__(self,element_name,allow_missing=True,validate_elements=None):
        ElementBase.__init__(self,element_name,dict,allow_missing,None)
        if validate_elements==None:
            self.validate_elements = []
        else:
            self.validate_elements = validate_elements
    def validate(self,input):
        if ElementBase.validate(self,input):
            val = input.get(self.element_name,{})
            for v in self.validate_elements:
                if not v.validate(val):
                    return False
            return True
        else:
            return False
    def extract(self,input):
        if self.element_name in input:
            return dict([(v.element_name,v.extract(input[self.element_name])) for v in self.validate_elements])
        else:
            return dict([(v.element_name,v.extract({})) for v in self.validate_elements])
        
def ThousandWrap(f,char=','):
    re_thousands = re.compile(r'(\d)(\d{3}($|\D))')
    replace = r'\1'+char+r'\2'
    def _inner(*args,**kwargs):
        s = f(*args,**kwargs)
        while True:
            r = re_thousands.sub(replace,s)
            if r==s:
                return r
            else:
                s = r
        return s
    return _inner

def UnitWrap(f,unit):
    def _inner(*args,**kwargs):
        return f(*args,**kwargs)+unit
    return _inner

class TimeFormatter(matplotlib.ticker.ScalarFormatter):
    formats = ((0,'%M:%S'),
               (60,'%H:%M'),
               (3600,'%a %H:%M'),
               (86400,'%m %d'),
               (604800, '%b %d'),
               (2419200,'%d %b %Y'),
               (31557600,'%b %Y'),
               (315576000,'%Y'))
    def __init__(self,span=3600):
        self.span = span
    def __call__(self,val,pos=None):
        t = time.localtime(val)
        for f in formats:
            if f[0]>=self.span:
                return time.strftime(f[1],t)
                
            

class SuffixFormatter(matplotlib.ticker.ScalarFormatter):
    suffix = [(1,'')]
    def __call__(self,val,pos=None):
        for s in self.suffix:
            if abs(val)>=100.*s[0]:
                return "%.0f%s"%(val/s[0],s[1])
            if abs(val)>=10.*s[0]:
                return "%.1f%s"%(val/s[0],s[1])
            if abs(val)>=1.*s[0]:
                return "%.2f%s"%(val/s[0],s[1])
        return str(val)

class LongSIFormatter(SuffixFormatter):
    suffix = [(1e18,'exa'),(1e15,'peta'),(1e12,'tera'),(1e9,'giga'),(1e6,'mega'),(1e3,'kilo'),(1,''),(1e-3,'mili'),(1e-6,'micro'),(1e-9,'nano'),(1e-12,'pico'),(1e-15,'femto'),(1e-18,'atto')]

class SIFormatter(SuffixFormatter):
    suffix = [(1e18,'E'),(1e15,'P'),(1e12,'T'),(1e9,'G'),(1e6,'M'),(1e3,'k'),(1,''),(1e-3,'m'),(1e-6,'u'),(1e-9,'n'),(1e-12,'p'),(1e-15,'f'),(1e-18,'a')] 
        
class LongBinFormatter(SuffixFormatter):
    suffix = [(2.**60,'exa'),(2.**50,'peta'),(2.**40,'tera'),(2.**30,'giga'),(2.**20,'mega'),(2.**10,'kilo'),(1,'')]

class BinFormatter(SuffixFormatter):
    suffix = [(2.**60,'E'),(2.**50,'P'),(2.**40,'T'),(2.**30,'G'),(2.**20,'M'),(2.**10,'k'),(1,'')]

class BinaryMaxNLocator(matplotlib.ticker.MaxNLocator):
    def bin_boundaries(self,vmin,vmax):
        scales = (1.,1.5,2.,2.5,3.,4.,5.,6.,8.,10.)
        
        delta = abs(vmax-vmin)
        mean = vmin + 0.5*(vmax-vmin)
        
        bar_width = float(delta)/self._nbins
        bar_magnitude = int(math.log(bar_width,2))
        
        possible = [s*2.**bar_magnitude for s in scales]
        
        best_delta = max(scales)*2.**bar_magnitude
        
        bin_width = 0
        for p in possible:
            if abs(p-bar_width)<best_delta:
                best_delta = abs(p-bar_width)
                bin_width = p
        
        offset = int(vmin/bin_width)
        if vmin<0:
            offset -= 1
        val = offset*bin_width
        result = []
        while val<vmax+bin_width:
            result += [val]
            val += bin_width
        return result
        
class Mixin(object):
    def validate(self,input):
        return True
    def extract(self,input):
        pass
    def construct(self,*args,**kwargs):
        pass
    def predata(self,*args,**kwargs):
        pass
    def data(self,*args,**kwargs):
        pass
    def postdata(self,*args,**kwargs):
        pass
    def finalise(self,*args,**kwargs):
        pass

class FigureMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [IntBase('height',min=1,max=5000,default=600),
                           IntBase('width',min=1,max=5000,default=800),
                           FloatBase('dpi',min=1,max=300,default=96.)] 
        super(FigureMixin,self).__init__(*args,**kwargs)
    #def _apply(self,figure):
    #    return matplotlib.pyplot.figure(figsize=(self.props['width']/self.props['dpi'],self.props['height']/self.props['dpi']),dpi=self.props['dpi'])
    def construct(self,*args,**kwargs):
        self.figure = matplotlib.pyplot.figure(figsize=(self.props.width/self.props.dpi,self.props.height/self.props.dpi),
                                               dpi=self.props.dpi)
        super(FigureMixin,self).construct(*args,**kwargs)

class TitleMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [ElementBase('notitle',bool,default=False),
                  ElementBase('title',(str,unicode),default=''),
                  FontSize('title_size',default=14),
                  FontSize('subtitle_size',default=12),
                  FontWeight('title_weight',default='bold'),
                  FontWeight('subtitle_weight',default='normal'),
                  FontFamily('title_font',default='serif'),
                  FontFamily('subtitle_font',default='serif'),
                  ColourBase('title_colour',default='black'),
                  ColourBase('subtitle_colour',default='black'),
                  IntBase('padding',min=0,default=40),
                  IntBase('linepadding',min=0,default=10)]    
        super(TitleMixin,self).__init__(*args,**kwargs)
    def construct(self,*args,**kwargs):
        self.props.topbound = self.props.height-self.props.padding
        if not self.props.notitle:
            title = self.props.title.split('\n')
            
            tx,ty = text_size(title[0],self.props.title_size,self.props.dpi)
            h = self.props.height
            ch = h-self.props.linepadding
            self.figure.text(0.5,(ch-(ty*0.5))/h,title[0],
                        color=self.props.title_colour,
                        family=self.props.title_font,
                        weight=self.props.title_weight,
                        size=self.props.title_size,
                        ha='center',
                        va='center')
            ch -= ty
            ch -= self.props.linepadding
            
            for subtitle in title[1:]:
                tx,ty = text_size(subtitle,self.props.subtitle_size,self.props.dpi)
                self.figure.text(0.5,(ch-(ty*0.5))/h,
                            subtitle,color=self.props.subtitle_colour,
                            family=self.props.subtitle_font,
                            weight=self.props.subtitle_weight,
                            size=self.props.subtitle_size,
                            ha='center',
                            va='center')
                ch -= ty
                ch -= self.props.linepadding
                
            self.props.topbound = ch
        super(TitleMixin,self).construct(*args,**kwargs)
    
        

class FigAxesMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [StringBase('projection',('aitoff','hammer','lambert','mollweide','polar'),'rectilinear'),
                  ElementBase('square',bool,default=False),
                  IntBase('padding',min=0,default=40)]    
        super(FigAxesMixin,self).__init__(*args,**kwargs)
    def construct(self,*args,**kwargs):
        w,h = self.props.width,self.props.height
        topbound = self.props.get('topbound',h)
        padding = self.props.padding
        square = self.props.square
        projection = self.props.projection
        if h-topbound<padding:
            topbound = h-padding
        
        avail_width = w - 2*padding
        avail_height = topbound - padding
        
        if square:
            max_dim = min(avail_width,avail_height)
            left = 0.5*w - 0.5*max_dim
            bottom = 0.5*topbound - 0.5*max_dim
            self.figure.add_axes((float(left)/w,float(bottom)/h,float(max_dim)/w,float(max_dim)/h),projection=projection)
        else:
            self.figure.add_axes((float(padding)/w,float(padding)/h,float(avail_width)/w,float(avail_height)/h),projection=projection)
        super(FigAxesMixin,self).construct(*args,**kwargs)
        
class StyleMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [ColourBase('background',default=None),
                  ColourMap('colourmap',default=None),
                  ElementBase('gridlines',bool,default=True)]
        super(StyleMixin,self).__init__(*args,**kwargs)    
    def construct(self,*args,**kwargs):
        if not self.props.background==None:
            self.figure.set_facecolor(self.props.background)
        if self.props.gridlines:
            self.figure.gca().grid()
        super(StyleMixin,self).construct(*args,**kwargs)



class NumericAxisMixin(Mixin):    
    def __init__(self,*args,**kwargs):
        self.validators += [DictElementBase(self.axis,True,[StringBase('label',None,default=''),
                                                     FloatBase('min',default=None),
                                                     FloatBase('max',default=None),
                                                     ElementBase('log',bool,default=False),
                                                     FloatBase('logbase',min=1,default=10),
                                                     StringBase('logerror',('mask','clip'),default='clip'),
                                                     StringBase('timeformat',None,default=None),
                                                     StringBase('format',('num','time','binary','si'),default='num')])]
        super(NumericAxisMixin,self).__init__(*args,**kwargs)
    def validate(self,input):
        return super(NumericAxisMixin,self).validate(input)
    def predata(self,*args,**kwargs):
        axes = self.figure.gca()
        axis = getattr(axes,self.axis)
        data = self.props.get(self.axis)
        
        if data['format']=='si':
            axis.set_major_formatter(SIFormatter())
        elif data['format']=='time':
            if not data['timeformat']==None:
                axis.set_major_formatter(TimeFormatter(data['timeformat']))
            else:
                axis.set_major_formatter(TimeFormatter())
            axis.set_major_locator(TimeLocator())
        elif data['format']=='binary':
            axis.set_major_formatter(BinFormatter())
            axis.set_major_locator(BinaryMaxNLocator())
        
        axis.set_label(data['label'])
        
        if data['log']:
            axis.set_scale('log',base=data['logbase'],nonpos=data['logerror'])
            setattr(self.props,self.axis+'_log',True)
        else:
            setattr(self.props,self.axis+'_log',False)
        super(NumericAxisMixin,self).predata(*args,**kwargs)
    
    def postdata(self,*args,**kwargs):
        axes = self.figure.gca()
        axis = getattr(axes,self.axis)
        data = self.props.get(self.axis)
        
        if data['min'] or data['max']:
            axis.set_view_interval(data['min'],data['max'])
        
        super(NumericAxisMixin,self).postdata(*args,**kwargs)
        
class XNumericAxisMixin(NumericAxisMixin):
    axis='xaxis'
class YNumericAxisMixin(NumericAxisMixin):
    axis='yaxis'
        
class BinnedNumericAxisMixin(NumericAxisMixin):
    def __init__(self,*args,**kwargs):
        self.validators += [DictElementBase(self.axis,False,[FloatBase('min',default=0),
                                                     FloatBase('max',default=1),
                                                     FloatBase('width',min=0,default=1)])]
        super(BinnedNumericAxisMixin,self).__init__(*args,**kwargs)
    def validate(self,input):
        return super(BinnedNumericAxisMixin,self).validate(input)
    def predata(self,*args,**kwargs):
        data = self.props.get(self.axis)
        if data['log']:
            if not (data['min']>0 and data['max']>0):
                data['bins'] = 0
                data['edges'] = (0,0)
            else:
                data['bins'] = int(abs(math.log(data['min'],data['logbase'])-math.log(data['max'],data['logbase']))/data['width'])
                data['edges'] = [data['logbase']**(math.log(data['min'],data['logbase'])+i*data['width']) for i in range(data['bins']+1)]    
        else:
            data['bins'] = int(float(data['max']-data['min'])/data['width'])
            data['edges'] = [data['min']+data['width']*i for i in range(data['bins']+1)]
        
        super(BinnedNumericAxisMixin,self).predata(*args,**kwargs)

class XBinnedNumericAxisMixin(BinnedNumericAxisMixin):
    axis='xaxis'
class YBinnedNumericAxisMixin(BinnedNumericAxisMixin):
    axis='yaxis'          
        
class LabelledAxisMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [DictElementBase(self.axis,False,[StringBase('label',None,default=''),
                                                     ListElementBase('labels',(str,unicode),min=1,default=('default',))])]
        super(LabelledAxisMixin,self).__init__(*args,**kwargs)   
    def predata(self,*args,**kwargs):
        axes = figure.gca()
        axis = getattr(axes,self.axis)
        data = self.props.get(self.axis)
        
        axis.set_label(data['label'])
        axis.set_ticklabels(data['labels'])
        axis.set_ticks([i+0.5 for i in range(len(axis['labels']))])
        
        data['bins'] = len(data['labels'])
        data['edges'] = range(len(data['labels'])+1)
        
        super(LabelledAxisMixin,self).predata(*args,**kwargs)

class XLabelledAxisMixin(LabelledAxisMixin):
    axis='xaxis'
class YLabelledAxisMixin(LabelledAxisMixin):
    axis='yaxis'
        
class AutoLabelledAxisMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [DictElementBase(self.axis,True,[StringBase('label',None,default='')])]
        super(AutoLabelledAxisMixin,self).__init__(*args,**kwargs)

class XAutoLabelledAxisMixin(AutoLabelledAxisMixin):
    axis='xaxis'
class YAutoLabelledAxisMixin(AutoLabelledAxisMixin):
    axis='yaxis'
            

class NumericSeriesMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [ListElementBase('series',dict,DictElementBase('listitem',False,[StringBase('label',None,default=''),ListElementBase('values',(int,float),allow_missing=False),ColourBase('colour',default=None)]),allow_missing=False)]
        super(NumericSeriesMixin,self).__init__(*args,**kwargs)
    def data(self,*args,**kwargs):
        cmap = self.props.colourmap
        xbins = self.props.xaxis['bins']
        for i,series in enumerate(self.props.series):
            if series['colour']==None:
                series['colour']=cmap(float(i)/len(self.props['series']))
            if len(series['values'])>xbins:
                self.props.series[i]['values'] = series['values'][:xbins]
            elif len(series['values'])<xbins:
                self.props.series[i]['values'] = series['values'] + [0]*xbins-len(series['values'])
            series['min'] = min(series['values'])
            series['max'] = max(series['values'])
        super(NumericSeriesMixin,self).data(*args,**kwargs)
    
class LabelledSeriesMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [ListElementBase('series',dict,DictElementBase('listitem',False,[StringBase('label',None,default=''),FloatBase('value',allow_missing=False),ColourBase('colour',default=None),ElementBase('explode',(int,float),default=0)]),allow_missing=False)]
        super(LabelledSeriesMixin,self).__init__(*args,**kwargs)
    def data(self,*args,**kwargs):
        cmap = self.props.colourmap
        for i,series in enumerate(self.props.series):
            if series['colour']==None:
                series['colour']=cmap(float(i)/len(self.props.series))
        super(LabelledSeriesMixin,self).data(*args,**kwargs)
        
class DataMixin(Mixin):
    def __init__(self,*args,**kwargs):
        self.validators += [ListElementBase('data',(list,tuple),ListElementBase('listitem',(int,float),FloatBase('listitem',min=0.,max=1.),allow_missing=False),allow_missing=False)]
        super(DataMixin,self).__init__(*args,**kwargs)
    def validate(self,input):
        lengths = set([len(line) for lin in self.props.data])
        if not len(lengths)==1:
            return False
        return super(DataMixin,self).validate(input)
            
    
class CleanLogSeries:
    def __init__(self,series):
        self.series = series
        self.min = min(series)
        self.max = max(series)
        self.positive = filter(lambda x: x>0,series)
        if len(self.positive)>0:
            self.minpos = min(self.positive)
            self.maxpos = max(self.positive)
        else:
            self.minpos = None
            self.maxpos = None
    def remove_negative(self):
        result = []
        for i in self.series:
            if i<0:
                result += [0]
            else:
                result += [i]
        return result
    def remove_negorzero(self,replace):
        result = []
    def roundmin(self):
        if self.minpos:
            return 10**(int(math.log10(self.minpos)))
        else:
            return None
    def roundmax(self):
        if self.maxpos:
            l = math.log10(self.maxpos)
            if abs(int(l)-l)<0.001:
                return 10**l
            else:
                return 10**(l+1)
        else:
            return None
             
    
    
        
    
        
