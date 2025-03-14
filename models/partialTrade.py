import json
class PartialTrade:
    def __init__(self, name, status, qty, entryPrice, slPrice, maxSlPrice, targetPrice, orderType, prd, exch, tsym, diff, token):
        self.name = name
        self.status = status  # 0:inactive, 1:active, 2:completed
        self.qty = qty
        self.entryPrice = entryPrice
        self.exitPrice = None
        self.slPrice = slPrice
        self.maxSlPrice = maxSlPrice
        self.targetPrice = targetPrice
        self.orderNumber = None
        self.orderType = orderType
        self.prd = prd
        self.exch = exch
        self.tsym = tsym
        self.diff = diff
        self.token = token

    def to_json(self):
        return json.dumps(self.__dict__, indent=4)

