# VibeTicket ERC-20 Token Contract

This is a simple ERC-20-like token for the Vibe Debating project, designed to:
1. Track each debater's "tickets" (tokens) as a record of their contributions
2. Allow minting of new tokens for debate performance/rewards
3. Enable simple transfer/award/revoke mechanics

## Features
- Simple ownership model (only deployer can mint)
- Basic transfer mechanics
- Events for frontend tracking
- MIT Licensed (free to use/modify)

## Deployment

### Prerequisites
- Node.js >= 16
- npm or yarn
- MetaMask or similar wallet
- Testnet ETH (Base Sepolia recommended)

### Steps
1. Install dependencies:
   ```bash
   npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
   ```

2. Compile:
   ```bash
   npx hardhat compile
   ```

3. Create deployment script (`scripts/deploy.js`):
   ```javascript
   const hre = require("hardhat");

   async function main() {
     const [deployer] = await hre.ethers.getSigners();
     console.log("Deploying with account:", deployer.address);

     const VibeTicket = await hre.ethers.getContractFactory("VibeTicket");
     const ticket = await VibeTicket.deploy("VibeTicket", "Vibe Ticket");
     await ticket.waitForDeployment();

     console.log("VibeTicket deployed to:", ticket.target);
   }

   main().catch((error) => {
     console.error(error);
     process.exitCode = 1;
   });
   ```

4. Deploy to Base Sepolia:
   ```bash
   npx hardhat run scripts/deploy.js --network baseSepolia
   ```

5. After deployment, use the contract address to:
   - Mint initial tickets to each debater's address
   - Track awards via `awardTicket()` or direct transfers
   - Query balances with `heldBalance(address)`

## Usage in Vibe Debating

Each debate round:
1. After judging, call `awardTicket(debaterAddress)` for winning points
2. Or use direct transfers for more complex scoring
3. Frontend displays `heldBalance(address)` as the debater's "ticket count"

## Integration Notes

- Token address becomes the single source of truth for debater scores
- All reward logic lives in the contract (transparent, immutable)
- Frontend only needs to read `heldBalance` and call contract methods via wallet
- Compatible with any EVM-compatible wallet (MetaMask, Coinbase Wallet, etc.)

## License
MIT - feel free to copy, modify, and distribute.