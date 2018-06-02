"""A Python-based utility to do:
A folder to folder comparison, displaying file names that are in either
one or the other folder, or in both folders.
Mirror folders, a quick&dirty backup with minimal sophistication,
allows one to selectively copy over only those files that are newer (or different)
in the source folder than in the destination folder
SRTonse, Created: 28th March 2018
"""

""" Modifications:
Version_Number = ("1.0.0", "(3/28/2018)"):  Original version
Version_Number = ("1.1.0", "(4/1/2018)"): Finessed the output
Version_Number = ("1.2.4", "(4/14/2018)"): --jeeva option. Better handling of assert in ProcessInputOptsnArgs 



-----------------End of Modifications-----------------
"""

Version_Number = ("1.3.5", "(5/31/2018)")
"""   
"""

"""ToDo:
Fix the diff programming to use MD5sum but in an economical fashion.
logging? Allow --log for people who want output to look at later.
Default value of opt.loglevel=False. If False then do not even start a
logger.
If in both folders,list whether the 2 files are identical, or whether differnt or
have different modification times. 
How to handle Shortcuts?
Threads? say 3 or 4? Only necessary if doing md5sum, using hashlib.md5,
currently I just use file size to determine if they are different, which
is not great.
"""
import os
import optparse
import shutil
from collections import Counter
from printindentwidth import PrintIndentWidth

#used for formatting of output for --compare
INDENT_INCREMENT = "   "
INDENT_ARROW = "|->"

L_listerrors = list()    #to contain names of any directories that could not be list'ed

class PathItem(object):
    """Hold the items being copied or compared:
    file name, mtime, md5sum, whether regular, link or dir file
    """
    def __init__(self, p):
        self.path = p

    def __str__(self):    #EGOF a print() class member func that prints using class dict()
        """EGOF print whatever attributes are available
        """
        S = "%s" % (self.path)
        for attrib in ["s_mtime", "d_mtime", "s_size", "d_size"]:
            if self.__dict__.has_key(attrib):  # EGOF class dict to check attribute existence
                S += "%s:%d  " % (attrib, self.__dict__[attrib])       
        return S
    
    def __repr__(self):
        S = "%s" % (self.path)
        return S

    #EGOF these 2 member functions are necessary because the instances are going to be set() members    
    def __hash__(self):
        return hash(self.path)     #customized use of file name itself as hash value for the class instance

    def __eq__(self, P):
        return self.path == P.path

#----------------------------------------------------------------------------
class DirSizeError(Exception): pass       #EGOF nice, not ungainly, exception example

#----------------------------------------------------------------------------

USAGE_MESSAGE = """
python jeeva.py [options] source_folder destination_folder

To be used for:
A) Comparing 2 folders. No copying is done. Displays file names that
   are in either one or the other or both folders.
   Display consists of 6 numbers:
   1) # regular files in source folder but not destination folder
   2) # in both source and dest
   3) # in dest but not source, 
   4,5,6) the same 3 corresponding values but for directories/folders")

B) Mirroring folders. Quick copy to backup with zero sophistication.
Allows one to selectively copy over to the destination folder only those files
that are newer in source than in the destination folder. Can recursively descend directory tree 
"""

