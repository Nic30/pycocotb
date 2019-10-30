from copy import copy
from typing import Tuple


def sim_eval_cond(*conds):
    """
    Evaluate list of values as condition

    :return: tuple (value, value valid)
    """
    _cond = True
    _vld = True
    for v in conds:
        val = bool(v.val)
        fullVld = v.vld_mask == 1
        if fullVld:
            if not val:
                return False, True
        else:
            return False, False

        _cond = _cond and val
        _vld = _vld and fullVld

    return _cond, _vld


def valueHasChanged(valA: "Value", valB: "Value"):
    return valA.val is not valB.val or valA.vld_mask != valB.vld_mask


def mkUpdater(nextVal, invalidate: bool):
    """
    Create value updater for simulation

    :param nextVal: instance of Value which will be asssiggned to signal
    :param invalidate: flag which tells if value has been compromised
        and if it should be invaidated
    :return: function(value) -> tuple(valueHasChangedFlag, nextVal)
    """

    def updater(currentVal: "Value"):
        _nextVal = copy(nextVal)
        if invalidate:
            _nextVal.vld_mask = 0
        return (valueHasChanged(currentVal, _nextVal), _nextVal)

    return updater


def mkArrayUpdater(nextItemVal: "Value", indexes: Tuple["Value"],
                   invalidate: bool):
    """
    Create value updater for simulation for value of array type

    :param nextVal: instance of Value which will be asssiggned to signal
    :param indexes: tuple on indexes where value should be updated
        in target array

    :return: function(value) -> tuple(valueHasChangedFlag, nextVal)
    """

    def updater(currentVal):
        if len(indexes) > 1:
            raise NotImplementedError("[TODO] implement for more indexes")

        _nextItemVal = copy(nextItemVal)
        if invalidate:
            _nextItemVal.vld_mask = 0

        index = indexes[0]
        change = valueHasChanged(currentVal[index], _nextItemVal)
        currentVal[index] = _nextItemVal
        return (change, currentVal)

    return updater
