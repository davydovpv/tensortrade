import pandas as pd

from typing import Callable, Tuple, Union, List, Dict

from tensortrade import Component


class Portfolio(Component):
    """A portfolio of wallets for use on any ."""

    registered_name = "portfolio"

    def __init__(self, base_instrument: 'Instrument'):
        self._base_instrument = self.default(self.context.base_instrument, base_instrument)

        self._wallets = {}

    @property
    def base_instrument(self) -> 'Instrument':
        """The exchange instrument used to measure value and performance statistics."""
        return self._base_instrument

    @base_instrument.setter
    def base_instrument(self, base_instrument: 'Instrument'):
        self._base_instrument = base_instrument

    @property
    def initial_balance(self) -> 'Quantity':
        """The initial balance of the base instrument over all wallets, set by calling `reset`."""
        return self._initial_balance

    @property
    def base_balance(self) -> 'Quantity':
        """The current balance of the base instrument over all wallets."""
        return self.balance(self._base_instrument)

    @property
    def balances(self) -> List['Quantity']:
        """The current unlocked balance of each instrument over all wallets."""
        return [wallet.balance for wallet in self._wallets.values()]

    @property
    def locked_balances(self) -> List['Quantity']:
        """The current locked balance of each instrument over all wallets."""
        return [wallet.locked_balance for wallet in self._wallets.values()]

    @property
    def net_worth(self) -> float:
        """Calculate the net worth of the active account on the exchange.

        Returns:
            The total portfolio value of the active account on the exchange.
        """
        net_worth = 0

        if not self._wallets:
            return net_worth

        for (_, instrument), wallet in self._wallets.items():
            current_price = wallet.exchange.quote_price(instrument)
            net_worth += current_price * wallet.balance

        return net_worth

    @property
    def profit_loss(self) -> float:
        """Calculate the percentage change in net worth since the last reset.

        Returns:
            The percentage change in net worth since the last reset.
            e.g. A return value of 1 would indicate a 100% increase in net worth ($100 -> $200)
        """
        return self.net_worth / self._initial_net_worth

    @property
    def performance(self) -> pd.DataFrame:
        """The performance of the active account on the exchange since the last reset.

        Returns:
            A `pandas.DataFrame` with the locked and unlocked balance of each wallet at each time step.
        """
        return self._performance

    def balance(self, instrument: 'Instrument') -> 'Quantity':
        balance = 0

        for (_, instr), wallet in self._wallets.items():
            if instr.symbol == instrument.symbol:
                balance += wallet.balance

        return balance

    def locked_balance(self, instrument: 'Instrument') -> 'Quantity':
        balance = 0

        for (_, instr), wallet in self._wallets.items():
            if instr.symbol == instrument.symbol:
                balance += wallet.locked_balance

        return balance

    def group_by_exchange(self, exchange_id: str):
        # TODO
        return list(filter(self._wallets), exchange_id)

    def group_by_instrument(self, instrument: 'Instrument'):
        # TODO
        return list(filter(self._wallets), instrument.symbol)

    def filter_by(self, function: Callable):
        # TODO
        return list(filter(self._wallets, function))

    def get_wallet(self, exchange_id: str, instrument: 'Instrument'):
        return self._wallets[(exchange_id, instrument.symbol)]

    def _wallet_key(self, wallet: 'Wallet') -> Tuple[str, str]:
        return str(wallet.exchange.id), wallet.instrument.symbol

    def add(self, wallet: 'Wallet'):
        self._wallets[self._wallet_key(wallet)] = wallet

    def remove(self, wallet: 'Wallet'):
        self._wallets.pop(self._wallet_key(wallet), None)

    def update(self):
        current_performance = [self._current_step] + [quantity.amount for quantity in self.balances]
        self._performance = self._performance.append(current_performance)
        self._current_step += 1

    def reset(self):
        self._initial_balance = self.base_balance
        self._initial_net_worth = self.net_worth
        self._performance = pd.DataFrame([], columns=["step"], index="step")

        self._current_step = 0