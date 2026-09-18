require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const ARC_MAINNET_RPC_URL = process.env.ARC_MAINNET_RPC_URL || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";

/**
 * Arc mainnet: chain ID 5042 (0x13b2), EVM-compatible, gas paid in USDC.
 * Get an RPC URL from a provider that lists Arc (Alchemy, Blockdaemon, dRPC,
 * QuickNode) and put it in .env as ARC_MAINNET_RPC_URL. Do not commit .env.
 * Confirm chain ID and the RPC URL against Arc's own docs before deploying,
 * since endpoints for a brand-new mainnet can still move around.
 */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    arcMainnet: {
      url: ARC_MAINNET_RPC_URL,
      chainId: 5042,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};
