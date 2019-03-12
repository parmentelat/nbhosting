from collections import OrderedDict
from datetime import datetime, timedelta

class TimeBuckets:
    """
    we want to show how nbstudents_per_notebook makes progress over time

    so the basic logic would be
    * create object with a grain value (the duration of each time bucket)
    * call snapshot(date, data)
    * that would magically recall the state of <data> at the end of each period

    except that this 'data' business is a mutable and is altered as we go
    so we would need to copy it, but we can't afford to copy it each time
    so instead we'd rather do

    data = some_mutable()
    tb = TimeBuckets(grain=timedelta(hours=4))
    for date in events:
       previous, next, need_store = tb.prepare(date)
       if need_store:
          tb.record_data(copy(data), previous, next)
       change(data)
    tb.wrap(copy(data))
    
    """

    epoch = datetime(year=2017, month=1, day=1)

    def __init__(self, grain: timedelta, time_format):
        self.grain = grain
        self.time_format = time_format
        # hash grain_index (quotient of time / grain)
        # into whatever data is provided to snapshot
        self.hash = OrderedDict()
        # n-th grain from the epoch
        self.quotient = 0

    def prepare(self, date):
        dt = datetime.strptime(date, self.time_format)
        # bucket indices are quotients
        next = ((dt-self.epoch) // self.grain)
        need_store = self.quotient and self.quotient != next
        retcod = self.quotient, next, need_store
        if not self.quotient:
            self.quotient = next
        return retcod

    # next is optional at wrap-time
    def record_data(self, data, previous, next=None):
        # copy is up to the caller if needed
        self.hash[previous] = data
        if next:
            self.quotient = next

    def _make_readable(self):
        """
        rewrite all keys into actual dates
        use END of period as the key
        """
        def reverse_date(quotient):
            dt = self.epoch + (quotient+1) * self.grain
            return dt.strftime(self.time_format)
        self.readable = OrderedDict()
        for q, v in self.hash.items():
            self.readable[reverse_date(q)] = v
        return self.readable

    def wrap(self, data):
        self.record_data(data, self.quotient)
        return self._make_readable()
        

if __name__ == '__main__':
    tb = TimeBuckets(grain = timedelta(hours=1), time_format="%Y-%m-%dT%H:%M:%S")
    events = [
        "2017-11-06T09:00:09 1",
        "2017-11-06T09:59:58 2",
        "2017-11-06T10:00:09 3",
        "2017-11-06T10:59:58 4",
        "2017-11-06T11:00:09 5",
        "2017-11-06T11:59:58 6",
        "2017-11-06T12:00:09 7",
        "2017-11-06T12:59:58 8",
        ]
    l = []
    for event in events:
        date, nb = event.split()
        previous, next, changed = tb.prepare(date)
        if changed:
            tb.record_data(l[:], previous, next)
        l.append(nb)
    result = tb.wrap(l[:])
    for k, v in result.items():
        print(k, v)


