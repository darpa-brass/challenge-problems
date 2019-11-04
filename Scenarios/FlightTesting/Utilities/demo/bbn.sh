#!/bin/bash
python3 bbn.py

mkdir -p bbn
unzip artifacts.zip -d bbn
rm artifacts.zip

python3 ../xml_visualizer/xml-visualizer.py bbn/phase3/artifacts/graph_exports/0-MDL.xml --svg --config bbn_visualize_settings_1.json
mv output.svg bbn/

eog bbn/output.svg

python3 ../xml_visualizer/xml-visualizer.py bbn/phase3/artifacts/graph_exports/1-MDL.xml --svg --config bbn_visualize_settings_2.json
mv output.svg bbn/output_2.svg

eog bbn/output_2.svg
