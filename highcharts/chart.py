#!/usr/bin/env python
""" PyHighcharts chart.py
A Wrapper around the Highcharts JS objects to dynamically generate
browser enabled charts on the fly.

For Highcharts Licencing Visit: 
http://shop.highsoft.com/highcharts.html
"""
from options import ChartOptions, \
    ColorsOptions, CreditsOptions, ExportingOptions, \
    GlobalOptions, LabelsOptions, LangOptions, \
    LegendOptions, LoadingOptions, NavigationOptions, PaneOptions, \
    PlotOptions, SeriesData, SubtitleOptions, TitleOptions, \
    TooltipOptions, xAxisOptions, yAxisOptions 

from highchart_types import Series, SeriesOptions
from common import Formatter



# Stdlib Imports
import datetime, random, webbrowser, os, inspect

TMP_DIR = "/tmp/highcharts_tmp/"
DEFAULT_HEADERS = """<script type='text/javascript' src=\
'https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js'>\
</script>\n<script src="http://code.highcharts.com/highcharts.js"></script>\n \
<script src="http://code.highcharts.com/modules/exporting.js"></script>"""

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
# Static Vars
BASE_TEMPLATE = ROOT_PATH + "/templates/base.tmp"
SHOW_TEMPLATE = ROOT_PATH + "/templates/show_temp.tmp"
GECKO_TEMPLATE = ROOT_PATH + "/templates/gecko_temp.tmp"
THEMES_JS = ROOT_PATH + "/templates/js/themes/default.js"
CSS = ROOT_PATH + "/templates/css/nature.css"
DEFAULT_POINT_INTERVAL = 86400000

FORMAT_SPECIAL_CASES = {
    "formatter": "formatter",
    "pointStart": "skip_quotes"
}

class HighchartError(Exception):
    """ Highcharts Error Class """
    def __init__(self, *args):
        Exception.__init__(self, *args)
        self.args = args

def color_formatter(data):
    """ Nothing to see here """
    return str(data['colors'])


def update_template(tmp, key, val, tab_depth=1):
    """ Generate Json Dicts """
    if key not in FORMAT_SPECIAL_CASES:
        # Value Checking
        if isinstance(val, dict):
            tmp += "\t%s: {\n" % key
            for subkey, subval in val.items():
                tmp = update_template(tmp, subkey, subval, tab_depth=3)
            tmp += "\t\t" + "},\n"
            return tmp
        elif isinstance(val, bool):
            # Convert Bool to js equiv.
            bool_mapping = {
                False: 'false',
                True: 'true',
            }
            val = bool_mapping[val]
        elif isinstance(val, str):
            # Need to keep string quotes
            val = "\'" + val + "\'"
        tmp += "\t"*tab_depth + "%s: %s,\n" % (key, val)
    else:
        if FORMAT_SPECIAL_CASES[key] == "skip_quotes":
            tmp += "\t"*tab_depth + "%s: %s,\n" % (key, val)
        elif key == "formatter":
            tmp += "\t"*tab_depth + "%s: %s,\n" % (key, val.formatter)
        else:
            raise NotImplementedError
    return tmp

def series_formatter(data):
    """ Special Formatting For Series """
    temp = ""
    for data_set in data['data']:
        temp += "{\n"
        for key, val in  data_set.__dict__.items():
            temp = update_template(temp, key, val, tab_depth=2)
        temp += "\t},"
    return temp


