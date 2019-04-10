from lxml import etree
from io import StringIO
from validate import validate
from validate import strip_default_ns
import argparse

V17_FILENAME_XSD = '../../Scenario_6/MDL_v0_8_17_with_Examples/MDL_v0_8_17.xsd'
V19_FILENAME_XSD = '../../Scenario_6/MDL_v0_8_19_with_Examples/MDL_v0_8_19.xsd'
V17_TO_V19_XSLT = '../../Scenario_6/v17_to_19.xsl'
V19_TO_V17_XSLT = '../../Scenario_6/v19_to_17.xsl'


def validate_mdl(filename_v17_mdl, filename_v19_mdl, target_version):
    """
    Validates provided generated MDL against XSLT conversion of provided starting MDL.
    :param filename_v17_mdl: The v0_8_17 MDL file.
    :param filename_v19_mdl: The v0_8_19 MDL file.
    :param target_version: Indicates which of the files provided was generated vs. source of generation.
    """

    # figure out whether we're going to 19 or to 17 and set vars accordingly
    filename_to_transform = filename_v17_mdl
    filename_xslt = V17_TO_V19_XSLT
    filename_xsd = V19_FILENAME_XSD
    filename_xml = filename_v19_mdl

    if target_version == 17:
        filename_to_transform = filename_v19_mdl
        filename_xslt = V19_TO_V17_XSLT
        filename_xsd = V17_FILENAME_XSD
        filename_xml = filename_v17_mdl

    # perform transformation and pass values off to be validated
    xml_doc = etree.parse(filename_to_transform)
    xslt_doc = etree.parse(filename_xslt)
    xslt = etree.XSLT(xslt_doc)
    transformed_doc = xslt(xml_doc)
    transformed_str = strip_default_ns(str(transformed_doc))
    transformed_file = StringIO(transformed_str)

    # invoke validation
    validate(filename_xsd, filename_xml, transformed_file)


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser(description='Validate provided MDL against XSLT converted file.')
    parser.add_argument('--v17-mdl', action='store', dest='filename_v17_mdl', help='The v17 MDL file.')
    parser.add_argument('--v19-mdl', action='store', dest='filename_v19_mdl', help='The v19 MDL file.')
    parser.add_argument('--target-version', action='store', dest='target_version', type=int, choices=[17, 19])
    cli_args = parser.parse_args()

    validate_mdl(cli_args.filename_v17_mdl, cli_args.filename_v19_mdl, cli_args.target_version)
