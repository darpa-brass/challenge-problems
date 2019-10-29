#!/bin/bash
python uw.py

mkdir uw
unzip BambooEvaluationInput.zip -d uw
python ../TxOpScheduleViewer/TxOpSchedViewer.py ta_1.mdl -s score_1.json