def chart_formatter(option_type, data):
    """ Formatter Function """
    # Special Cases
    special_cases = {
        "colors": color_formatter,
        "series": series_formatter,
    }
    tmp = ""
    #print option_type, 'option_type900000000000990'
    #print data, 'data99999000000000'
    if data == {}:
        #print option_type, 'option_type900000000000990'
        return tmp
    if option_type in special_cases:
        #print special_cases[option_type](data), 'vvvvvvvvvvvvvv'
        tmp += special_cases[option_type](data)
    else:
        for key, val in data.items():
            if isinstance(val, dict):
                tmp += "\t%s: {\n" % key
                for subkey, subval in val.items():
                    tmp = update_template(tmp, subkey, subval, tab_depth=3)
                tmp += "\t\t" + "},\n"
            elif isinstance(val, SeriesOptions):
                tmp += "\t%s: {\n" % key
                for subkey, subval in val.__dict__.items():
                    tmp = update_template(tmp, subkey, subval, tab_depth=3)
                tmp += "\t\t" + "},\n"
            else:
                tmp = update_template(tmp, key, val)
    return tmp



class Highchart(object):
    """ Highchart Wrapper """

    def __init__(self, **kwargs):

        # Default Nulls // ? 
        self.hold_point_start = None
        self.hold_point_interval = None
        self.start_date_set = None

        # Bind Base Classes to self
        self.options = {
            "chart": ChartOptions(),
            "colors": ColorsOptions(),
            "credits": CreditsOptions(),
            "exporting": ExportingOptions(),
            "global": GlobalOptions(),
            "labels": LabelsOptions(),
            "lang": LangOptions(),
            "legend": LegendOptions(),
            "loading": LoadingOptions(),
            "navigation": NavigationOptions(),
            "pane": PaneOptions(),
            "plotOptions": PlotOptions(),
            "series": SeriesData(),
            "subtitle": SubtitleOptions(),
            "title": TitleOptions(),
            "tooltip": TooltipOptions(),
            "xAxis": xAxisOptions(),
            "yAxis": yAxisOptions(),
        }

        self.__load_defaults__()

        # Process kwargs
        allowed_kwargs = ["width", "height", "renderTo", "backgroundColor"]
        
        for keyword in allowed_kwargs:
            if keyword in kwargs:
                self.options['chart'].update_dict(**{keyword:kwargs[keyword]})

        # Some Extra Vals to store: 
        self.data_set_count = 0


    def __render__(self, ret=False, template="base"):
        if template == "base":
            TEMPLATE = BASE_TEMPLATE
        elif template == "gecko":
            TEMPLATE = GECKO_TEMPLATE
        with open(TEMPLATE,"rb") as template_file:
            tmp = template_file.read()
        rendered = tmp.format(**self.__export_options__())
        if ret: 
            return rendered
     


    def __export_options__(self):
        bind = self.options.items()
        m = bind
        # for a, b in m:
        #      print a, 'sssssssssssssswwwwww'
        data = {k:chart_formatter(k, opClass.__dict__) \
            for k, opClass in bind}
        return data


    def __load_defaults__(self):
        self.options["chart"].update_dict(renderTo='container')
        self.options["title"].update_dict(text='A New Highchart')
        self.options["yAxis"].update_dict(title_text='units') 
        self.options["credits"].update_dict(enabled=False)


    def title(self, title=None):
        """ Bind Title """
        if not title:
            return self.options["title"].text
        else:
            self.options["title"].update_dict(text=title)


    def colors(self, colors=None):
        """ Bind Color Array """
        if not colors:
            return self.options["colors"].list()
        else:
            self.options["colors"].set_colors(colors)


    def chart_background(self, background=None):
        """ Apply Chart Background """
        if not background:
            return self.options["chart"].backgroundColor
        else:
            self.options["chart"].update_dict(backgroundColor=background)


    def set_start_date(self, date):
        """ Set Plot Start Date """
        if isinstance(date, (int, float)):
            date = datetime.datetime.fromtimestamp(date)
        elif not isinstance(date, datetime):
            error = "Start Date Format Currently Not Supported: %s" % date
            raise HighchartError(error)
        date_dict = {
            "year": date.year,
            "month": date.month - 1,
            "day": date.day,
            "hour": date.hour,
        }
        formatted_date = "Date.UTC({year}, {month}, {day}, {hour}, 0, 0)"
        formatted_date = formatted_date.format(**date_dict)
        if not self.options['plotOptions'].__dict__: 
            self.hold_point_start = formatted_date
            self.hold_point_interval = DEFAULT_POINT_INTERVAL
        hold_iterable = self.options['plotOptions'].__dict__.items()
        for series_type, series_options in hold_iterable:
            series_options.process_kwargs({'pointStart':formatted_date},
                series_type=series_type)
            if not 'pointInterval' in series_options.__dict__: 
                series_options.process_kwargs({
                    'pointInterval':DEFAULT_POINT_INTERVAL},
                    series_type=series_type,
                    supress_errors=True)
        self.options['tooltip'].update_dict(formatter=Formatter('date'))
        self.options['xAxis'].update_dict(type='datetime')
        self.start_date_set = True


    def set_interval(self, interval):
        """ Set Plot Step Interval """
        if not isinstance(interval, int): 
            raise HighchartError("Interval Value Must Be An Integer")
        # Unset Any Held Values To Avoid Them Overwriting This Value
        if self.hold_point_interval: 
            self.hold_point_interval = None
        if not self.options['plotOptions'].__dict__: 
            self.hold_point_interval = interval
        for hold_item in self.options['plotOptions'].__dict__.items():
            series_type, series_options = hold_item
            series_options.process_kwargs({'pointInterval':interval},
                series_type=series_type)
        if not self.start_date_set:
            print "Set The Start Date With .set_start_date(date)"


    def add_data_set(self, data, series_type="line", name=None, **kwargs):
        """ Update Plot Options With Defaults If None Exist """
        self.data_set_count += 1      
        if not name: 
            name = "Series %d" % self.data_set_count
        kwargs.update({'name':name})
        if self.hold_point_start: 
            kwargs.update({"pointStart":self.hold_point_start})
            self.hold_point_start = None
        if self.hold_point_interval: 
            kwargs.update({"pointInterval":self.hold_point_interval})
            self.hold_point_interval = None
        if series_type not in self.options["plotOptions"].__dict__:
            to_update = {series_type:SeriesOptions(series_type=series_type,
                supress_errors=True, **kwargs)}
            self.options["plotOptions"].update_dict(**to_update)
        series_data = Series(data, series_type=series_type, \
            supress_errors=True, **kwargs)
        #print series_data, 'dataserce99999999'
        self.options["series"].data.append(series_data)


    def set_options(self, options):
        """ Set Plot Options """
        new_options = {}
        for key, option_data in options.items():
            data = {}
            for key2, val in option_data.items():
                if isinstance(val, dict):
                    for key3, val2 in val.items():    
                        data.update({key2+"_"+key3:val2})
                else:   
                    data.update({key2:val})
            new_options.update({key:data})
        for key, val in new_options.items():
            self.options[key].update_dict(**val)


    def show(self):
        """ Show Function """
        
        handle = webbrowser.get()
        if not os.path.exists(TMP_DIR): 
            os.mkdir(TMP_DIR)
        new_filename = "%x.html" % (random.randint(pow(16, 5), pow(16, 6)-1))
        new_fn = TMP_DIR + new_filename
        with open(SHOW_TEMPLATE, 'rb') as file_open:
            tp = file_open.readlines()
        tp.insert(4,'<script type="text/javascript" src=' + THEMES_JS + '></script>\n')
        tp.insert(5,'<link rel="stylesheet" type="text/css" href=' + CSS + '></link>\n')
        tmp = ''
        for tp_str in tp:
            tmp += tp_str  
        html = tmp.format(chart_data=self.__render__(ret=True))
        with open(new_fn, 'wb') as file_open:
            file_open.write(html)
        handle.open("file://"+new_fn)
    

    def generate(self):
        """ __render__ Wrapper """
        return self.__render__(ret=True)


    @staticmethod
    def need():
        """ Returns Header """
        return DEFAULT_HEADERS

