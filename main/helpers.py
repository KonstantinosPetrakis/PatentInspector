from __future__ import unicode_literals
from django.db import models
from django.db.models import Aggregate, FloatField, IntegerField, Func


class Median(Aggregate):
    function = 'PERCENTILE_CONT'
    name = 'median'
    output_field = FloatField()
    template = '%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)'


class WordCount(Func):
    function = 'CHAR_LENGTH'
    name = 'word_count'
    template = "(%(function)s(%(expressions)s) - CHAR_LENGTH(REPLACE(%(expressions)s, ' ', '')))"
    output_field = IntegerField()



class Datediff(models.Func):
    """
    Returns the date difference of two database fields, using the database's own arithmatic.
    
    Ever been annoyed at the inconsistent implementation of calculating date differences in databases?
    Well this solves that problem. 
    
    Example usage in Django:
        
        articles = Articles.objects.filter(author=my_user)
        articles = articles.annotate(revision_time=Datediff('date_published','date_started', interval='days')) #Assumes your Articles model has fields "date_started" and "date_published"
        
    @author: Dr Michael J T Brooks
    @contact: michael [dot] brooks [at] patientsource.co.uk
    @license: MIT (software supplied AS IS. Use at your own risk. Leave these credentials in place.)
    @version: 20160504 (May the forth be with you)
    
    """
    function = '' #We ignore the function property
    interval = 'dd'
    param_order = ("date_end", "date_start") #Which order do these appear in our template (necessary to ensure correct order of params passed down to cursor.execute)

    def __init__(self, *expressions, **extra):
        """
        Initialise the Datediff abstraction ORM function
            
            @param expressions[0]: The "to" date
            @param expressions[1]: The "from" date
            @keyword interval: A string representing the units you want the result in (see SUPPORTED_INTERVALS, below)
                
        """
        SUPPORTED_INTERVALS = """
        
                "years" / "year" / "yy"                          Years
                "months" / "month" / "mm"                        Months
                "days" / "day" / "dd"                            Days  [default]
                "weeks" / "week" / "wk"                          Weeks
                "hours" / "hour" / "hr" / "hh"                   Hours
                "minutes" / "minute" / "mins" / "min" / "mi"     Minutes
                "seconds" / "second" / "secs" / "sec" / "ss"     Seconds
                
        """
        interval = str(extra.get('interval','dd')).lower() #Default to days
        #Now standardise & sanitise interval:
        if interval in ("years", "year", "yy"):
            interval = "yy"
        elif interval in ("months", "month", "mm"):
            interval = "mm"
        elif interval in ("days", "day", "dd"):
            interval = "dd"
        elif interval in ("weeks", "week", "wk"):
            interval = "wk"
        elif interval in ("hours", "hour", "hr", "hh"):
            interval = "hh"
        elif interval in ("minutes", "minute", "mins", "min", "mi"):
            interval = "mi"
        elif interval in ("seconds", "second", "secs", "sec", "ss"):
            interval = "ss"
        else:
            raise ValueError('Datediff() interval "{0}" is not supported! Supported intervals are: {1}'.format(interval, SUPPORTED_INTERVALS))
        self.interval = interval
        #Sanitise date expressions
        if len(expressions) != 2:
            raise ValueError('Datediff must take two expressions corresponding to the dates to calculate the difference between')
        # The parent init method takes all *expressions, assumes strings are column names, and parses them into a list, which gets put into self.source_expressions
        super(Datediff, self).__init__(output_field=models.IntegerField(), *expressions, **extra)
        #Something funny happens to self.source_expressions between here and self.as_sql to inflate them into proper SQL
    
    def as_sql(self, compiler, connection, function=None, template=None):
        """
        Complete override to ensure that our compiled date_end and date_start get flushed into as_sql
        """
        connection.ops.check_expression_support(self)
        params = []
        date_start_sql, date_start_params = compiler.compile(self.source_expressions[1]) #self.source_expressions has now been inflated to a SQL string unlike in init
        date_end_sql, date_end_params = compiler.compile(self.source_expressions[0])
        self.extra['date_start'] = date_start_sql #This simply puts the SQL for date_start into the template, but with %s as params
        self.extra['date_end'] = date_end_sql
        #To prevent SQLinjection, we must pass user derived values in to cursor.execute as a positional list. We cannot use premature string substitution
        #The problem, is that the position of date_end and date_start varies depending on the database and interval we are using!!! Thus we use param_order to say what order to stick our params in  
        params_dict = {
                        'date_start':date_start_params,
                        'date_end':date_end_params
                       } #Used to lookup params
        for params_for in self.param_order:
            params.extend(params_dict[params_for]) #Extend our list of params in the order date_start and date_end appear
        #
        template = template or self.extra.get('template', self.template)
        return ((template % self.extra), params) #Returns a tuple of (SQL statement without values, list of params to substitute in)
    
    def as_mysql(self, compiler, connection):
        """
        MySQL (and derivatives e.g. MariaDB) have a range of functions for the various intervals plus one standard function
        for the lot: TIMESTAMPDIFF(interval, date2, date1). The key thing to note is that the dates are in the inverse order
        compared to DATEDIFF... yes I've got no idea why either! 
        
            Years:     TIMESTAMPDIFF(YEAR,datestart,dateend) 
            Months:    TIMESTAMPDIFF(MONTH,datestart,dateend)
            Days:      TIMESTAMPDIFF(DAY,datestart,dateend)
            Weeks:     TIMESTAMPDIFF(WEEK,datestart,dateend)
            Hour:      TIMESTAMPDIFF(HOUR,datestart,dateend)
            Minute:    TIMESTAMPDIFF(MINUTE,datestart,dateend)
            Second:    TIMESTAMPDIFF(SECOND,datestart,dateend)
        """
        interval_expression = "DAY" #Default to no multiplication
        if self.interval == "yy":
            interval_expression = "YEAR"
        elif self.interval == "mm":
            interval_expression = "MONTH"
        elif self.interval == "dd":
            interval_expression = "DAY"
        elif self.interval == "wk":
            interval_expression = "WEEK"
        elif self.interval == "hh":
            interval_expression = "HOUR"
        elif self.interval == "mi":
            interval_expression = "MINUTE"
        elif self.interval == "ss":
            interval_expression = "SECOND"
        #
        self.template = 'TRUNCATE(TIMESTAMPDIFF(%(interval_expression)s,%(date_start)s,%(date_end)s),0)' #The ,0 at the end tells TRUNCATE to round to integers
        self.extra["interval_expression"] = interval_expression 
        self.param_order = ("date_start", "date_end")
        #Now we can call the standard as_sql to build the statement with these new values
        return self.as_sql(compiler, connection) 
    
    def as_postgresql(self, compiler, connection):
        """
        PostgreSQL doesn't provide Datediff. Instead it can subtract dates directly, with the ability to return the difference
        in any denominator you ask for (days, months, years etc)
            Years:    DATE_PART('year', end) - DATE_PART('year', start)
            Months:   years_diff * 12 + (DATE_PART('month', end) - DATE_PART('month', start))
            Days:     DATE_PART('day', end - start)
            Weeks:    TRUNC(DATE_PART('day', end - start)/7)
            Hours:    days_diff * 24 + DATE_PART('hour', end - start )
            Minutes:  hours_diff * 60 + DATE_PART('minute', end - start )
            Seconds:  minutes_diff * 60 + DATE_PART('minute', end - start )
            
            @todo: Cast values which are very obviously string dates into PostgreSQL date syntax: e.g. ('2016-05-04'::date) 
        """
        if self.interval == "yy":
            template = "DATE_PART('year', %(date_end)s) - DATE_PART('year', %(date_start)s)" 
        elif self.interval == "mm":
            template = "years_diff * 12 + (DATE_PART('month', %(date_end)s) - DATE_PART('month', %(date_start)s))"
        elif self.interval == "dd":
            template = "DATE_PART('day', %(date_end)s - %(date_start)s)"
        elif self.interval == "wk":
            template = "TRUNC(DATE_PART('day', %(date_end)s - %(date_start)s)/7)"
        elif self.interval == "hh":
            template = "days_diff * 24 + DATE_PART('hour', %(date_end)s - %(date_start)s)"
        elif self.interval == "mi":
            template = "hours_diff * 60 + DATE_PART('minute', %(date_end)s - %(date_start)s)"
        elif self.interval == "ss":
            template = "minutes_diff * 60 + DATE_PART('minute', %(date_end)s - %(date_start)s)"
        self.template = template
        self.param_order = ("date_end", "date_start")
        return self.as_sql(compiler, connection)
    
    def as_oracle(self, compiler, connection):
        """
        Oracle's (eye-wateringly overpriced*) database permits subtraction of two dates directly, so long as they are cast
        appropriately:
            
            Years:     TRUNC(MONTHS_BETWEEN(date_end, date_start) / 12)
            Months:    MONTHS_BETWEEN(date_end, date_start)
            Days:      TRUNC(date_end - date_start)
            Weeks:     TRUNC((date_end - date_start)/7)
            Hours:     TRUNC((date_end - date_start)*24)
            Minutes:   TRUNC((date_end - date_start)*24*60)
            Seconds:   TRUNC((date_end - date_start)*24*60*60)
            
            NB: We use TRUNC as it always rounds towards zero, thus important for negative date periods
        
            @todo: Cast date string values into native Oracle date types: e.g TO_DATE('2000-01-02', 'YYYY-MM-DD')
        
            *seriously, why are you using this database?! I recommend switching to PostgreSQL. That'll save yourself some
            licence fee money and you won't have to untangle Oracle's multitude of different licenses nightmare. If it's 
            about "support", then PostgreSQL has plenty of third party companies offering support contracts.  
        """
        if self.interval == "yy":
            template = "TRUNC(MONTHS_BETWEEN(%(date_end)s, %(date_start)s) / 12)" 
        elif self.interval == "mm":
            template = "MONTHS_BETWEEN(%(date_end)s, %(date_start)s)"
        elif self.interval == "dd":
            template = "TRUNC(%(date_end)s - %(date_start)s)"
        elif self.interval == "wk":
            template = "TRUNC((%(date_end)s - %(date_start)s)/7)"
        elif self.interval == "hh":
            template = "TRUNC((%(date_end)s - %(date_start)s)*24)"
        elif self.interval == "mi":
            template = "TRUNC((%(date_end)s - %(date_start)s)*24*60)"
        elif self.interval == "ss":
            template = "TRUNC((%(date_end)s - %(date_start)s)*24*60*60)"
        self.template = template
        self.param_order = ("date_end", "date_start")
        return self.as_sql(compiler, connection)

    def as_sqlite(self, compiler, connection):
        """
        SQLite doesn't carry a DateDiff equivalent. Instead, it allows subtraction between date fields so 
        long as they are casted into dates with juliandate()
            Years: (this is an approximation as we don't know exactly WHEN the leap years will fall)
                Select Cast (
                    (JulianDay(SecondDate) - JulianDay(FirstDate)) / 365.242
                ) As Integer
            
            Months: (this is a crude approximation)
                Select Cast (
                    (JulianDay(SecondDate) - JulianDay(FirstDate)) / 30
                ) As Integer
            Weeks:
                Select Cast (
                    (JulianDay(SecondDate) - JulianDay(FirstDate)) / 7
                ) As Integer
        
            Days:
                Select Cast (
                    JulianDay(SecondDate) - JulianDay(FirstDate)
                ) As Integer
        
            Hours:
                Select Cast (
                    (JulianDay(SecondDate) - JulianDay(FirstDate)) * 24
                ) As Integer
            Minutes:
                Select Cast (
                    (JulianDay(SecondDate) - JulianDay(FirstDate)) * 24 * 60
                ) As Integer
                
            Seconds:
                Select Cast (
                    (JulianDay(SecondDate) - JulianDay(FirstDate)) * 24 * 60 * 60
                ) As Integer
        """
        multiplier_expression = "" #Default to no multiplication
        if self.interval == "yy":
            multiplier_expression = " / 365.242"
        elif self.interval == "mm":
            multiplier_expression = " / 30"
        elif self.interval == "dd":
            multiplier_expression = ""
        elif self.interval == "wk":
            multiplier_expression = " / 7"
        elif self.interval == "hh":
            multiplier_expression = " * 24"
        elif self.interval == "mi":
            multiplier_expression = " * 24 * 60"
        elif self.interval == "ss":
            multiplier_expression = " * 24 * 60"
        #
        self.template = 'Cast((JulianDay(%(date_end)s) - JulianDay(%(date_start)s))%(multiplier_expression)s) AS INTEGER' #Must use the old modulus substitution syntax to work with Django's ORM methods
        self.extra["date_start"] = self.source_expressions[1] #The second argument
        self.extra["date_end"] = self.source_expressions[0] #The first argument
        self.extra["multiplier_expression"] = multiplier_expression #Adds this extra keyword
        self.param_order = ("date_end", "date_start")
        #Now we can call the standard as_sql to build the statement with these new values
        return self.as_sql(compiler, connection) 
        