"""
src/ragEngine.py — ASCSPipeline RAG Knowledge Base
===================================================
Provides a lightweight TF-IDF-backed retrieval engine seeded with smart
contract vulnerability information from the SWC registry and common DeFi
attack patterns.

Uses scikit-learn TfidfVectorizer + cosine similarity instead of
sentence-transformers + FAISS, reducing the dependency footprint from
~1.5 GB to ~25 MB with no meaningful quality loss for a 16-chunk corpus.

Usage:
    from src.ragEngine import RagEngine
    engine = RagEngine()
    context = engine.retrieveContext("reentrancy vulnerability withdraw")

Author: ASCSPipeline
Coding style: camelCase, PascalCase for classes, minimal underscores
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List


# ── Knowledge Base ─────────────────────────────────────────────────────────────

KNOWLEDGE_CHUNKS = [
    # ── SWC-101: Integer Overflow / Underflow ──────────────────────────────────
    """SWC-101: Integer Overflow and Underflow.
Solidity integers can overflow or underflow without reverting in compiler versions
below 0.8.0. An attacker can trigger arithmetic wrap-around to bypass balance checks.
Exploit: An attacker calls transfer with a value larger than uint256 max, causing
the sender balance to wrap to a very large number.
Fix: Use Solidity >= 0.8.0 (built-in checked arithmetic) or OpenZeppelin SafeMath
for older versions. Always validate arithmetic results.""",

    # ── SWC-107: Reentrancy ────────────────────────────────────────────────────
    """SWC-107: Reentrancy Attack.
A contract makes an external call before updating its own state. A malicious
contract receives control and recursively calls back into the vulnerable function,
draining funds before the balance is ever decremented.
Exploit: Attacker deploys a contract whose fallback/receive function re-enters
the withdraw() function. The balance check passes each time since state is not yet
updated. The attacker drains the contract in a loop.
Fix: Follow the Checks-Effects-Interactions pattern. Update all state variables
BEFORE making any external calls. Use a ReentrancyGuard mutex (nonReentrant
modifier from OpenZeppelin).""",

    # ── SWC-105: Unprotected Ether Withdrawal ─────────────────────────────────
    """SWC-105: Unprotected Ether Withdrawal.
A function that sends Ether lacks proper access control, allowing any caller to
drain the contract's Ether balance.
Exploit: Attacker calls the withdrawal function without any ownership check and
receives all contract Ether.
Fix: Add an onlyOwner or access-control modifier (e.g., Ownable from OpenZeppelin)
to restrict who can call withdrawal functions.""",

    # ── SWC-106: Unprotected SELFDESTRUCT ─────────────────────────────────────
    """SWC-106: Unprotected SELFDESTRUCT Instruction.
A selfdestruct call is exposed without access control. Any caller can destroy the
contract and receive all its Ether.
Exploit: Attacker calls the function containing selfdestruct(attacker_address),
destroying the contract and redirecting all funds.
Fix: Gate the selfdestruct call with a strict onlyOwner modifier. Consider removing
selfdestruct entirely in upgradeable contract architectures.""",

    # ── SWC-108: State Variable Default Visibility ─────────────────────────────
    """SWC-108: State Variable Default Visibility.
State variables declared without an explicit visibility specifier default to
internal, but this is not always the developer's intent.
Fix: Always specify visibility (public, private, internal) explicitly for every
state variable to document intent and prevent accidental exposure.""",

    # ── SWC-110: Assert Violation ──────────────────────────────────────────────
    """SWC-110: Assert Violation.
An assert() statement fails, consuming all remaining gas. assert() should only
be used for invariant checks that should never fail. Using assert() where
revert() or require() is appropriate wastes user gas on failures.
Fix: Replace assert() with require() for input validation and error conditions.
Reserve assert() strictly for internal invariants.""",

    # ── SWC-113: DoS with Failed Call ─────────────────────────────────────────
    """SWC-113: Denial of Service with Failed Call.
A contract loops over an array of addresses and calls each one. If any external
call fails (reverts or runs out of gas), the entire transaction reverts,
potentially blocking all future interactions.
Exploit: Attacker creates a contract that always reverts on receive. Once it is
added to the array, the loop can never complete, freezing withdrawals.
Fix: Use the pull-payment pattern (let users withdraw individually) instead of
pushing payments in loops. Use try/catch and continue on failure.""",

    # ── SWC-115: tx.origin Authentication ─────────────────────────────────────
    """SWC-115: Authorization Using tx.origin.
Using tx.origin for authentication allows phishing attacks where a malicious
intermediate contract triggers the vulnerable contract on behalf of the victim.
Exploit: Victim calls MaliciousContract, which in turn calls VulnerableContract.
VulnerableContract checks tx.origin == owner, which passes because tx.origin is
the victim (owner). The malicious contract drains funds.
Fix: Always use msg.sender for authorization. Never use tx.origin for access control.""",

    # ── SWC-116: Block Timestamp Manipulation ─────────────────────────────────
    """SWC-116: Block Timestamp Manipulation.
