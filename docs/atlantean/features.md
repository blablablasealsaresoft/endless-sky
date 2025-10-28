# Atlantean MMOFPS Feature Snapshot

This document summarizes the Atlantean Sovereignty content that currently exists in the data files and calls out major MMOFPS expectations that are **not** yet implemented. Use it as a quick reference when evaluating gaps between the present prototype and the Blizzard/Halo-style vision.

## Implemented Content

### Faction & Progression Hooks
- **Government:** `Atlantean Sovereignty` is defined with its own diplomacy profile and hail lines so it can participate in universe politics like any other faction.【F:data/governments.txt†L2299-L2320】
- **Licenses & Campaign:** The prologue missions award the `Atlantean Vanguard` license, unlock an Arsenal outfitter on Earth, and expand fleet presence across Sol, giving a story-driven onboarding flow.【F:data/atlantean/atlantean.txt†L333-L383】【F:data/atlantean/atlantean.txt†L410-L419】
- **License visibility & gating:** Dedicated license outfits now document each Atlantean rank and exchange clearance, and the Solana Bridge uplink requires the bridge clearance alongside exchange access so the crypto loop can't be skipped.【F:data/atlantean/atlantean.txt†L162-L198】
- **Ranked Leveling:** Completing the prologue, arena jobs, and exchange missions now increments an `Atlantean XP` counter and unlocks `Atlantean Vanguard Rank I-III` licenses through ascension trials, providing a light level curve and higher-tier gear gates.【F:data/atlantean/atlantean.txt†L466-L778】

### Gear & Economy
- **Atlantean Arsenal:** Multiple resonance weapons, defensive systems, engines, and support outfits emulate Halo/Destiny fireteam roles for capital ships, and the new Mythic Fusion Rifle/Arena Thruster/Bastion Bulwark extend that catalog for higher ranks.【F:data/atlantean/atlantean.txt†L14-L236】
- **Auction House:** The `Atlantean Auction House Activation` mission brings a rotating outfitter online so ranked pilots can spend tokens and credits on premium drops alongside the original exchange turn-ins.【F:data/atlantean/atlantean.txt†L706-L755】【F:data/atlantean/atlantean.txt†L120-L206】
- **Solana Bridge:** A dedicated mission installs the `Solana Bridge Uplink` and unlocks repeatable cash-out contracts, letting AquaToken caches convert into credits via a lore-friendly on-chain mirror.【F:data/atlantean/atlantean.txt†L688-L742】
- **Ledger Safeguards:** The AquaToken ledger is now bound to the Atlantean Vanguard license and remains a lightweight data outfit, preventing unintended drive buffs while keeping the crypto economy gated to ranked pilots.【F:data/atlantean/atlantean.txt†L132-L174】

### Fleets & Encounters
- **Fireteam Deployments:** Hawk and Falcon variants use the new gear, while Strike Battalion fleets patrol Sol once the player engages with the exchange storyline.【F:data/atlantean/atlantean.txt†L216-L314】【F:data/atlantean/atlantean.txt†L525-L534】
- **Arena PvP Simulations:** Repeatable control and slayer jobs spawn `Atlantean War Games` fleets near Mars and Titan, paying out caches, XP, and credits to mimic Halo/CoD multiplayer queues inside Endless Sky's single-player framework.【F:data/atlantean/atlantean.txt†L804-L880】【F:data/governments.txt†L2322-L2345】

## Remaining MMO Pillars

The latest pass adds simulated leveling, PvP queues, and an auction outfitter, but several Blizzard-scale expectations still require future work:
- **Deep Talent Trees & Roles:** Ascension ranks gate gear, yet there are no class specializations, role-based skill trees, or ability rotations beyond flavor text.
- **Player-Driven Economy:** The auction house sells curated drops rather than facilitating player listings, bids, or supply/demand dynamics.
- **True Online Multiplayer:** Endless Sky remains single-player; the arena runs are scripted encounters that only emulate PvP scoreboard pacing.
- **External Blockchain Hooks:** The Solana bridge mirrors caches in lore, but there is no actual network connectivity, wallet integration, or signature validation beyond mission text.

## Next Steps to Reach the Vision

Future milestones should focus on deeper progression systems (talents, loadout synergies), reactive economic tools (player listings, bidding windows), and, if desired, genuine networking or external API calls to back the Solana flavor with real connectivity. Those layers would elevate the Atlantean experience from a rich single-player saga to the fully fledged metaverse MMOFPS envisioned.
