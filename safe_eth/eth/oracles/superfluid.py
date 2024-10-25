from eth_abi.exceptions import DecodingError
from eth_utils import to_checksum_address
from web3.exceptions import Web3Exception

from .. import EthereumClient, EthereumNetwork
from .abis.superfluid_abis import super_token_abi
from .exceptions import CannotGetPriceFromOracle
from .oracles import PriceOracle


class SuperfluidOracle(PriceOracle):
    def __init__(self, ethereum_client: EthereumClient, price_oracle: PriceOracle):
        """
        :param ethereum_client:
        :param price_oracle: Price oracle to get the price for the components of Superfluid Tokens
        """
        self.ethereum_client = ethereum_client
        self.w3 = ethereum_client.w3
        self.price_oracle = price_oracle

    @classmethod
    def is_available(
        cls,
        ethereum_client: EthereumClient,
    ) -> bool:
        """
        :param ethereum_client:
        :return: `True` if Oracle is available for the EthereumClient provided, `False` otherwise
        """
        return ethereum_client.get_network() in (
            EthereumNetwork.POLYGON,
            EthereumNetwork.GNOSIS,
            EthereumNetwork.ARBITRUM_ONE,
            EthereumNetwork.OPTIMISM,
        )

    def get_price(self, token_address: str) -> float:
        try:
            token_address_checksum = to_checksum_address(token_address)
            underlying_token = (
                self.w3.eth.contract(
                    address=token_address_checksum, abi=super_token_abi
                )
                .functions.getUnderlyingToken()
                .call()
            )
            return self.price_oracle.get_price(underlying_token)
        except (Web3Exception, DecodingError, ValueError):
            raise CannotGetPriceFromOracle(
                f"Cannot get price for {token_address}. It is not a wrapper Super Token"
            )
