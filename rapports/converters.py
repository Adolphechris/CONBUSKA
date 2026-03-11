import datetime


class DateConverter:
    regex = r'\d{4}/\d{1,2}/\d{1,2}'
    format = '%Y/%m/%d'

    def to_python(self, value):
        return datetime.datetime.strptime(value, self.format).date()

    def to_url(self, value):
        return value.strftime(self.format)


class DateRangeConverter:
    regex = '\d{1,2}/\d{1,2}/\d{4} - \d{1,2}/\d{1,2}/\d{4}'
    format = '%m/%d/%Y %H:%M:%S'

    def to_python(self, value):
        date_range = value.split('-')
        time_debut = "00:00:01"
        time_fin = "23:59:59"
        date1 = datetime.datetime.strptime(str(date_range[0].strip()) + ' ' + time_debut, self.format)
        date2 = datetime.datetime.strptime(str(date_range[1].strip()) + ' ' + time_fin, self.format)
        return date1, date2

    def to_url(self, value):
        return value