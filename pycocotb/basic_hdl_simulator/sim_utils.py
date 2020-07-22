from typing import Tuple
from itertools import islice


def sim_eval_cond(v):
    """
    Evaluate list of values as condition

    :return: tuple (value, value valid)
    """
    if v.vld_mask == 1:
        return bool(v.val), True
    else:
        return False, False


def valueHasChanged(valA: "Value", valB: "Value"):
    return valA.val is not valB.val or valA.vld_mask != valB.vld_mask


class ValueUpdater():

    def __init__(self, nextVal, invalidate: bool):
        """
        Create value updater for simulation
    
        :param nextVal: instance of Value which will be assigned to signal
        :param invalidate: flag which tells if value has been compromised
            and if it should be invalidated
        """
        self.nextVal = nextVal
        self.invalidate = invalidate

    def __call__(self, currentVal: "Value"):
        _nextVal = self.nextVal.__copy__()
        if self.invalidate:
            _nextVal.vld_mask = 0
        return (valueHasChanged(currentVal, _nextVal), _nextVal)


class ArrayValueUpdater():
    
    def __init__(self, nextItemVal: "Value", indexes: Tuple["Value"],
                 invalidate: bool):
        """
        Create value updater for simulation for value of array type
        
        :param nextVal: instance of Value which will be assigned to signal
        :param indexes: tuple on indexes where value should be updated
            in target array
        """
        self.nextItemVal = nextItemVal
        self.indexes = indexes
        self.invalidate = invalidate

    def __call__(self, currentVal):
        _currentVal = currentVal
        indexes = self.indexes
        if len(indexes) > 1:
            raise NotImplementedError("[TODO] implement for more indexes")
            for i in islice(indexes, len(indexes) - 1):
                _currentVal = _currentVal[i]

        nextItemVal = self.nextItemVal
        _nextItemVal = nextItemVal.__copy__()
        if self.invalidate:
            _nextItemVal.vld_mask = 0

        index = indexes[-1]
        change = valueHasChanged(_currentVal[index], _nextItemVal)
        _currentVal[index] = _nextItemVal
        return (change, currentVal)
