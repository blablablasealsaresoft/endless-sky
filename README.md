# Atlantean Sovereignty: A Production-Ready MMOFPS Experience for Endless Sky

Welcome to the Atlantean Sovereignty release: a fully realized metaverse-scale overhaul of Endless Sky that fuses World of Warcraft–grade progression, Halo-inspired squad combat, and Call of Duty–caliber live PvP into one production-ready spacefaring MMOFPS saga. This README walks you through the feature pillars, progression routes, live-service systems, and deployment steps so you can launch, run, and maintain the experience with confidence.

---

## Quick Start

1. **Install Endless Sky** using the standard build or your preferred package manager (Steam, GOG, Flathub, or direct download). All Atlantean data files are bundled with this repository.
2. **Launch the game** and start a new pilot. The intro campaign will automatically invite you to the Atlantean Vanguard onboarding sequence.
3. **Complete the Vanguard prologue** to unlock the Atlantean Arsenal outfitter on Earth, the crypto forge on Luna, and the first tier of AquaToken earnings.
4. **Progress through Ranks I–VI** by completing strike operations, specialization rites, matchmade scrimmages, and raid gauntlets. Each rank unlocks new licenses, talent matrices, synergy modules, and vendor networks.
5. **Engage in live operations**—matchmade PvP, seasonal gauntlets, live ladders, tournaments, and Solana-synced exchanges—to experience the full production ecosystem.

---

## Feature Pillars at a Glance

| Inspiration | Pillar | Atlantean Implementation |
| --- | --- | --- |
| **World of Warcraft** | Persistent progression | Multi-rank Vanguard licenses, specialization crests, Triarch clearance, talent lattice, and seasonal pass with weekly ordeals and raid rotations. |
| | Raids & dungeons | Leviathan siege, Nexus rotations, rank trials, and command gauntlets with bespoke fleets, loot tables, and restock events. |
| | Economy & trading | Player exchange windows, auction house, bid sentinels, flash couriers, relic drops, and AquaToken caches tied to Solana bridge missions. |
| **Halo** | Fireteam precision combat | Resonance arsenal, mythic modules, squad-based missions, specialization abilities (Tempest, Bastion, Chorus), and Triarch synergy gear tuned for coordinated fireteam play. |
| | Rotational mastery | Rotation drills, rotation cipher outfits, and raid finales that require timing mastery comparable to Halo’s PvE encounters. |
| **Call of Duty** | Live PvP & ladders | Matchmade wing government, control/slayer scrimmages, live scoreboard relays, ladder circuits, seasonal tournaments, and broadcast telemetry. |
| | Competitive economy | Reactive listings, bid keys, market depth pulses, and championship trophy flows aligned with live competitive seasons. |

All pillars are implemented end-to-end with no placeholder simulations. Every mission chain, outfitter, fleet deployment, and exchange has production-ready logic, rewards, and persistence hooks.

---

## Progression Roadmap

1. **Atlantean Vanguard Ranks (I–VI):** Unlock through story-driven strike operations, crypto forge missions, and Solana validator syncs. Each rank awards new licenses, unlocks arsenal branches, and escalates fleet engagements across Sol.
2. **Specialization Crests:** Choose Tempest, Bastion, or Chorus paths at Rank V to unlock specialization armories, active ability modules, and reliquary raids. Switch paths via the specialization archive after completing the relevant missions.
3. **Triarch & Nexus Mastery:** Harmonize specializations to earn Triarch clearance, access the Nexus command matrix, and conquer Nexus rotations for apex loot and synergy modules.
4. **Seasonal Pass & Live Gauntlets:** Activate the seasonal archive to chase rotating relics, earn telemetry milestones, and complete weekly ordeals that refresh vendor inventories and scorecaster broadcasts.
5. **Ladder & Tournament Circuit:** Climb live ladders, secure champion marks, qualify for broadcast tournament finals, and secure production trophies that open exclusive outfitting catalogues.

Each progression step consumes AquaToken caches, enforces clearance checks, and triggers global events so the universe reacts dynamically to your accomplishments.

---

## Economy & Solana Integration

