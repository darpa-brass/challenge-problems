#!/bin/bash
cd ~/brass/rice-proteus

env TERM=xterm-256color python3 software/challenge-problems/Scenarios/FlightTesting/Utilities/RadioQueue/RadioQueue.py --config software/cps/Sources/flightTestScenario7/orientdb_config.json -i software/cps/Sources/flightTestScenario7/data_input_rates.json -b software/cps/Sources/flightTestScenario7/bw_allocs.json --database proteus_sandbox 2>/dev/null
