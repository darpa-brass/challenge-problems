This README file explains how to use the xml-visualizer.py script to create diagrams of XML files. 

The xml-visualizer folder contains the following files and folders:
- 'json' directory contains the files to fine tune the output 
- xml-visualizer.py script 

Under the xml-visualizer directory, run the following command to generate the graphics:
    
    xml-visualizer.py [-h] [--version] [--output OUTPUT] [--config CONFIG] [--no-rollup] [--spacing SPACING] (--dot | --svg) instance

positional arguments:
    instance        instance document to be visualized
    
optional arguments:
    -h, --help          show this help message and exit
    --version           show program's version number and exit
    --output OUTPUT     output file location (extension depends on output options) (default: output)
    --config CONFIG     config file to fine tune output (default: None)
    --no-rollup         disable child idrefs pointing to their nearest included ancestor
    --spacing SPACING   adjust the spacing between ranks (columns) (default: 2)
    --dot               output a dot file (default: False)
    --svg               output a svg file (requires graphviz in the path) (default: False)

 ------- EXAMPLE OF GENERATING AN GRAPH ------------------------------------------------------
 Run this command if you would like to generate an svg graph file named Dau for the DAU.xml MDL file:
 
 python xml-visualizer.py --output Dau --config json\DAU.json --svg ..\schema\Examples\xml\DAU.xml
     
    
----------- Prerequisites to run the xml-visualizer.py script -------------------------------

Developed on Python version 3.3+ (not guaranteed to run on earlier versions) [https://www.python.org/downloads/]

Python libraries:
LXML - to parse the XML files [http://lxml.de/installation.html]
Graphviz - to generate the graphs [https://pypi.python.org/pypi/graphviz]

Utilities:
Graphviz - to render the graphs [http://www.graphviz.org/Download_windows.php]
