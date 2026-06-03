// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VibeTicket
 * @notice 为 Vibe‑Debating 项目发行的 "定位代币"
 *         每位辩手在部署后会获得固定的代币余额，
 *         后续所有 "议案通过"、"赞同票" 都会在该代币上记账。
 */
contract VibeTicket {
    address public owner;
    string public symbol;
    string public name;
    uint256 public totalSupply;

    mapping(address => uint256) public seatBalance;
    mapping(address => uint256) public heldBalance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Minted(address indexed to, uint256 amount);
    event Revoked(address indexed who, uint256 amount);

    constructor(string memory _symbol, string memory _name) {
        symbol = _symbol;
        name = _name;
        totalSupply = 0;
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function balanceOf(address account) public view returns (uint256) {
        return heldBalance[account];
    }

    function getTotalSupply() public view returns (uint256) {
        return totalSupply;
    }

    function mintTicket(address account, uint256 amount) external onlyOwner {
        require(account != address(0), "Zero address not allowed");
        totalSupply += amount;
        heldBalance[account] += amount;
        emit Minted(account, amount);
    }

    function awardTicket(address to) external onlyOwner {
        heldBalance[to] += 1;
        emit Transfer(address(this), to, 1);
    }

    function revokeTicket(address to) external onlyOwner {
        require(heldBalance[to] > 0, "No ticket to revoke");
        heldBalance[to] = 0;
        emit Transfer(to, address(this), 0);
    }
}