def DefineInputOptsnArgs(Version_Number_Date):
    """Define the command line options and arguments here
    """
    CLOP = optparse.OptionParser(version=Version_Number_Date,usage=USAGE_MESSAGE)     #command line options
    #EGOF Divide optparse into Option groups, easier to read Help
    CLOP.add_option("-r", "--recursive", action="store_true", dest="recursive", default=False,
                    help='Compare or Copy recursively down a directory structure. Default = False')
    CLOP.add_option("--jeeva", action="store_true", dest="jeeva", default=False,
                    help='A little trivia on why it is called Jeeva')
    compare = optparse.OptionGroup(CLOP,"Solely compare-related options")
    compare.add_option("--compare", action="store_true", dest="compare", default=False,
                    help="Compare contents of source and destination folders. No copying is done. See docs above. ")
    compare.add_option("--details", action="store", dest="details", type="string", default="no",
                    help="Detailed output showing filenames for --compare. DETAILS should be one of: yes | no (default) | query | or a mask e.g. \"nynyny\" where each y/n (yes/no) corresponds to the 6 values described above for --compare")
    CLOP.add_option_group(compare)           #EGOF using option groups in optparse module

    copygroup = optparse.OptionGroup(CLOP,"Solely copy-related options")
    copygroup.add_option("--copy", action="store", dest="copyopt", type="string", default="",
                    help="Copy files from source to dest. COPYOPT should be one of: all | newer | update. No default. \"all\" overwrites dest with source. \"newer\" copies regular files that are newer in source. Files that are in source but not in dest are not copied. \"update\" additionally copies those files, plus, if --mkdir option permits, directories are also created and copied.")
    #CLOP.add_option("--copy", action="store", dest="copyopt", type="string", default="",
    #                help="Copy files from source to dest. COPYOPT should be one of: all | newer | diff | nad (newer and different) | nod (newer or different). \"newer\" pertains to the source file being newer. Files that are in source but not in dest will be copied only if \"all\" is used.")
    copygroup.add_option("--mkdir", action="store", dest="mkdir", type="string", default="query",
                    help="Create destination directory/folder if it does not exist. MKDIR should be one of: yes | no | query(default)")
    copygroup.add_option("--dryrun", action="store_true", dest="dryrun", default=False,
                    help='Test mode: Code will run without actually copying any files or changing anything. Only meaningful for --copy')
    CLOP.add_option_group(copygroup)
    #CLOP.add_option("--log", action="store", dest="loglevel", type="string", default="INFO",
    #                help="Specify logging verbosity level (DEBUG/ INFO(default)/ WARNING/ ERROR/ FATAL) on command line")
    return CLOP
#----------------------------------------------------------------------------

def ProcessInputOptsnArgs(clop):
    """Process the input command line opts and args
    """
    opts,args = clop.parse_args()
    if opts.jeeva:
        S =\
"""Why \"Jeeva\"?
Jeeva was a \"goonda\" who terrorised everybody in my neighbourhood
when I was a kid. An auto-rickshaw driver by profession. I saw
him once take on 4 guys, viciously beating them up with a wrench, then
lean against a wall, fold his arms and scream in his broken English,
\"You bring friends? Go! Bring friends! I wait!\"
Needless to say, his adversories just slunk away, figuring that one thrashing
a day was plenty. Jeeva made a lasting impression on me, although 40 years
have passed. This unique piece of software, (unique in that no other
Python 2.x script has ever been named after a goonda autorickshaw driver)
is dedicated to his memory."""
        print S
        os._exit(0)
    #test of validity of input opts/args
    try:  #EGOF use AssertionError exception to quickly jump out of program
        assert len(args) == 2, "Exactly 2 args, a source folder and a destination folder are required. Exiting."
        assert os.path.exists(args[0]), "Source folder does not exist"
        assert os.path.isdir(args[0]), "Source folder is not a folder/directory"
        assert os.path.isdir(args[1]), "Destination folder is not a folder/directory"
        """yesno = raw_input("Destination folder does not exist. Would you like to create it now? (Y/N)")
                if yesno == "Y" or yesno == "y":
                if opts.dryrun:
                    print "Dryrun: os.mkdir(%s)" % args[1]
                else:
                    os.mkdir(args[1])
                else:
                assert False,"OK fine, whatever, exiting."
        """
        #EGOF Exclusive OR
        assert (opts.compare and not opts.copyopt) or (not opts.compare and opts.copyopt),\
        "Either --compare or --copy required, not neither, not both. See help (-h)"
        
        #check that --details options are OK       
        Odu = opts.details.upper()
        #possible that a 6-char mask consisting eg of "ynynny" was input
        d1 = Counter(Odu)               #EGOF collections module Counter func
        good_mask = (d1["Y"] + d1["N"]) == 6
        assert (Odu=="YES") or (Odu=="NO") or (Odu=="QUERY") or good_mask, "Invalid value for --details: %s" % opts.details 

    except AssertionError, X:
        print X
        os._exit(1)
    except:
        raise             #twas some other type of exception

    return opts, args[0], args[1]
