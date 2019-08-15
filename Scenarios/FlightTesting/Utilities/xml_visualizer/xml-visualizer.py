# This script was produced under the iNET program.

import argparse
import itertools
import textwrap
import json
import sys

from collections import defaultdict, OrderedDict

from lxml import etree
import graphviz


RANKSEP = "0"


# generated list of colors to index into based on the graph depth
def get_new_hex(old, _):
    # break the incoming hex into rgb and subtract 18 from each
    r, g, b = [int(old[i:i+2], 16) - 18 for i in range(0, 5, 2)]

    return "{:02x}{:02x}{:02x}".format(r, g, b)


# create a list of 10 colors starting at e8eef7
colors = list(itertools.accumulate(itertools.repeat("e8eef7", 10), get_new_hex))


# assign unique numbers to use as node names
unique_identifiers = itertools.count(0)


def get_unique_identifier():
    return "n"+str(next(unique_identifiers))


def format_text(text):
    """
    Text wrap to 40 characters to make it fit in our boxes
    """
    return textwrap.fill(str(text), 40)


def get_label(node):
    """
    Returns a wrapped string with the element name, its attributes, and contents
    """
    if node.tag == 'this-is-a-shortened-xml-tag':
        return "..."

    entries = [etree.QName(node.tag).localname]

    for key, value in node.attrib.items():
        entries.append(format_text("{}: {}".format(key, value)))

    if node.text:
        entries.append(format_text(node.text))

    return "\n".join(entries)


def defaultdict_list_update(fred, joe):
    """
    Returns the result of defaultdict(list) fred with joe's elements appended
    """
    for k, v in joe.items():
        fred[k].extend(v)

    return fred


def get_base_graph():
    """
    Returns a graph with all the default node options set up
    """
    base_graph = graphviz.Digraph('G', engine='dot', format='svg')
    # lay out the graph where items at the same depth are in the same vertical plane
    base_graph.graph_attr.update(rankdir="LR")
    # nodes will touch each other
    base_graph.graph_attr.update(nodesep="0")
    # allows for edges to be customized with logical heads and tails (for edges pointing to clusters)
    base_graph.graph_attr.update(compound="true")
    # monowidth font so we can wrap to a fixed size and it will always fit
    base_graph.graph_attr.update(fontname="consolas", fontsize="8")
    # make more space between the nodes with edges
    base_graph.graph_attr.update(ranksep=RANKSEP)
    # arrow color
    base_graph.edge_attr.update(color='#4677bf')
    base_graph.node_attr.update(style='filled', shape='box', color='black', width='2.75', height=".3", fontname='consolas', fontsize="8")

    # overlap and splines may be able to help with edges overlapping, but didn't seem to do anything in big file tests (maybe because subgraphs)
    # base_graph.graph_attr.update(overlap="scalexy")
    # base_graph.graph_attr.update(splines="true")

    return base_graph


def visualize_root_config(instance, config, rollup=True):
    """
    Returns a graph object visualizing a specified subset of an XML file based on a config file
    """
    ns = config['namespaces']
    reverse_ns = {v: k for k, v in config['namespaces'].items()}
    base_graph = get_base_graph()
    ids = {}
    idrefs = defaultdict(list)

    for path, options in config['objects'].items():
        for element in instance.xpath(path, namespaces=ns):
            # remove all the extra nodes matching the path, and replace the second to last with a ...
            if 'abbreviate' in options:
                # store up the changes, because we run the xpath each time and if we've removed things the number will change
                removals = []
                shortens = []
                for path in options['abbreviate']:
                    for node in element.xpath(path, namespaces=ns):
                        # count preceding siblings with the same tag
                        qname = etree.QName(node.tag)
                        preceding = node.xpath("count(preceding-sibling::{}:{})".format(reverse_ns[qname.namespace], qname.localname), namespaces=ns)
                        if preceding > 1:
                            removals.append(node)
                        elif preceding == 1:
                            shortens.append(node)

                for node in removals:
                    node.getparent().remove(node)
                for node in shortens:
                    # our label maker knows to replace this tag name with a ... (which is not a valid XML tag)
                    node.getparent().replace(node, etree.Element("this-is-a-shortened-xml-tag"))

            if 'exclude' in options:
                # remove all the elements which match the xpath
                for path in options['exclude']:
                    for node in element.xpath(path, namespaces=ns):
                        node.getparent().remove(node)

            graph, child_ids, child_idrefs = visualize(element, limit=options.get('depth', None), rollup=rollup)

            ids.update(child_ids)
            idrefs = defaultdict_list_update(idrefs, child_idrefs)

            # set the style for the child here, so they all match (but the graph background is still white)
            graph.graph_attr.update(color="black")
            graph.graph_attr.update(style="filled")

            base_graph.subgraph(graph)

    # add edges from each IDREF to its target ID
    for ref, nodes in idrefs.items():
        for node in nodes:
            # when taking a subset it's possible for not all IDREFs to have matching IDs, so just warn and ignore them
            if ref not in ids:
                print("Matching ID not found for IDREF: {}".format(ref), file=sys.stderr)
                continue
            # set the lhead to point to the cluster and the actual edge to point to the invisible node in clusters
            if "cluster_" in ids[ref]:
                base_graph.edge(node, ids[ref][8:], None, {"lhead": ids[ref]})
            else:
                base_graph.edge(node, ids[ref])

    return base_graph


