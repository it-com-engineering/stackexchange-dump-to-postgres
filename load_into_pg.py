#!/usr/bin/env python
import sys
import time
import argparse
import psycopg2 as pg
import row_processor as Processor

# Special rules needed for certain tables (esp. for old database dumps)
specialRules = {
    ('Posts', 'ViewCount'): "NULLIF(%(ViewCount)s, '')::int"
}

def _makeDefValues(keys):
    """Returns a dictionary containing None for all keys."""
    return dict(( (k, None) for k in keys ))

def _createMogrificationTemplate(table, keys):
    """Return the template string for mogrification for the given keys."""
    return ( '(' +
             ', '.join( [ '%(' + k + ')s' if (table, k) not in specialRules else specialRules[table, k]
                          for k in keys
                        ]
                      ) +
             ')'
           )

def _createCmdTuple(cursor, keys, templ, attribs):
    """Use the cursor to mogrify a tuple of data.
    The passed data in `attribs` is augmented with default data (NULLs) and the
    order of data in the tuple is the same as in the list of `keys`. The
    `cursor` is used toe mogrify the data and the `templ` is the template used
    for the mogrification.
    """
    defs = _makeDefValues(keys)
    defs.update(attribs)
    return cursor.mogrify(templ, defs)

def handleTable(table, keys, dbname, mbDbFile, mbHost, mbPort, mbUsername, mbPassword):
    """Handle the table including the post/pre processing."""
    dbFile     = mbDbFile if mbDbFile is not None else table + '.xml'
    tmpl       = _createMogrificationTemplate(table, keys)
    start_time = time.time()

    try:
        pre    = file('./sql/' + table + '_pre.sql').read()
        post   = file('./sql/' + table + '_post.sql').read()
    except IOError as e:
        print >> sys.stderr, "Could not load pre/post sql. Are you running from the correct path?"
        sys.exit(-1)

    dbConnectionParam = "dbname={}".format(dbname)

    if mbPort is not None:
        dbConnectionParam += ' port={}'.format(mbPort)

    if mbHost is not None:
        dbConnectionParam += ' host={}'.format(mbHost)

    # TODO Is the escaping done here correct?
    if mbUsername is not None:
        dbConnectionParam += ' user={}'.format(mbUsername)

    # TODO Is the escaping done here correct?
    if mbPassword is not None:
        dbConnectionParam += ' password={}'.format(mbPassword)

    try:
        with pg.connect(dbConnectionParam) as conn:
            with conn.cursor() as cur:
                try:
                    with open(dbFile) as xml:
                        # Pre-processing (dropping/creation of tables)
                        print 'Pre-processing ...'
                        if pre != '':
                            cur.execute(pre)
                            conn.commit()
                        print 'Pre-processing took {} seconds'.format(time.time() - start_time)

                        # Handle content of the table
                        start_time = time.time()
                        print 'Processing data ...'
                        for rows in Processor.batch(Processor.parse(xml), 500):
                            valuesStr = ',\n'.join(
                                            [ _createCmdTuple(cur, keys, tmpl, row_attribs)
                                                for row_attribs in rows
                                            ]
                                        )

                            if len(valuesStr) > 0:
                                cmd = 'INSERT INTO ' + table + \
                                      ' VALUES\n' + valuesStr + ';'
                                cur.execute(cmd)
                                conn.commit()
                        print 'Table processing took {} seconds'.format(time.time() - start_time)

                        # Post-processing (creation of indexes)
                        start_time = time.time()
                        print 'Post processing ...'
                        if post != '':
                            cur.execute(post)
                            conn.commit()
                        print 'Post processing took {} seconds'.format(time.time() - start_time)

                except IOError as e:
                    print >> sys.stderr, "Could not read from file {}.".format(dbFile)
                    print >> sys.stderr, "IOError: {0}".format(e.strerror)
    except pg.Error as e:
        print >> sys.stderr, "Error in dealing with the database."
        print >> sys.stderr, "pg.Error ({0}): {1}".format(e.pgcode, e.pgerror)
        print >> sys.stderr, str(e)
    except pg.Warning as w:
        print >> sys.stderr, "Warning from the database."
        print >> sys.stderr, "pg.Warning: {0}".format(str(w))



#############################################################

all_tables = ['Users', 'Badges', 'Posts', 'Tags', 'Votes','PostLinks','Comments']


parser = argparse.ArgumentParser()
parser.add_argument( '-t', '--table'
                   , help    = 'The table to work on.'
                   , choices = ['Users', 'Badges', 'Posts', 'Tags', 'Votes','PostLinks','Comments']
                   , default = None
                   )

