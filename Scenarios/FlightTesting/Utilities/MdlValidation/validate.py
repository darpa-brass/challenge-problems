from lxml import etree
from xmldiff import main, formatting
import sys
import argparse


def validate(filename_xsd, filename_xml, filename_xml_ground_truth):
    # parse xml
    try:
        xml_doc = etree.parse(filename_xml)
        print('XML well formed, syntax ok.')

    # check for file IO error
    except IOError:
        print(f'Invalid XML file: {filename_xml}', file=sys.stderr)
        sys.exit(1)

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        print(f'XML syntax Error: {err.error_log}', file=sys.stderr)
        sys.exit(1)

    except Exception as err:
        print(f'Unknown error parsing XML, exiting: {err}', file=sys.stderr)
        sys.exit(1)

    # validate against schema
    try:
        xmlschema_doc = etree.parse(filename_xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        xmlschema.assertValid(xml_doc)
        print('XML valid, schema validation ok.')

    # check for file IO error
    except IOError:
        print(f'Invalid schema file: {filename_xsd}', file=sys.stderr)
        sys.exit(1)

    except etree.DocumentInvalid as err:
        print(f'Schema validation error: {err.error_log}', file=sys.stderr)
        sys.exit(1)

    except Exception as err:
        print(f'Unknown error validating XML against schema, exiting: {err}', file=sys.stderr)
        sys.exit(1)

    # diff ground truth
    try:
        xml_ground_truth = etree.parse(filename_xml_ground_truth)
        diff = main.diff_trees(xml_doc, xml_ground_truth, formatter=formatting.XMLFormatter())
        if "diff:" not in diff:
            print("Ground truth matches provided XML.")
        else:
            print("Ground truth not matched. Diff follows:")
            print(diff)

    # check for file IO error
    except IOError:
        print(f'Invalid ground truth file: {filename_xml_ground_truth}', file=sys.stderr)
        sys.exit(1)

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        print(f'XML syntax error in ground truth: {err.error_log}', file=sys.stderr)
        sys.exit(1)

    except Exception as err:
        print(f'Unknown error diffing XML, exiting: {err}', file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser(description='Validate provided XML against provided schema.')
    parser.add_argument('--xsd', action='store', dest='filename_xsd', help='The schema file to be validated against.')
    parser.add_argument('--xml', action='store', dest='filename_xml', help='The XML file to be validated.')
    parser.add_argument('--xml-ground-truth', action='store', dest='filename_xml_ground_truth', help='The XML file serving as ground truth.')
    cli_args = parser.parse_args()

    validate(cli_args.filename_xsd, cli_args.filename_xml, cli_args.filename_xml_ground_truth)