#--------------------------------------------------------------------------

def SetOfRegFiles(dir1):
    """Return a set of regular file names from folder dir1
    """
    myset = set()
    try:
        for f in os.listdir(dir1):
            if os.path.isfile(os.path.join(dir1, f)):            #only members that are regular files
                myset.add(f)
    except:
        #the dir contents could not be list'ed. Store for possible display at end of running
        L_listerrors.append(dir1)
    return myset
#--------------------------------------------------------------------------

def SetOfDirFiles(dir1):
    """Return a set of directory file names from folder dir1
    """
    myset = set()
    try:
        for f in os.listdir(dir1):
            if os.path.isdir(os.path.join(dir1, f)):            #only members that are directory files
                myset.add(f)
    except:
        #the dir contents could not be list'ed. Store for possible display at end of running
        L_listerrors.append(dir1)
    return myset
#--------------------------------------------------------------------------

def CompareFolder(source, dest, opts, indent):
    """A folder to folder comparison, displaying number of files (or file names)
        that are in either
        one or the other folder, or in both folders. User can decide with CL args
        what level of detail to output with --details
    """
    def Print_Details(sourcenotdestReg, sourceanddestReg, destnotsourceReg,
                      sourcenotdestDir, sourceanddestDir, destnotsourceDir, opts, indent):
        """Print details if and at level the user has requested with --details
        """
        def PrintContent(S_in, title):
            """Print in comma sep form. S_in=set() of file names. title=string
            """
            print indent, title
            PrintIndentWidth(S_in, len(indent), width=65)
        #------------------------------
        print_detail = (opts.details == "yes")
        if opts.details == "query":
            print_detail = raw_input(indent+"List the actual filenames? (Y/y)").upper() == "Y"
        if print_detail:
            T1 = ( (sourcenotdestReg, "Files in Source but not in Destination folder:"),
            (sourceanddestReg, "File names common to Source and Destination folders:"),
            (destnotsourceReg, "Files not in Source but in Destination folder:"),
            (sourcenotdestDir, "Dirs in Source but not in Destination folder:"),
            (sourceanddestDir, "Dir names common to Source and Destination folders:"),
            (destnotsourceDir, "Dirs not in Source but in Destination folder:") )
            for t in T1:
                if len(t[0]): PrintContent(t[0].copy(), t[1])
            """if len(sourcenotdestReg): PrintContent(sourcenotdestReg.copy(), "Files in Source but not in Destination folder:")
            if len(sourceanddestReg): PrintContent(sourceanddestReg.copy(), "File names common to Source and Destination folders:")
            if len(destnotsourceReg):PrintContent(destnotsourceReg.copy(), "Files not in Source but in Destination folder:")
            if len(sourcenotdestDir): PrintContent(sourcenotdestDir.copy(), "Dirs in Source but not in Destination folder:")
            if len(sourceanddestDir): PrintContent(sourceanddestDir.copy(), "Dir names common to Source and Destination folders:")
            if len(destnotsourceDir):PrintContent(destnotsourceDir.copy(), "Dirs not in Source but in Destination folder:")"""
        #See if a mask of y's and n's was given: Should be a 6 letter string consisting ONLY of Y and N, case-insenstive
        if len(opts.details) == 6:
            mask = opts.details.upper()
            d1 = Counter(mask)
            if d1["Y"] + d1["N"] == 6:
                T1 = ( (sourcenotdestReg, "Files in Source but not in Destination folder:"),
                (sourceanddestReg, "File names common to Source and Destination folders:"),
                (destnotsourceReg, "Files not in Source but in Destination folder:"),
                (sourcenotdestDir, "Dirs in Source but not in Destination folder:"),
                (sourceanddestDir, "Dir names common to Source and Destination folders:"),
                (destnotsourceDir, "Dirs not in Source but in Destination folder:") )
                for i in range(5):
                    if mask[i]=="Y" and len(T1[i][0]): PrintContent(T1[i][0].copy(), T1[i][1])
                """"i += 1
                if mask[i]=="Y" and len(sourceanddestReg): PrintContent(sourceanddestReg.copy(), "File names common to Source and Destination folders:")
                i += 1
                if mask[i]=="Y" and len(destnotsourceReg):PrintContent(destnotsourceReg.copy(), "Files not in Source but in Destination folder:")
                i += 1
                if mask[i]=="Y" and len(sourcenotdestDir): PrintContent(sourcenotdestDir.copy(), "Dirs in Source but not in Destination folder:")
                i += 1
                if mask[i]=="Y" and len(sourceanddestDir): PrintContent(sourceanddestDir.copy(), "Dir names common to Source and Destination folders:")
                i += 1
                if mask[i]=="Y" and len(destnotsourceDir):PrintContent(destnotsourceDir.copy(), "Dirs not in Source but in Destination folder:")"""

    #------------------------------------------------
    #indent is False on first call
    if not bool(indent): print "Source folder:%s        Destination folder:%s" % (source, dest)

    set_source = SetOfRegFiles(source)      #set of files in Source folder
    set_dest = SetOfRegFiles(dest)      #set of files in Destination folder
    sourcenotdestReg = set_source.difference(set_dest)
    destnotsourceReg = set_dest.difference(set_source)
    sourceanddestReg = set_source.intersection(set_dest)

    set_source = SetOfDirFiles(source)      #set of dir files in Source folder
    set_dest = SetOfDirFiles(dest)      #set of dir files in Dest folder
    sourcenotdestDir = set_source.difference(set_dest)
    destnotsourceDir = set_dest.difference(set_source)  #EGOF set() difference. A and not B
    sourceanddestDir = set_source.intersection(set_dest)  #EGOF set() intersection. A and B

    #indent is False on first call
    if bool(indent):
        indent_arrow = INDENT_ARROW
    else:
        indent_arrow = ""

    """output: indentation, Path, 6 numbers: 1) # regular files in source folder but not destination folder
       2) # in both source and dest 3) # in dest but not source,
       4,5,6) the same 3 corresponding values but for directories/folders")
    """
    print "%s%s%s (%i,%i,%i ; %i,%i,%i)" % (indent, indent_arrow, os.path.basename(source), 
                                            len(sourcenotdestReg), len(sourceanddestReg), len(destnotsourceReg),
                                            len(sourcenotdestDir), len(sourceanddestDir), len(destnotsourceDir))
    #This will return output if the --details CL opt says to:
    Print_Details(sourcenotdestReg, sourceanddestReg, destnotsourceReg,
                  sourcenotdestDir, sourceanddestDir, destnotsourceDir, opts, indent)
    return sourceanddestDir   #for use by calling routine Enter_dir to descend dir tree recursively