parser.add_argument( '-d', '--dbname'
                   , help    = 'Name of database to create the table in. The database must exist.'
                   , default = 'stackoverflow'
                   )

parser.add_argument( '-f', '--file'
                   , help    = 'Name of the file to extract data from.'
                   , default = None
                   )
                   
parser.add_argument( '--dir'
                   , help    = 'Name of the directory where XML files are.'
                   , default = None
                   )

parser.add_argument( '-u', '--username'
                   , help    = 'Username for the database.'
                   , default = None
                   )

parser.add_argument( '-p', '--password'
                   , help    = 'Password for the database.'
                   , default = None
                   )

parser.add_argument( '-P', '--port'
                   , help    = 'Port to connect with the database on.'
                   , default = None
                   )

parser.add_argument( '-H', '--host'
                   , help    = 'Hostname for the database.'
                   , default = None
                   )

parser.add_argument( '--with-post-body'
                   , help   = 'Import the posts with the post body. Only used if importing Posts.xml'
                   , action = 'store_true'
                   , default = False
                   )

parser.add_argument( '--with-comment-text'
                   , help   = 'Import the comments with the comment text. Only used if importing Comments.xml'
                   , action = 'store_true'
                   , default = False
                   )

parser.add_argument( '--suppress-drop-warning'
                   , help    = 'Whether or not to suppress table drop confirmations.'
                   , action  = 'store_true'
                   , default = False
                   )

parser.add_argument( '--all'
                   , help    = 'Import all XML files, including Post bodies and Comment text.'
                   , action  = 'store_true'
                   , default = False
                   )
                   
                   
args = parser.parse_args()

selected_table = args.table
        
KeysHash = {}

KeysHash['Users'] = [
        'Id'
      , 'Reputation'
      , 'CreationDate'
      , 'DisplayName'
      , 'LastAccessDate'
      , 'WebsiteUrl'
      , 'Location'
      , 'AboutMe'
      , 'Views'
      , 'UpVotes'
      , 'DownVotes'
      , 'ProfileImageUrl'
      , 'Age'
      , 'AccountId'
    ]
    
KeysHash['Badges'] = [
        'Id'
      , 'UserId'
      , 'Name'
      , 'Date'
    ]

KeysHash['PostLinks'] =[
        'Id'
      , 'CreationDate'
      , 'PostId'
      , 'RelatedPostId'
      , 'LinkTypeId'
    ]

KeysHash['Comments'] = [
        'Id'
      , 'PostId'
      , 'Score'
      , 'Text'
      , 'CreationDate'
      , 'UserId'
    ]

KeysHash['Votes'] = [
        'Id'
      , 'PostId'
      , 'VoteTypeId'
      , 'UserId'
      , 'CreationDate'
      , 'BountyAmount'
    ]
    
KeysHash['Posts'] = [
        'Id'
      , 'PostTypeId'
      , 'AcceptedAnswerId'
      , 'ParentId'
      , 'CreationDate'
      , 'Score'
      , 'ViewCount'
      , 'Body'
      , 'OwnerUserId'
      , 'LastEditorUserId'
      , 'LastEditorDisplayName'
      , 'LastEditDate'
      , 'LastActivityDate'
      , 'Title'
      , 'Tags'
      , 'AnswerCount'
      , 'CommentCount'
      , 'FavoriteCount'
      , 'ClosedDate'
      , 'CommunityOwnedDate'
    ]

KeysHash['Tags'] = [
        'Id'
      , 'TagName'
      , 'Count'
      , 'ExcerptPostId'
      , 'WikiPostId'
    ]
	
if args.all:
	tables=all_tables
	_name = "All tables"
else:
	tables=[selected_table]
	_name = "the " + selected_table + " table"
	

if not args.with_comment_text:
    specialRules[('Comments', 'Text')] = 'NULL'

if not args.with_post_body:
    specialRules[('Posts', 'Body')] = 'NULL'

choice = 'no'

if args.suppress_drop_warning:
	choice = "y"
else:
	choice = raw_input('This will drop {}. Are you sure [y/n]?'.format(_name))
	
# TODO - need to handle args.suppress_drop_warning:

if len(choice) > 0 and choice[0].lower() == 'y':			
			
	for _table in tables:
	
		if len(tables) > 1 and args.dir != None:
			_file=args.dir + "/" + _table + ".xml"
		else:
			_file=args.file

		print '\nProcessing ' + _table + ' table ...\n'
		handleTable(_table, KeysHash[_table], args.dbname, _file, args.host, args.port, args.username, args.password)

else:
	print "Cancelled."
