#!/bin/bash
python3 spiral.py

mkdir -p spiral
mv TmnsDAU_out.pcapng spiral/

wireshark spiral/TmnsDAU_out.pcapng
