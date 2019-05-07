from lxml import etree
from xmldiff import main, formatting
import os
import sys
import re
import argparse
import json


def write_error(message, report_data):
    report_data['Error']['Type'] = 'IOError'
    report_data['Error']['Message'] = message
    write_report(report_data)
    print(message, file=sys.stderr)


def write_report(report_data):
    cwd = os.getcwd()
    report_dir = 'validation_log'
    report_file = 'validation_report.json'
    report_dir_path = os.path.join(cwd, report_dir)
    report_file_path = os.path.join(report_dir_path, report_file)
    with open(report_file_path, 'w') as f:
        json.dump(report_data, f)


def validate(filename_xsd, filename_xml, filename_xml_ground_truth):
    """
    Validates the provided XML based on schema and checks whether the XML matches ground truth. Not matching ground
    truth does not mean XML is invalid, but does mean manual inspection is required.
    :param filename_xsd: The filename of the schema to validate against.
    :param filename_xml: The filename of the XML to be validated.
    :param filename_xml_ground_truth: The filename (or file-like object) to compare against.
    """
    # Initialize Report
    validation = {"Well Formed": None,
                  "Schema Valid": None,
                  "Ground Truth": {"Diff": None,
                                   "Matched": False},
                  "Error": {"Message": None,
                            "Type": None},
                  "File Names": {"Ground Truth MDL": filename_xml_ground_truth,
                                 "Transformed MDL": filename_xml}
                  }

    # parse xml
    try:
        xml_doc = etree.parse(filename_xml)
        print('XML well formed, syntax ok.')
        validation["Well Formed"] = True
    # check for file IO error
    except IOError:
        msg = f'Invalid XML file: {filename_xml}'
        write_error(msg, validation)
        raise

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        msg = f'XML syntax Error: {err.error_log}'
        write_error(msg, validation)
        raise

    except Exception as err:
        msg = f'Unknown error parsing XML, exiting: {err}'
        write_error(msg, validation)
        raise

    # validate against schema
    try:
        xmlschema_doc = etree.parse(filename_xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        xmlschema.assertValid(xml_doc)
        print('XML valid, schema validation ok.')
        validation["Schema Valid"] = True

    # check for file IO error
    except IOError:
        msg = f'Invalid schema file: {filename_xsd}'
        write_error(msg, validation)
        raise

    except etree.DocumentInvalid as err:
        msg = f'Schema validation error: {err.error_log}'
        write_error(msg, validation)
        raise

    except Exception as err:
        msg = f'Unknown error validating XML against schema, exiting: {err}'
        write_error(msg, validation)
        raise

    # diff ground truth
    try:
        xml_ground_truth = etree.parse(filename_xml_ground_truth)
        xml_doc = parse_xml(filename_xml)
        diff = main.diff_trees(xml_doc, xml_ground_truth, formatter=formatting.XMLFormatter())
        if "diff:" not in diff:
            print("Ground truth matches provided XML.")
            validation["Ground Truth"]["Matched"] = True
        else:
            print("Ground truth not matched. Diff follows:")
            print(diff)
            validation["Ground Truth"]["Diff"] = diff

    # check for file IO error
    except IOError:
        msg = f'Invalid ground truth file: {filename_xml_ground_truth}'
        write_error(msg, validation)
        raise

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        msg = f'XML syntax error in ground truth: {err.error_log}'
        write_error(msg, validation)
        raise

    except Exception as err:
        msg = f'Unknown error diffing XML, exiting: {err}'
        write_error(msg, validation)
        raise

    write_report(validation)


def parse_xml(filename: str) -> object:
    """
    Parses the XML at the provided file, removing the default namespace which is not supported by xmldiff lib.
    :param filename: The filename to be read and sanitized.
    :return: The sanitized file, parsed to lxml DOM object.
    """
    with open(filename, 'r') as file:
        body = file.read()

    body = strip_default_ns(body)
    return etree.fromstring(body)


def strip_default_ns(xml_body: str) -> str:
    """
    Strips the default namespace from the provided XML body.
    :param xml_body: The XML body to be sanitized.
    :return: The sanitized XML body.
    """
    return re.sub(r'\sxmlns="[^"]+"', '', xml_body, count=1)


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser(description='Validate provided XML against provided schema.')
    parser.add_argument('--xsd', action='store', dest='filename_xsd', help='The schema file to be validated against.')
    parser.add_argument('--xml', action='store', dest='filename_xml', help='The XML file to be validated.')
    parser.add_argument('--xml-ground-truth', action='store', dest='filename_xml_ground_truth', help='The XML file serving as ground truth.')
    cli_args = parser.parse_args()

    try:
        validate(cli_args.filename_xsd, cli_args.filename_xml, cli_args.filename_xml_ground_truth)
    except Exception as err:
        sys.exit(sys.exc_info())