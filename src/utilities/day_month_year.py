
def DayMonthYear(month,year):
    year = int(year)
    if month == 2 :
        if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
            return 29
        else:
            return 28
        pass
    if month < 8 :
        if month % 2 == 0 :
            return 30
        else:
            return 31
    else:
        if month % 2 == 0:
            return 31
        else:
            return 30
