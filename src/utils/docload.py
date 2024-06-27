#!/usr/bin/env python3

# Script to load documentation from a tarball or source directory

import sys
import os
import tarfile
import csv
import io
import re
import tidylib
from optparse import OptionParser
from configparser import ConfigParser
import psycopg2
import logging
from psycopg2.extras import LoggingConnection

logging.getLogger("loggerinformation")
db_settings = {
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "database": "test_db"
}

# the Bootstrap grid classes that are added onto any images that are rendered in the docs
BOOTSTRAP_FIGURE_CLASS = r'<div\1class="figure col-xl-8 col-lg-10 col-md-12"'
# a counter that keeps track of the total number of pages (HTML, SVG) that are loaded
# into the database
pagecount = 0
# if set to "True" -- mutes any output from the script. Controlled by an option
quiet = False
# if set to "True" -- outputs extra much data (row-per-file)
verbose = False
# regular expression used to search and extract the title on a given piece of
# documentation, for further use in the application
re_titlematch = re.compile(r'<title\s*>([^<]+)</title\s*>', re.IGNORECASE)
# regular expression used to find any images that are in the HTML and apply
# additional bootstrap classes
re_figure_match = re.compile('<div([^<>]+)class="figure"', re.IGNORECASE)


# Load a single page
def load_doc_file(filename, f, c):
    """Prepares and loads a HTML file for import into the documentation database"""
    tidyopts = dict(
        drop_proprietary_attributes=1,
        alt_text='',
        hide_comments=1,
        output_xhtml=1,
        show_body_only=1,
        clean=1,
        char_encoding='utf8',
        indent='auto',
    )

    # Postgres 10 started using xml toolchain and now produces docmentation in utf8. So we need
    # to figure out which version it is.
    rawcontents = f.read()
    rawfirst = rawcontents[:50].decode('utf8', errors='ignore')
    if rawfirst.startswith('<?xml version="1.0" encoding="UTF-8"'):
        # Version 10, use utf8
        encoding = 'utf-8'
        # XML builds also don't need clean=1, and that one adds some interesting CSS properties
        del tidyopts['clean']
    else:
        encoding = 'latin1'

    # PostgreSQL prior to 11 used an older toolchain to build the docs, which does not support
    # indented HTML. So turn it off on those, but keep it on the newer versions where it works,
    # because it makes things a lot easier to debug.
    if float(ver) < 11 and float(ver) > 0:
        tidyopts['indent'] = 'no'

    # convert the raw contents to the appropriate encoding for the content that will
    # be stored in the database
    contents = str(rawcontents, encoding)

    # extract the title of the page, which is rendered in a few places in the documentation
    tm = re_titlematch.search(contents)
    if tm:
        title = tm.group(1)
    else:
        title = ""

    # find any images that are embedded in the HTML and add in the Bootstrap grid classes
    # in order to ensure they are able to display responsively
    contents = re_figure_match.sub(BOOTSTRAP_FIGURE_CLASS, contents)

    # in verbose mode, output the (filename, title) pair of the docpage that is being processed
    if verbose:
        print("--- file: %s (%s) ---" % (filename, title))

    # run libtidy on the content
    (html, errors) = tidylib.tidy_document(contents, options=tidyopts)

    # add all of the information to the CSV that will be used to load the updated
    # documentation pages into the database
    c.writerow([filename, ver, title, html])


def load_svg_file(filename, f, c):
    """Prepares and loads a SVG file for import into the documentation database"""
    # this is fairly straightforward: we just need to load the contents, and
    # set the "title" as NULL as there is no title tag
    svg = f.read()
    c.writerow([filename, ver, None, svg.decode('utf-8')])


def parse_tarfile(tarfilename):
    # this regular expression is for "newer" versions of PostgreSQL that keep all of
    # the HTML documentation built out
    re_htmlfile = re.compile('[^/]*/doc/src/sgml/html/.*')
    # this regular expression is for "older" versions of PostgreSQL that keep the
    # HTML documentation in a tarball within the tarball
    re_tarfile = re.compile('[^/]*/doc/postgres.tar.gz$')

    tf = tarfile.open(tarfilename)

    for member in tf:
        if re_htmlfile.match(member.name):
            yield member.name, lambda: tf.extractfile(member)
        elif re_tarfile.match(member.name):
            # older versions of PostgreSQL kept a tarball of the documentation within the source
            # tarball, and as such will go down this path
            f = tf.extractfile(member)
            inner_tar = tarfile.open(fileobj=f)
            for inner_member in inner_tar:
                # Some old versions have index.html as a symlink - so let's
                # just ignore all symlinks to be on the safe side.
                if inner_member.issym():
                    continue

                if inner_member.name.endswith('.html') or inner_member.name.endswith('.htm'):
                    yield inner_member.name, lambda: inner_tar.extractfile(inner_member)


def parse_directory(dirname):
    for fn in os.listdir(dirname):
        if fn.endswith('.html') or fn.endswith('.svg'):
            yield fn, lambda: open(os.path.join(dirname, fn), 'rb')


# Main execution
parser = OptionParser(
    usage="usage: %prog [options] <version> <tarfile|directory>")
parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                  help="Run quietly (no output at all)")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  help="Run verbosely")
parser.add_option("-g", "--git", type=str,
                  help="Specify git hash used to load")
(options, args) = parser.parse_args()

if len(args) != 2:
    parser.print_usage()
    sys.exit(1)

quiet = options.quiet
verbose = options.verbose

if verbose and quiet:
    print("Can't be both verbose and quiet at the same time!")
    sys.exit(1)

ver = args[0]
# def install_docs(version, file, mdl):
# global pagecount
# global ver
# args = [version, file]
# print('Version -> ', mdl.objects.all())
# ver = args[0]
# load the configuration that is used to connect to the database
config = ConfigParser()
config.read(os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'docload.ini'))

# Load a tarfile or a "naked" directory
print("file: ", args[1])
if os.path.isfile(args[1]):
    generator = parse_tarfile(args[1])
elif os.path.isdir(args[1]):
    generator = parse_directory(args[1])
else:
    print("File or directory %s not found" % args[1])
    sys.exit(1)


# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)
connection = psycopg2.connect(
    dbname="test_db", user="postgres", password="postgres", host="localhost")  # connection_factory=LoggingConnection)
# connection.initialize(logger)

if not quiet:
    print("Starting load of documentation for version %s." % (ver, ))

curs = connection.cursor()
curs.execute("SELECT * FROM core_version")
# x = curs.fetchall()
# print(x)
# Verify that the version exists, and what we're loading
curs.execute("SELECT current FROM core_version WHERE tree=%(v)s", {'v': ver})
r = curs.fetchall()
print(r)
if len(r) != 1:
    print("Version %s not found in the system, cannot load!" % ver)
    sys.exit(1)

iscurrent = r[0][0]

# begin creating a CSV that will be used to import the documentation into the database
s = io.StringIO()
c = csv.writer(s, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

# Import each page of documentation
for filename, getter in generator:
    filename = os.path.basename(filename)
    print(filename)
    f = getter()

    # determine if the file being loaded is an SVG or a regular doc file
    if filename.endswith('.svg'):
        load_svg_file(filename, f, c)
    else:
        load_doc_file(filename, f, c)

    # after successfully preparing the file for load, increase the page count
    pagecount += 1

print("Page count: ", pagecount)
if not quiet:
    print("Total parsed doc size: {:.1f} MB".format(s.tell() / (1024 * 1024)))

s.seek(0)

# Start loading the documentation into the database
# First, load the newly discovered documentation into a temporary table, where we
# can validate that we loaded exactly the number of docs that we thought we would,
# based on the page counter
curs.execute("CREATE TEMP TABLE docsload (file varchar(64) NOT NULL, version numeric(3,1) NOT NULL, title varchar(256) NOT NULL, content text)")
curs.copy_expert("COPY docsload FROM STDIN WITH CSV DELIMITER AS ';'", s)
if curs.rowcount != pagecount:
    print("Loaded invalid number of rows! {} rows for {} pages!".format(
        curs.rowcount, pagecount))
    sys.exit(1)

numchanges = 0

# If the previous step succeeded, delete all the documentation for the specified version
# and insert into / update the doc table the content that was loaded into the temporary table
curs.execute("DELETE FROM docs WHERE version=%(version)s AND NOT EXISTS (SELECT 1 FROM docsload WHERE docsload.file=docs.file)", {
    'version': ver,
})
numchanges += curs.rowcount
if not quiet:
    print("Deleted {} orphaned doc pages".format(curs.rowcount))

curs.execute("INSERT INTO docs (file, version, title, content) SELECT file, version, title, content FROM docsload WHERE NOT EXISTS (SELECT 1 FROM docs WHERE docs.file=docsload.file AND docs.version=%(version)s)", {
    'version': ver,
})
numchanges += curs.rowcount
if not quiet:
    print("Inserted {} new doc pages.".format(curs.rowcount))

curs.execute("UPDATE docs SET title=l.title, content=l.content FROM docsload l WHERE docs.version=%(version)s AND docs.file=l.file AND (docs.title != l.title OR docs.content != l.content)", {
    'version': ver,
})
numchanges += curs.rowcount
if not quiet:
    print("Updated {} changed doc pages.".format(curs.rowcount))

if numchanges > 0:
    # Update the docs loaded timestamp
    if ver == "0" and options.git:
        githash = options.git
    else:
        githash = ''

    curs.execute("UPDATE core_version SET docsloaded=CURRENT_TIMESTAMP, docsgit=%(git)s WHERE tree=%(v)s", {
        'v': ver,
        'git': githash,
    })

    # Issue varnish purge for all docs of this version
    if ver == "0":
        # Special handling of developer docs...
        ver = "devel"

    curs.execute("SELECT varnish_purge_xkey('pgdocs_{}')".format(ver))
    curs.execute("SELECT varnish_purge_xkey('pgdocs_all')")
    if iscurrent:
        curs.execute("SELECT varnish_purge_xkey('pgdocs_current')")

# ensure the changes are committed, and close the connection
connection.commit()
connection.close()

if not quiet:
    print("Done loading docs version %s (%i pages)." % (ver, pagecount))
