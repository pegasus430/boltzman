import datetime
import uuid
import time

class AITimeGenerator:
    def __init__(self,  initial_time = datetime.datetime.now().timestamp(), time_step = 15 * 60, anchor_to_real_time = False, logger = None):
        """Generates fake or real time

        Args:
            initial_time (int), optional):beginning of the time. Defaults to now. 
            time_step (_type_, optional): time increment value, default is 15 minutes (15 * 60)
            anchor_to_real_time (bool, optional): if set true generated time returns current time - (initial current time - initial time)
                                                if not set it increments the the time with timestep with no delay.
                                            
        """  
        self.current_time = int(initial_time)
        self.initial_time = int(initial_time)
        self.time_step = int(time_step)
        self.delta = datetime.datetime.now().timestamp() - initial_time
        self.anchored = anchor_to_real_time
        self.logger = logger
        self.id = uuid.uuid4()
        self._delay = 0

    def is_simulation(self):
        return not (self.anchored == True and self.delta > 0)
    
    def set_delay(self, new_delay):
        self._delay = new_delay

    def get_delay(self):
        return self._delay

    delay = property(get_delay, set_delay)

    def get_current_time (self):
        if (self.delay > 0):
            time.sleep(self.delay)

        if (self.anchored):
            self.current_time = datetime.datetime.timestamp((datetime.datetime.now() - datetime.timedelta(seconds=self.delta)))
        else:
            self.current_time = self.current_time + self.time_step     
        return self.current_time