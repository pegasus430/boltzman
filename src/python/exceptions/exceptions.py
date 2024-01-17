class ExposedException(Exception):
    pass 


class NetworkLayerMismatch(Exception):
    pass 

class TrainerBeginTimeError(Exception):
    pass 

class NetworkDataportError(Exception):
    pass 

class DataportInputOutputTypeMismatch(Exception):
    pass 

class SymbolNotFound(Exception):
    pass

class TrainerDispatcherError(Exception):
    pass    

class NetworkInvalidRecordToDelete(Exception):
    pass    

class NetworkInputSizeDataMismatch(Exception):
    pass    

class PredictionDataMismatch(Exception):
    pass    

class PredictionAlreadyExists(Exception):
    pass    

class MaximumPredictionExceeded(Exception):
    pass    

class NoIexData(Exception):
    pass        

class MaintananceTestFailure(Exception):
    pass        

class MissingServiceIdEnvVariable(Exception):
    pass


class AssertionError(Exception):
    pass        

class MissingPythonPathEnvVariable(Exception):
    pass

class NetworkIsNotFound(Exception):
    pass 

class NotificationTypeIsNotSupported(Exception):
    pass 

class MultipleRecordsRetuened(Exception):
    pass        

class DataIntegrityCompromised(Exception):
    pass        

class RecordNotFound(Exception):
    pass        


#exceptions exposed to front end
class ServiceImageIsNotFound(ExposedException):
    pass        

class ServiceContainerNotFound(ExposedException):
    pass        

class AuthorizationError(ExposedException):
    pass        

class AuthorizationTokenNotFound(ExposedException):
    pass        

class AuthorizationTokenExpired(ExposedException):
    pass        

class LogoutFailed(ExposedException):
    pass        