def visualize_root(instance, rollup=True):
    """
    Returns a graph object visualizing a full XML file starting from the root node
    """
    base_graph = get_base_graph()
    root = instance.getroot()

    graph, ids, idrefs = visualize(root, rollup=rollup)

    # set the style for the children here, so they all match (but the graph background is still white)
    graph.graph_attr.update(color="black")
    graph.graph_attr.update(style="filled")

    # add edges from each IDREF to its target ID
    for ref, nodes in idrefs.items():
        for node in nodes:
            # set the lhead to point to the cluster and the actual edge to point to the invisible node in clusters
            if "cluster_" in ids[ref]:
                # unlike the config case, we set the edges inside the top level graph because otherwise it would create the nodes before the graph
                graph.edge(node, ids[ref][8:], None, {"lhead": ids[ref]})
            else:
                graph.edge(node, ids[ref])

    base_graph.subgraph(graph)
    return base_graph


def visualize(node, depth=0, limit=None, rollup=True):
    """
    Recursive call for visualize, returns a graph object for a given element and all others below it, optionally bounded at a given depth
    """
    # dict from XML IDs to their corresponding node identifiers
    ids = {}
    # dict from XML IDs to nodes which are IDREFs referencing them
    idrefs = defaultdict(list)

    ident = "cluster_{}".format(get_unique_identifier())
    # clusters (collections of nodes) have 'cluster' prepended to their names
    graph = graphviz.Digraph(ident)
    graph.graph_attr.update(label=get_label(node))

    if 'ID' in node.attrib:
        # add an invisible node to point to when referencing subgraphs
        graph.node(ident[8:], None, {"shape": "point", "style": "invis", "width": "0"})
        ids[node.get('ID')] = ident
    if 'IDREF' in node.attrib:
        idrefs[node.get('IDREF')].append(ident)

    # just reuse the last color once we've exceeded the depth
    if depth + 1 < len(colors):
        graph.graph_attr.update(fillcolor='#{}'.format(colors[depth]))
        graph.node_attr.update(fillcolor='#{}'.format(colors[depth+1]))
    else:
        graph.graph_attr.update(fillcolor='#{}'.format(colors[len(colors)-1]))
        graph.node_attr.update(fillcolor='#{}'.format(colors[len(colors)-1]))

    # if limit is 0, short circuit and just return the current node
    # for limit 1, the short circuit doesn't apply, but it will fail the first check, giving only the children
    if limit == 0:
        # create an invisible empty node to force the box to be the right size
        graph.node(ident[8:] + "f", None, {"style": "invis", "height": "0", "fixedsize": "true", "fontsize": "0"})
        if rollup:
            for element_id in node.xpath(".//@ID"):
                ids[element_id] = ident
    # a node should go only as deep as the limit, so we add one since we're adding children here
    elif limit is None or depth + 1 < limit:
        for element in node.iterchildren(tag=etree.Element):
            # if it has children, recurse and add as a subgraph
            if len(element):
                child, child_ids, child_idrefs = visualize(element, depth+1, limit, rollup)
                ids.update(child_ids)
                idrefs = defaultdict_list_update(idrefs, child_idrefs)
                graph.subgraph(child)
            else:
                # if it doesn't, check IDs and IDREFs before adding as a node at the current level
                ident = get_unique_identifier()
                if 'ID' in element.attrib:
                    ids[element.get('ID')] = ident
                if 'IDREF' in element.attrib:
                    idrefs[element.get('IDREF')].append(ident)
                graph.node(ident, get_label(element))
    else:
        # no more recursing; everything left is a leaf node
        for element in node.iterchildren(tag=etree.Element):
            ident = get_unique_identifier()
            if 'ID' in element.attrib:
                ids[element.get('ID')] = ident
            if 'IDREF' in element.attrib:
                idrefs[element.get('IDREF')].append(ident)
            graph.node(ident, get_label(element))
            # if we're using rollup, every sub element with an ID is now the parent element
            # this means IDREFs that would point to a child will point to this nearest ancestor
            if rollup:
                for element_id in element.xpath(".//@ID"):
                    ids[element_id] = ident

    return graph, ids, idrefs


def main():
    global RANKSEP
    file_version = "0.0.1"
    parser = argparse.ArgumentParser(description="XML Visualizer to create diagrams of XML files",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(file_version))

    parser.add_argument('instance', help="instance document to be visualized")
    parser.add_argument('--output', help="output file location (extension depends on output options)", default="output")
    parser.add_argument('--config', help="config file to fine tune output")
    parser.add_argument('--no-rollup', help="disable child idrefs pointing to their nearest included ancestor", action="store_false")
    parser.add_argument('--spacing', help="adjust the spacing between ranks (columns)", default="2")
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument('--dot', help="output a dot file", action="store_true")
    outputs.add_argument('--svg', help="output a svg file (requires graphviz in the path)", action="store_true")

    args = parser.parse_args()

    RANKSEP = args.spacing
    with open(args.instance, 'r') as f:
        instance = etree.parse(f)

    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
            # sort the dictionary to make running on one file more deterministic
            config['objects'] = OrderedDict(sorted(config['objects'].items()))
            graph = visualize_root_config(instance, config, args.no_rollup)
    else:
        # simple mode: just visualize the whole file
        graph = visualize_root(instance, args.no_rollup)

    if args.svg:
        graph.render(args.output)
    elif args.dot:
        with open('{}.dot'.format(args.output), 'w') as f:
            f.write(graph.source)


if __name__ == "__main__":
    main()
