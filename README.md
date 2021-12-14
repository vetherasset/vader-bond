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
env $(cat .env) brownie run scripts/deploy_treasury.py --network kovan
env $(cat .env) brownie run scripts/deploy_bond.py --network kovan
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

##### Kovan

-   LP: [0x38F19a5452B03262203cAe9532Fbfd211fa32FF1](https://kovan.etherscan.io/address/0x38F19a5452B03262203cAe9532Fbfd211fa32FF1)
-   Vader: [0xB46dbd07ce34813623FB0643b21DCC8D0268107D](https://kovan.etherscan.io/address/0xB46dbd07ce34813623FB0643b21DCC8D0268107D)
-   Treasury: [0x15d89713eA5C46dE381C51A34fE4C743677576B4](https://kovan.etherscan.io/address/0x15d89713eA5C46dE381C51A34fE4C743677576B4)
-   Bond: [0x5D0cb7f45Cf1D538b252ecCB3edAEc8edce9A462](https://kovan.etherscan.io/address/0x5D0cb7f45Cf1D538b252ecCB3edAEc8edce9A462)

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
