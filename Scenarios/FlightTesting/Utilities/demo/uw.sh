#!/bin/bash
python3 uw.py

mkdir -p uw
unzip BambooEvaluationInput.zip -d uw
rm BambooEvaluationInput.zip

python3 ../TxOpScheduleViewer/TxOpSchedViewer.py ./uw/BambooEvaluationInput/ta_schedule_output_15.mdl -s ./uw/BambooEvaluationInput/score_15.json

python3 ../TxOpScheduleViewer/TxOpSchedViewer.py ./uw/BambooEvaluationInput/BRASS_Scenario4_After_Adaptation.mdl
