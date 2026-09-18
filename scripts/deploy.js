const hre = require("hardhat");

async function main() {
  const WatchlistRegistry = await hre.ethers.getContractFactory("WatchlistRegistry");
  const registry = await WatchlistRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log("WatchlistRegistry deployed to:", address);
  console.log("Network:", hre.network.name);
  console.log("Save this address into bot/.env as REGISTRY_ADDRESS");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
