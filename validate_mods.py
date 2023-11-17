"""
Validates mods from the embedded xsd url in the mods root element.

Usage...
    $ python ./validate_mods.py --input_path "/path/to/mods.xml"

---

Example failure...

I initially had ``<mods:relatedItem type="collection">``.

log output...
    is_valid, ``False``
    Validation failed. Errors:
        Element '{http://www.loc.gov/mods/v3}relatedItem', attribute 'type': [facet 'enumeration'] 
        The value 'collection' is not an element of the set {'preceding', 'succeeding', 'original', 'host', 'constituent', 'series', 'otherVersion', 'otherFormat', 'isReferencedBy', 'references', 'reviewOf'}.
    done
"""

import argparse, logging, os, pprint
from lxml import etree
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request


lglvl: str = os.environ.get( 'LOGLEVEL', 'DEBUG' )
lglvldct = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO }
logging.basicConfig(
    level=lglvldct[lglvl],  # assigns the level-object to the level-key
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S' )
log = logging.getLogger( __name__ )
log.debug( 'logging working' )


## main function ----------------------------------------------------
def validate_mods (xml_path: str) -> bool:

    ## get xsd from xml
    xsd_url: str = get_xsd_url_from_xml( xml_path )
    xsd_string: str = download_xsd_to_string(xsd_url)
    log.debug( 'xsd_string prepared' )

    xmlschema_doc = etree.fromstring( xsd_string.encode('utf-8') )  # creates a plain xml-doc-object from the string
    log.debug( 'xmlschema_doc prepared' )
    xmlschema = etree.XMLSchema(xmlschema_doc)  # creates a schema-object from the xml-doc-object, which has certain capabilities such as validation
    log.debug( 'xmlschema prepared' )

    mods_doc = etree.parse(xml_path)
    is_valid = xmlschema.validate(mods_doc)
    log.debug( f'is_valid, ``{is_valid}``' )

    if not is_valid:
        log.error('Validation failed. Errors:')
        for error in xmlschema.error_log:
            log.error(f'Line {error.line}: {error.message}')

    return is_valid


def get_xsd_url_from_xml(xml_path):
    """ Parses the xsd url from the MODS root element. 
        Attribute looks like: ```xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/mods/v3/mods-3-7.xsd"```.
        Called by validate_mods() """
    xsd_url = 'init'
    with open(xml_path, 'r') as file:
        for line in file:
            log.debug( f'line: {line}' )
            if 'xsi:schemaLocation' in line:
                log.debug( f'found xsi:schemaLocation' )
                parts = line.split()
                log.debug( f'parts: {pprint.pformat(parts)}')
                for i, part in enumerate(parts):
                    if 'mods/v3' in part and 'xsd' in part:
                        xsd_url = part
                        log.debug( f'xsd_url: ``{xsd_url}``' )
                break
    if xsd_url == 'init':
        raise Exception( 'xsi:schemaLocation not found in the XML file.' )
    else:
        if 'http:' in xsd_url:
            xsd_url = xsd_url.replace('http:', 'https:')
        if 'www.loc.gov/mods' in xsd_url:
            xsd_url = xsd_url.replace('www.loc.gov/mods', 'www.loc.gov/standards/mods')
        if '.xsd">' in xsd_url:
            xsd_url = xsd_url.replace('.xsd">', '.xsd')
    log.debug( f'updated xsd_url, ``{xsd_url}``' )
    return xsd_url


def download_xsd_to_string( url: str ) -> str:
    log.debug( f'starting to access url, ``{url}``' )
    try:
        with urlopen(url) as response:
            xsd_str = response.read().decode()
            log.debug( 'returning xsd_str' )
            return xsd_str
    except Exception as e:
        raise Exception( f'failed to download XSD file from {url}. Error: {e}' )


if __name__ == '__main__':
    ## set up argparser
    parser = argparse.ArgumentParser(description='validate MODS.')
    parser.add_argument('--input_path', type=str, help='Path to the xml file')
    args = parser.parse_args()
    log.debug( f'args: {args}' )
    ## get input path
    input_path = args.input_path if args.input_path else "./am_me_items_mods/HH020005_0001_mods.xml"
    log.debug( f'input_path: {input_path}' )
    ## get to work
    validate_mods( input_path )
    log.debug( 'done' )
    