#--------------------------------------------------------------------------

def CopyFolder(source, dest, opts, indent):
    """Copy files from Source to Destination, depending on value of opts.copyopt, opts.recursive
        and opts.mkdir
    """
    def SetupSets(s,d):
        """Setup sets of Pathitem instances for the source dir and dest
        for regular and dir files
        For regular files and for directory files, return a set of files
        in Source but not Dest and a set of files in Source AND in Dest
        """
        #regular files
        set_sReg = SetOfRegFiles(s) 
        set_dReg = SetOfRegFiles(d)
        set_spReg = set(); set_dpReg = set()
        #EGOF a set() containing class instances. Class should define __hash__ and __eq__
        for f in set_sReg:
            set_spReg.add(PathItem(f))
        for f in set_dReg:
            set_dpReg.add(PathItem(f))
        #directory files
        set_sDir = SetOfDirFiles(s)
        set_dDir = SetOfDirFiles(d)
        set_spDir = set(); set_dpDir = set()
        for f in set_sDir:
            set_spDir.add(PathItem(f))
        for f in set_dDir:
            set_dpDir.add(PathItem(f))
        return set_spReg.difference(set_dpReg), set_spReg.intersection(set_dpReg),\
            set_spDir.difference(set_dpDir), set_spDir.intersection(set_dpDir) 
    #---------------------------

    def CopyorDryrun(source, dest, fn, dryrun, indent):
        """Do a copy of source/fn to dest/fn. If dryrun is true then just pretend to copy
        """
        if dryrun:
            print "%sDryrun: shutil.copyfile(%s, %s)" % (indent, os.path.join(source, fn), os.path.join(dest, fn))
        else:
            try:
                shutil.copyfile(os.path.join(source, fn), os.path.join(dest, fn))
            except Exception, X:
                print indent, X
    #----------------------------
    
    #Whole funny business with S_title is because I do not want to print it unless some
    #specific action occured. Otherwise the output is too verbose and conists mainly of
    #meaningless S_titles
    S_title = "%sSource folder:%s.   Destination folder:%s\n" % (indent, source, dest)
    #print indent, "Source folder:%s.   Destination folder:%s" % (source, dest)
    copyopt = opts.copyopt
    if copyopt == "all":
        if opts.recursive:
            if raw_input("Copying all files from Source to Dest.\n Will delete existing Dest folder %s and write new one.\n Continue? (YES/yes)" % dest).upper() == "YES":
                import time
                if opts.dryrun:
                    print S_title, "Dryrun: shutil.rmtree(%s)" % dest
                    S_title = ""
                    print "sleeping 2 secs"
                    time.sleep(2)     #necessary otherwise the rmtree is not regsitered with Windows OS!
                    print "Dryrun: shutil.copytree(%s, %s)" % (source, dest)
                else:
                    shutil.rmtree(dest)
                    time.sleep(2)     #necessary otherwise the rmtree is not regsitered with Windows OS!
                    shutil.copytree(source, dest)
            else:
                os._exit(0)
        else:
            set_source = SetOfRegFiles(source)       #set of file names in Source folder
            icount = 0
            for f in set_source:
                CopyorDryrun(source, dest, f, opts.dryrun, indent)
                icount += 1
            print S_title, "Copied %d files" % icount
            S_title = ""
        return None           #no need to return set of dir files common to source and dest

    #For remaining options need more than merely file name, so use the Pathitem class as set member
    elif copyopt == "newer" or copyopt == "update":
        #the following 4 sets are sets of Pathitems:
        set_sourcenotdestReg, set_sourceanddestReg, set_sourcenotdestDir, set_sourceanddestDir  = SetupSets(source, dest)
        
        #add mtimes to the PathItem for checking later
        for p in set_sourceanddestReg:
            sfn = os.path.join(source, p.path) #source file name
            dfn = os.path.join(dest, p.path)   #dest file name
            p.s_mtime =  int(os.path.getmtime(sfn))
            p.d_mtime =  int(os.path.getmtime(dfn))
        #actual copy/dryrun starts here
        icount = 0
        for p in set_sourceanddestReg:
            if p.s_mtime > p.d_mtime:
                if S_title: print S_title
                S_title = ""
                CopyorDryrun(source, dest, p.path, opts.dryrun, indent)
                icount += 1
        if icount:
            print S_title, indent, "Copied %d files that are newer in Source" % icount
            S_title = ""
        
        if copyopt == "update":
            #copy all the regular files in set_sourcenotdestReg
            icount = 0
            for p in set_sourcenotdestReg:
                if S_title: print S_title
                S_title = ""
                CopyorDryrun(source, dest, p.path, opts.dryrun, indent)
                icount += 1
            if icount:
                print S_title, indent, "Copied %d files that were in Source but not in Dest" % icount
                S_title = ""
            
            if opts.recursive:
                #create directories in set_sourcenotdestDir as subdirs of dest
                for p in set_sourcenotdestDir:
                    sourcepath = os.path.join(source, p.path)
                    destpath = os.path.join(dest, p.path)
                    assert not os.path.exists(destpath), "%s should not exist" % destpath
                    if opts.mkdir == "yes":
                        do_copytree = True
                    elif opts.mkdir == "no":
                        do_copytree = False
                    elif opts.mkdir == "query":
                        do_copytree = raw_input("%sDestination folder %s does not exist. Would you like to create it now? (Y/N)" % (S_title, destpath)).upper() == "Y"
                        S_title = ""
                    if do_copytree:
                        if opts.dryrun:
                            print S_title, indent, "Dryrun: shutil.copytree(%s, %s)" % (sourcepath, destpath)
                            S_title = ""
                        else:
                            try:
                                print S_title, indent, "Directory copy %s to  %s" % (sourcepath, destpath)
                                S_title = ""
                                shutil.copytree(sourcepath, destpath)
                            except:
                                print S_title, indent, "Failed Directory copy %s to  %s" % (sourcepath, destpath)
                                S_title = ""
                                
    else:
        raise Exception("An invalid option following for --copy was given: %s" % copyopt)

    #return a set of dir names that are common to source and dest so that Enter_dir can use
    sourceanddestDir = set()
    for s in set_sourceanddestDir:
        sourceanddestDir.add(s.path)

    return sourceanddestDir   #for use by calling routine Enter_dir to descend dir tree recursively

    """OLD CODE: KEEP IN ASE WANT TO USE --DIFF EVER
        elif copyopt == "newer" or copyopt == "diff" or copyopt == "nod" or copyopt == "nad":
        set_sourcenotdestReg, set_sourceanddestReg, set_sourcenotdestDir, set_sourceanddestDir  = SetupSets(source, dest)

        #first copy all the files in set_sourcenotdest, as no checking is required for those
        icount = 0
        for p in set_sourcenotdest:
            CopyorDryrun(source, dest, p.path, opts.dryrun)
            icount += 1
        print "Copied %d files that were in Source but not in Dest" % icount
        
        #add mtimes or size in bytes to the PathItem for checking later
        for p in set_sourceanddest:
            sfn = os.path.join(source, p.path) #source file name
            dfn = os.path.join(dest, p.path)   #dest file name
            if copyopt == "newer" or copyopt == "nod" or copyopt == "nad":
                p.s_mtime =  int(os.path.getmtime(sfn))
                p.d_mtime =  int(os.path.getmtime(dfn))
            if copyopt == "diff" or copyopt == "nod" or copyopt == "nad":
                try:
                    stats = os.stat(sfn)       #EGOF getting file details (size etc) with os.stat
                    p.s_size = stats[6]
                except:
                    raise DirSizeError('Cannot stat %s'% p.path)
                try:
                    stats = os.stat(dfn)       #EGOF getting file details (size etc) with os.stat
                    p.d_size = stats[6]
                except:
                    raise DirSizeError('Cannot stat %s'% p.path)
        #actual copy/dryrun starts here
        icount = 0
        if copyopt == "newer":
            print "Any files that are newer in source"
            for p in set_sourceanddest:
                if p.s_mtime > p.d_mtime:
                    CopyorDryrun(source, dest, p.path, opts.dryrun)
                    icount += 1
        elif copyopt == "diff":
            print "Any files that differ"
            for p in set_sourceanddest:
                if p.s_size != p.d_size:
                    CopyorDryrun(source, dest, p.path, opts.dryrun)
                    icount += 1
        elif copyopt == "nod":
            print "Any files that are newer or differ"
            for p in set_sourceanddest:
                if (p.s_mtime > p.d_mtime) or (p.s_size != p.d_size):
                    CopyorDryrun(source, dest, p.path, opts.dryrun)
                    icount += 1
        elif copyopt == "nad":
            print "Any files that are newer and differ"
            for p in set_sourceanddest:
                if (p.s_mtime > p.d_mtime) and (p.s_size != p.d_size):
                    CopyorDryrun(source, dest, p.path, opts.dryrun)
                    icount += 1
        print "Copied %d files" % icount
    else:
        raise Exception("An invalid option following for --copy was given: %s" % copyopt)
    return sourceanddestDir   #for use by calling routine Enter_dir to descend dir tree recursively
    """

