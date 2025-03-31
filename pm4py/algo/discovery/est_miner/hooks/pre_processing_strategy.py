import abc

class PreProcessingStrategy(abc.ABC):

    @abc.abstractmethod
    def execute(self, log):
        """
        Pre-process the given event log, using certain filters
        and aggregates.
        """
        pass

class NoPreProcessingStrategy(PreProcessingStrategy):

    def execute(self, log):
        print('Executed Pre Processing')
        return log
