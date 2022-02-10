# Vader Bond

### Install

```shell
# install virtualenv
python3 -m pip install --user virtualenv
virtualenv -p python3 venv
source venv/bin/activate

pip install eth-brownie
pip install matplotlib
pip install numpy
pip install prettytable

brownie pm install OpenZeppelin/openzeppelin-contracts@3.4.2

npm i
npm i -g ganache-cli

cp .env.sample .env
```

### Test

```shell
brownie test tests/path-to-test-file-or-folder -s -v

# mainnet
source .env

npx ganache-cli \
--fork https://mainnet.infura.io/v3/$WEB3_INFURA_PROJECT_ID \
--unlock $VADER_WHALE

env $(cat .env) brownie test tests/mainnet/test_zap_eth.py --network mainnet-fork -s --gas
```

### Deploy

```shell
env $(cat .env) ACCOUNT=dev brownie run scripts/deploy_treasury.py --network kovan
env $(cat .env) ACCOUNT=dev brownie run scripts/deploy_vader_bond.py --network kovan
```

### Simulation

##### Increasing bond price

![bond-price-inc](./doc/bond-price-inc.png)

##### Decreasing bond price

![bond-price-dec](./doc/bond-price-dec.png)

### Deployment

1. Deploy `Treasury`
2. Deploy `VaderBond`
3. Call `Treasury.setBondContract`
4. Set max payout to 0 `VaderBond.setBondTerm(1, 0)`
5. Call `Treasury.setMaxPayout`
6. Send Vader to `Treasury`
7. Call `VaderBond.initialize`

##### Mainet

-   Vader ETH LP: 0x452c60e1E3Ae0965Cd27dB1c7b3A525d197Ca0Aa
-   Treasury: 0x8a2afC7a4c2C19E81a79D9158d6bca3858a87B73
-   Vader: 0x2602278EE1882889B946eb11DC0E810075650983
-   VaderBond - Uniswap V2 ETH LP: 0x1B96d82b8b13C75d4cE347a53284B10d93B63684
-   ZapUniswapV2EthLp: 0x781B2844605298FB45C653Dc1EF0d0b941293323
-   VaderBond - WETH:
-   ZapEth:

##### Kovan

-   Vader ETH LP: 0xC42706E83433580dd8d865a30e2Ae61082056007
-   Treasury: 0x666266f24E17d9ab7bCb25715C75146143E16c39
-   Vader: 0xB46dbd07ce34813623FB0643b21DCC8D0268107D
-   VaderBond - Uniswap V2 ETH LP: 0xd932cc11F49df7638999E2a313e5808667363750
-   ZapUniswapV2EthLp: 0x6D51Ef96C362fdea02c61Ce2dD1A263B5ABbd4B9
-   VaderBond - WETH: 0xA8ac19C394783EAcDD36e53686Db037715c87fcD
-   ZapEth: 0x05191774a53c629d9c9ea90e3D4BC54b6863Fd60
-   PreCommit: 0xc2BB0EE1f78cC83317727edCC7FDfc1CaF808d0F
-   ZapEthToPreCommit: 0x1B3B835C0f7d355CBb02232624dB59ea8Cea0d48

##### Rinkeby

-   TestToken: 0xE8bD273f54a990007b1069a15b66B584abc86e04
-   Vader: 0xF79c9406c14AF5Aa8b3F1E5E538A026aDf4D0ff5
-   Treasury: 0xEa66FB7590147A5C901E14034f243e1cF8f958ff
-   VaderBond: 0x0A23bde5E3930EfEaa546A4b4F10a1b7A9cC1e6C
-   PreCommit: 0x795bE6b0BF54AF587385604B9DB869E797db69E0

### Misc

```shell
pip3 install solc-select

# select solc compiler
solc-select install 0.7.6
solc-select use 0.7.6

# check code size (max 2457 bytes)
brownie compile -s

# console
env $(cat .env) brownie console --network kovan
```
