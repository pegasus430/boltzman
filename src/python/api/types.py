import enum


class AIServiceNotificationType(enum.Enum):
    Ping = 0
    Shutdown = 1
    Dispatch_Network = 2
    ParkNetwork = 3
    SpinService = 4
    GetLocalServiceList = 5