Miners have limited ability to manipulate block.timestamp within a ~15 second
window. Contracts using block.timestamp for randomness, expiration checks, or
auction timing can be exploited.
Fix: Do not use block.timestamp for randomness. Use Chainlink VRF or
commit-reveal schemes. For time-based conditions, use block numbers.""",

    # ── SWC-120: Weak Sources of Randomness ───────────────────────────────────
    """SWC-120: Weak Sources of Randomness from Chain Attributes.
Using block.number, block.timestamp, blockhash, or other on-chain values as
randomness sources can be predicted or manipulated by miners and front-runners.
Exploit: A miner withholds a block until the random outcome favors them.
Fix: Use Chainlink VRF (Verifiable Random Function) for on-chain randomness.
For lotteries, use commit-reveal schemes with economic incentives to reveal.""",

    # ── DeFi: Flash Loan Attack ────────────────────────────────────────────────
    """DeFi Flash Loan Attack Pattern.
Flash loans provide uncollateralized capital within a single transaction.
Attackers use flash loans to temporarily acquire massive capital, manipulate
on-chain price oracles, drain liquidity pools, or exploit price differences.
Exploit: Attacker borrows 1M USDC via flash loan, manipulates AMM pool price
used by a lending protocol, borrows against inflated collateral, and repays the
flash loan — keeping the profit.
Fix: Do not use single AMM pool spot prices as oracles. Use Chainlink price feeds
or Uniswap V3 TWAPs with sufficient observation windows (minimum 30 minutes).""",

    # ── DeFi: Price Oracle Manipulation ──────────────────────────────────────
    """DeFi Price Oracle Manipulation.
Protocols relying on on-chain spot prices from DEX pools are vulnerable.
Attackers can briefly manipulate the price within a single block.
Fix: Use Chainlink decentralized oracle networks. If using on-chain DEX prices,
use Uniswap V3 pool.observe() TWAP with a window of at least 1800 seconds.
Add circuit breakers that freeze operations when price deviates significantly.""",

    # ── Access Control: Missing onlyOwner ─────────────────────────────────────
    """Access Control: Missing Owner Checks.
Critical functions like setOwner, upgradeTo, withdraw, or pause lack access
control modifiers. Any externally owned account can call them.
Fix: Inherit OpenZeppelin Ownable or AccessControl. Apply onlyOwner or
hasRole(ADMIN_ROLE, msg.sender) to all privileged functions. Emit events for
all ownership and role changes for off-chain monitoring.""",

    # ── ERC-20: Approve Race Condition ─────────────────────────────────────────
    """ERC-20 Approve Race Condition (SWC-114).
The standard ERC-20 approve() function is vulnerable to a front-running attack.
When an owner changes an allowance from N to M, the spender can observe the
pending transaction and spend the old N allowance before it is replaced.
Fix: Use increaseAllowance() / decreaseAllowance() instead of approve().
Alternatively, require setting allowance to 0 before any non-zero value.""",

    # ── Upgrade: Uninitialized Proxy ──────────────────────────────────────────
    """Uninitialized Proxy Implementation Contract.
In upgradeable proxy patterns (UUPS, Transparent Proxy), the implementation
contract itself may be callable directly if not initialized. An attacker can
call initialize() on the bare implementation and become its owner.
Fix: Call _disableInitializers() in the implementation contract constructor.
Always initialize proxies atomically in the same transaction as deployment.""",

    # ── Gas: Unbounded Loop ────────────────────────────────────────────────────
    """Gas Limit DoS: Unbounded Loop Over Dynamic Array.
A function iterates over an array whose size grows with user input. As the array
grows, the gas cost approaches or exceeds the block gas limit, permanently
breaking the function.
Exploit: Attacker submits many small entries to grow the array until the
processing function can no longer execute within a single block.
Fix: Cap array sizes. Use mappings instead of arrays for O(1) lookups. Process
entries in bounded batches using a pagination pattern.""",
]


# ── RAG Engine ─────────────────────────────────────────────────────────────────

class RagEngine:
    """
    Lightweight TF-IDF-based retrieval engine backed by scikit-learn.
    Pre-fitted on the hardcoded smart contract vulnerability knowledge base.
    No GPU, no heavy model downloads, no external API required.
    """

    def __init__(self):
        """Fits the TF-IDF vectorizer on all knowledge chunks at construction time."""
        self.chunks = KNOWLEDGE_CHUNKS
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=8000,
        )
        self.chunkMatrix = self.vectorizer.fit_transform(self.chunks)

    def retrieveContext(self, query: str, topK: int = 4) -> str:
        """
        Retrieves the most semantically relevant knowledge chunks for a given query
        using TF-IDF cosine similarity.

        Args:
            query: A natural language or code-based query string.
            topK:  Number of top results to return.

        Returns:
            A formatted string of the top-K relevant knowledge chunks.
        """
        queryVector = self.vectorizer.transform([query])
        similarities = cosine_similarity(queryVector, self.chunkMatrix).flatten()
        topIndices = similarities.argsort()[::-1][:topK]

        results: List[str] = []
        for rank, idx in enumerate(topIndices):
            if similarities[idx] > 0:
                results.append(f"[Relevant Context {rank + 1}]\n{self.chunks[idx]}")

        return "\n\n".join(results) if results else "No specific context retrieved."