#--------------------------------------------------------------------------
def Enter_dir(source, dest, opts, indent):
    """ Get a list and size of all names of files and subdirectories in directory source
        Recursively go down
    """
    if opts.compare:
        sourceanddestDir = CompareFolder(source, dest, opts, indent)
    elif opts.copyopt:
        sourceanddestDir = CopyFolder(source, dest, opts, indent)
    if opts.copyopt == "all" or not opts.recursive:
        return

    #recursive descent into directories
    for item in sourceanddestDir:
        # if item is a sub-directory, ensure that it exists, and that a corr item exists
        # in the destination, and then go into it
        sourcepath = os.path.join(source, item)
        destpath = os.path.join(dest, item)
        Enter_dir(sourcepath, destpath, opts, indent+INDENT_INCREMENT)

    """try:
        dir_list = os.listdir(source)
    except:
        # If source is a directory, we probably had permission problems
        if os.path.isdir(source):
            #the dir contents could not be list'ed. Store for possible display at end of running
            L_listerrors.append(source)
            return
        else: # otherwise, just re-raise the error so that it propagates, as could be serious
            raise
    for item in dir_list:
        # if item is a sub-directory, ensure that it exists, and that a corr item exists
        # in the destination, and then go into it
        sourcepath = os.path.join(source, item)
        if os.path.isdir(sourcepath):
            destpath = os.path.join(dest, item)
            #if destpath exists and is a dir file, go ahead. If it does not exist and
            #opts.mkdir permits, then create a new dir and go ahead and copy to it.
            if os.path.exists(destpath) and os.path.isdir(destpath):
                Enter_dir(sourcepath, destpath, opts, indent+INDENT_INCREMENT)
            elif not os.path.exists(destpath) and opts.copyopt:
                if opts.mkdir == "yes":
                    if opts.dryrun:
                        print "Dryrun: os.mkdir(%s)" % destpath
                    else:
                        os.mkdir(destpath)
                elif opts.mkdir == "query":
                    if raw_input("Destination folder %s does not exist. Would you like to create it now? (Y/N)" % destpath).upper == "Y":
                        if opts.dryrun:
                            print "Dryrun: os.mkdir(%s)" % destpath
                        else:
                            os.mkdir(destpath)
                    else:
                        print "OK fine, whatever, not creating."
                if os.path.exists(destpath) and os.path.isdir(destpath):   #now it should exist
                    Enter_dir(sourcepath, destpath, opts, indent+INDENT_INCREMENT)
    """
    return
#-------------------------------------------------------------------------------

#--------------------------------------- main -----------------------------------
CLOP = DefineInputOptsnArgs(Version_Number[0]+Version_Number[1])  #Define the input command line opts and args. 
opts, source, dest = ProcessInputOptsnArgs(CLOP)
if opts.dryrun: print "Dryrun option is ON. NO actual copying will occur"

#Most work done here
indent = ""
Enter_dir(source, dest, opts, indent)

# finally, write out names of dirs that gave a problem
L_listerrors = set(L_listerrors)    #remove duplicate entries:
if len(L_listerrors):     #EGOF handling a raw_input yesno in one line, testing for uppercase Y
    if (raw_input("Warning: Unable to list %i directories. Show?(Y/y)" % len(L_listerrors)).upper() =="Y"):
        print "The following directories were not processed due to dir listing Errors"
        for d in L_listerrors:
            print d