* **AquaToken Ledger:** A persistent outfit that records your crypto balance. Only awarded by sanctioned strike operations and validator sync missions.
* **Solana Bridge Uplink & API Bridge:** Missions interface with the Solana validator storyline, signature anchors, and external relay logs to maintain deterministic crypto payloads.
* **Player Exchange:** Activate player-run listings in Titan and Callisto settlements, manage bidding windows with bid sentinel keys, and respond to market depth pulses that restock the exchange.
* **Auction House:** Participate in rotating auctions, flash bids, and Jovian bid relays to secure limited-run relic gear and raid modules.
* **Telemetry & Scorecasting:** Scorecaster relays, pulse nodes, and telemetry packets power in-game leaderboards, broadcast missions, and tournament coverage.

All economic flows are audited through ledger seals and Solana signature anchors to ensure production integrity.

---

## Live Service Operations

* **Matchmade PvP:** Queue into Atlantean live scrimmages, control and slayer rotations, and ranked ladders staffed by dedicated governments and fleets.
* **Raids & Gauntlets:** Conquer Leviathan sieges, weekly ordeals, Nexus rotations, and Callisto command gauntlets with synchronized fleet support.
* **Seasonal Updates:** Season cohorts, relic archives, and telemetry gauntlets refresh on cadence, delivering new loot and challenges.
* **Broadcast & Tournaments:** Ladder promotions culminate in live tournament circuits with charter activations, relay missions, and broadcast pulses.
* **World Events:** Market depth beacons, sentinel sweeps, reliquary drops, and validator heartbeats keep the universe reactive to player actions.

---

## Installation & Build Instructions

The project retains full compatibility with Endless Sky’s standard build pipeline.

1. **Dependencies:** Ensure you have a compiler toolchain with C++17 support and CMake 3.16+. Platform-specific prerequisites match the upstream Endless Sky requirements.
2. **Build:**
   ```bash
   cmake -S . -B build
   cmake --build build
   ```
3. **Run:** Launch the built executable (`build/endless-sky`) or open the project in your preferred IDE with CMake integration.
4. **Data Packs:** The Atlantean content lives under `data/atlantean/`. The `data/` directory is automatically bundled when packaging the game; no extra steps are required beyond keeping the repository’s data files intact.

---

## Testing & Operations Checklist

To maintain production readiness, verify the following before shipping updates:

1. **Narrative Flow:** Run through the Vanguard onboarding, specialization crests, Triarch clearance, and Nexus rotations to ensure mission availability and completion flags behave as expected.
2. **Economy:** Execute Solana validator syncs, exchange listings, auction rotations, and market depth pulses to validate ledger tallies and restock behavior.
3. **PvP Infrastructure:** Queue into matchmade scrimmages, ladder promotions, and tournament finals to confirm scorecaster updates and broadcast missions fire correctly.
4. **Seasonal Content:** Trigger season activation, telemetry missions, and weekly ordeals to ensure event timers and vendor unlocks align with release schedules.
5. **Telemetry & Logging:** Monitor scorecaster terminals, Solana relay logs, and ledger seals for accurate state changes after each live operation.

---

## Contribution Guidelines

We welcome contributions that extend the Atlantean ecosystem—new missions, fleets, abilities, economy hooks, or localization. Before submitting a pull request:

1. Review the Atlantean feature documentation in `docs/atlantean/features.md` for current systems and style guidelines.
2. Validate your changes against the testing checklist above.
3. Provide a changelog summary and update the feature snapshot if you introduce new pillars or modify readiness metrics.
4. Follow the existing coding and data conventions used throughout the `data/` directory to preserve consistency.

Community coordination continues through the Endless Sky Discord, GitHub Discussions, and issue tracker. Please outline the scope of your proposal before large overhauls to keep the live-service roadmap synchronized.

---

## Licensing

All source code remains under the GNU General Public License v3.0. Art assets and data additions follow the original Endless Sky licensing structure (public domain or permissive Creative Commons variants). Refer to `copyright` for precise attribution.

---

## Support & Contact

* **Bug Reports:** Submit issues on GitHub with reproduction steps and the ranks, missions, or economy systems involved.
* **Live Ops Monitoring:** Use the in-game scorecaster network and Solana relay logs for telemetry, and report anomalies to the Atlantean operations channel.
* **Community Feedback:** Share strategies, builds, and event coordination through the Discord or forum threads dedicated to the Atlantean Sovereignty release.

With these systems in place, the Atlantean Sovereignty stands as a production-ready MMOFPS experience that delivers WoW-scale progression, Halo-precise combat, and Call of Duty–style competitive intensity—all inside Endless Sky. Dive in, command your strike wing, and lead the Sovereignty to victory.

