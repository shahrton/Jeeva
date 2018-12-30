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
Version_Number = ("1.3.6", "(7/9/2018)"): Removed --copy all
Version_Number = ("1.4.3", "(10/14/2018)") 2 new options: --sroot and --droot. If one is there then the
other has to be there, cannot just have one. Each has to be an existing folder. Execute Jeeva from
a folder below (or equal to) --sroot; that folder is Source. Jeeva look for a folder of the same
name and in a corresponding position below --droot. That will be Destination folder.
It will then proceed as usual to do a compare or a copy.  
Version_Number = ("1.4.4", "(10/16/2018)"): Minor bug: --details yyyyyy was not catching the 6th y.  
Version_Number = ("1.4.5", "(10/21/2018)"): Minor bug: --mkdir NO causing exception. Fixed by
lowercasing the option.

-----------------End of Modifications-----------------
"""

Version_Number = ("1.5.1", "(12/22/2018)")
"""   
Improve quality and readability of output for both compare and copy
Add --depth option for the --compare option only: Only compares d levels down the tree,
--recursive is unnecessary if this is used. 
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
New option -c for color. 
"""
import os
import optparse
import shutil
from collections import Counter
from printindentwidth import PrintIndentWidth

#used for formatting of output for --compare
INDENT_INCREMENT = "   "
INDENT_ARROW = "|->"
WIDTH_PRINTINDENTWIDTH = 65      #change this if want to narrow/widen output field for the --compare output

max_depth_reached = -1

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
OR
python jeeva.py [options] --sroot root_source_folder --droot root_destination_folder


To be used for:
A) Comparing 2 folders. No copying is done. Displays file names that
   are in either one or the other or both folders.
   The 6 numbers displayed after each folder name are:
   1) # regular files in source folder but not destination folder
   2) # in both source and dest
   3) # in dest but not source, 
   4,5,6) the same 3 corresponding values but for directories/folders

B) Mirroring folders. Quick copy for backing up with zero sophistication.
Allows one to selectively copy over to the destination folder only those files
that are newer in source than in the destination folder. Can recursively descend directory tree 
"""

def DefineInputOptsnArgs(Version_Number_Date):
    """Define the command line options and arguments here
    """
    CLOP = optparse.OptionParser(version=Version_Number_Date,usage=USAGE_MESSAGE)     #command line options
    #EGOF Divide optparse into Option groups, easier to read Help
    CLOP.add_option("--sroot", action="store", dest="source_root", default=False, type="string",
                    help='Location of root source folder. Default = False')
    CLOP.add_option("--droot", action="store", dest="dest_root", default=False, type="string",
                    help='Location of root destination folder. Default = False')
    CLOP.add_option("-r", "--recursive", action="store_true", dest="recursive", default=False,
                    help='Compare or Copy recursively down a directory structure. Default = False')
    CLOP.add_option("--jeeva", action="store_true", dest="jeeva", default=False,
                    help='A little trivia on why it is called Jeeva')
    
    compare = optparse.OptionGroup(CLOP,"Solely compare-related options")
    compare.add_option("--compare", action="store_true", dest="compare", default=False,
                    help="Compare contents of source and destination folders. No copying is done. See description earlier. ")
    compare.add_option("--details", action="store", dest="details", type="string", default="no",
                    help="Detailed output showing filenames for --compare. DETAILS should be one of: yes | no (default) | query | or a mask e.g. \"nynyny\" where each y/n (yes/no) corresponds to the 6 values described earlier for comparing")
    compare.add_option("-d", "--depth", action="store", type="int", dest = "depth", default=False,
                    help="Limit the # of directory-levels down for --compare display. --recursive unnecessary if this used")
    CLOP.add_option_group(compare)           #EGOF using option groups in optparse module


    copygroup = optparse.OptionGroup(CLOP,"Solely copy-related options")
    copygroup.add_option("--copy", action="store", dest="copyopt", type="string", default=False,
                    help="Copy files from source to dest. COPYOPT should be one of: mod | update. No default. \"mod\" copies regular files that are newer in source. Files that are in source but not in dest are not copied. \"update\" additionally copies those files, plus, if --mkdir option permits, directories are also created and copied.")
    #copygroup.add_option("--copy", action="store", dest="copyopt", type="string", default="",
    #                help="Copy files from source to dest. COPYOPT should be one of: all | newer | update. No default. \"all\" overwrites dest with source. \"newer\" copies regular files that are newer in source. Files that are in source but not in dest are not copied. \"update\" additionally copies those files, plus, if --mkdir option permits, directories are also created and copied.")
    copygroup.add_option("--mkdir", action="store", dest="mkdir", type="string", default="query",
                    help="Create destination directory/folder if it does not exist. MKDIR should be one of: yes | no | query(default)")
    copygroup.add_option("--dryrun", action="store_true", dest="dryrun", default=False,
                    help='Test mode: Code will run without actually copying any files or changing anything.')
    CLOP.add_option_group(copygroup)
    return CLOP
#----------------------------------------------------------------------------

def ProcessInputOptsnArgs(clop):
    """Process the input command line opts and args
    """
    def GetSourceDest(opts, args):
        """Test the validity of the input args/opts related to Source/Dest folders and return the 
        Source and Dest folder names 
        """
        try:
            assert (len(args)==2 and not opts.source_root and not opts.dest_root) or (len(args)==0 and opts.source_root and opts.dest_root),\
            "Either source/dest folder method OR root source/root dest method should be used, but not both.\
            \n Either specify Source and Destination folders as arguments or\
            \nroot Source and root Destination folders using --sroot and --droot respectively."
            if len(args)==2:
                source, dest = args      #using source/dest method
            else:
                #using root source/root dest method
                assert os.path.exists(opts.source_root), "Root Source folder does not exist"
                assert os.path.isdir(opts.source_root), "Root Source folder is not a folder/directory"
                assert os.path.exists(opts.dest_root), "Root Destination folder does not exist"
                assert os.path.isdir(opts.dest_root), "Root Destination folder is not a folder/directory"
                #get current location
                source = os.path.abspath(os.curdir)
                #get current location wrt root source
                opts.source_root = os.path.abspath(opts.source_root)
                rel_to_source = os.path.relpath(source, opts.source_root)
                #print "source, opts.source_root, rel_to_source", source, opts.source_root, rel_to_source
                #get destination location wrt root dest
                dest = os.path.join(opts.dest_root, rel_to_source)
                #print dest
                assert os.path.exists(dest), "Destination folder (%s) does not exist" % dest
                assert os.path.isdir(dest), "Destination folder (%s) is not a folder/directory" % dest
            return source, dest
        except AssertionError, X:
            print X
            os._exit(1)
    #------------------------
        
    opts,args = clop.parse_args()
    if opts.jeeva:
        S =\
"""Why \"Jeeva\"?\n
In Sanskrit \"Jeeva\" roughly translates as:
"a living being" or "an entity imbued with a life force".

Jeeva also hapened to be the name of a \"goonda\" who terrorised everybody
in my neighbourhood when I was a kid. He was an auto-rickshaw driver by
profession. I saw him once take on 4 guys, viciously beating them up with
a spanner (wrench), lean against a wall, fold his arms and scream
in his broken English,\"You bring friends? Go! Bring friends! I vait!\"
Needless to say, his adversories just slunk away, figuring that one sound
thrashing a day was a-plenty. Jeeva has made a lasting impression on me, even
after the passage of 40 years.
This unique piece of software, unique in that no other Python 2.x script
has ever been named after a goonda autorickshaw driver, is dedicated to
his memory."""
        print S
        os._exit(0)
    #Test the validity of the input args/opts related to Source/Dest folders and return the 
    #Source and Dest folder names
    source, dest = GetSourceDest(opts, args)
    #print source, dest
    try:  #EGOF use AssertionError exception to quickly jump out of program
        #EGOF Exclusive OR
        assert (opts.compare and not opts.copyopt) or (not opts.compare and opts.copyopt),\
        "Either --compare or --copy required, not neither, not both. See help (-h)"
        
        #Handle the --depth option.
        #Must only be used with --compare
        assert not (opts.copyopt and opts.depth),"--depth option only permitted with --compare option"
        #and if present, go ahead and turn on the --recursive option even if latter was not explcitly turned on
        if opts.depth:
            opts.recursive = True
        depth = opts.depth
        
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

    return opts, source, dest, depth
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
        that are in either one or the other folder, or in both folders. User
        can decide with CL args what level of detail to output with --details
    """
    def Print_Details(sourcenotdestReg, sourceanddestReg, destnotsourceReg,
                      sourcenotdestDir, sourceanddestDir, destnotsourceDir, opts, indent):
        """Print details if and at level of detail the user has requested with --details
        """
        def PrintContent(S_in, title):
            """Print in comma sep form. S_in=set() of file names. title=string
            """
            print indent, title,  "\n",  indent, "-"*len(title)
            PrintIndentWidth(S_in, len(indent), width=WIDTH_PRINTINDENTWIDTH)
        #------------------------------
        print_detail = (opts.details == "yes")
        if opts.details == "query":
            print_detail = raw_input(indent+"List the actual filenames? (Y/y)").upper() == "Y"
        if print_detail:
            T1 = ( (sourcenotdestReg, "FILES IN SOURCE ONLY:"),
            (sourceanddestReg, "FILES COMMON TO BOTH:"),
            (destnotsourceReg, "FILES IN DESTINATION ONLY:"),
            (sourcenotdestDir, "DIRS IN SOURCE ONLY:"),
            (sourceanddestDir, "DIRS COMMON TO BOTH:"),
            (destnotsourceDir, "DIRS IN DESTINATION ONLY:") )
            for t in T1:
                if len(t[0]): PrintContent(t[0].copy(), t[1])

        #See if a mask of y's and n's was given: Should be a 6 letter string consisting ONLY of Y and N, case-insenstive
        if len(opts.details) == 6:
            mask = opts.details.upper()
            d1 = Counter(mask)
            if d1["Y"] + d1["N"] == 6:      #sum of number of Ys and Ns is 6. So must be a mask
                T1 = ( (sourcenotdestReg, "FILES IN SOURCE ONLY:"),
                       (sourceanddestReg, "FILES COMMON TO BOTH:"),
                       (destnotsourceReg, "FILES IN DESTINATION ONLY:"),
                       (sourcenotdestDir, "DIRS IN SOURCE ONLY:"),
                       (sourceanddestDir, "DIRS COMMON TO BOTH:"),
                       (destnotsourceDir, "DIRS IN DESTINATION ONLY:") )
                for i in range(6):
                    if mask[i]=="Y" and len(T1[i][0]): PrintContent(T1[i][0].copy(), T1[i][1])

    #------------------------------------------------
    #indent is False on first call
    if not bool(indent): print "Source folder:%s        Destination folder:%s" % (source, dest)  #only do at top-level

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
        in Source but not Dest, and a set of files in Source AND in Dest
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
        """Do a copy of source/fn to dest/fn, where fn is filename.
        If dryrun is true then just pretend to copy
        """
        if dryrun:
            #print "%sDryrun: shutil.copyfile(%s, %s)" % (indent, os.path.join(source, fn), os.path.join(dest, fn))
            pass
        else:
            try:
                shutil.copyfile(os.path.join(source, fn), os.path.join(dest, fn))
            except Exception, X:
                print indent, X
    #----------------------------
    
    #Whole funny business with S_title is because I do not want to print it unless some
    #specific action occured. Otherwise the output is too verbose and conists mainly of
    #meaningless S_titles
    #S_title = "%sSource folder:%s.   Destination folder:%s" % (indent, source, dest)
    S_title = "%sSOURCE:%s.   DESTINATION:%s" % (indent, source, dest)
    #Add a row of underscores above it for clearer display and put whole thing back into S_title
    len_underscores = min(len(S_title),50)     #EGOF putting a underscore or minus sign underline
    S_title = "%s%s\n%s" % (indent, len_underscores*"_",S_title)   #EGOF repetitive char in string

    #print indent, "Source folder:%s.   Destination folder:%s" % (source, dest)
    copyopt = opts.copyopt
    #For remaining options need more than merely file name, so use the Pathitem class as set member
    if copyopt == "mod" or copyopt == "update":
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
            #print S_title, indent, "Copied %d files that have been modified in Source" % icount
            print S_title, indent, "COPIED %d MODIFIED FILES" % icount
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
                #print S_title, indent, "Copied %d files that were in Source but not in Dest" % icount
                print S_title, indent, "COPIED %d NEW FILES" % icount
                S_title = ""
            
            if opts.recursive:
                #create directories in set_sourcenotdestDir as subdirs of dest
                for p in set_sourcenotdestDir:
                    sourcepath = os.path.join(source, p.path)
                    destpath = os.path.join(dest, p.path)
                    assert not os.path.exists(destpath), "%s should not exist" % destpath
                    do_copytree = False
                    if (opts.mkdir).lower() == "yes":
                        do_copytree = True
                    elif (opts.mkdir).lower() == "no":
                        do_copytree = False
                    elif (opts.mkdir).lower() == "query":
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


#--------------------------------------------------------------------------
def Enter_dir(source, dest, opts, indent, start_depth=0, max_depth=0):
    """ Get a list and size of all names of files and subdirectories in directory source
        Recursively go down
    """
    global max_depth_reached
    if (max_depth and (start_depth > max_depth)):  #do not do if --depth is being used and have surpassed limit
        return 
    max_depth_reached = max(start_depth, max_depth_reached)

    if opts.compare:
        sourceanddestDir = CompareFolder(source, dest, opts, indent)
    elif opts.copyopt:
        sourceanddestDir = CopyFolder(source, dest, opts, indent)
    if not opts.recursive:
        return
    

    #recursive descent into directories
    for item in sourceanddestDir:
        # if item is a sub-directory, ensure that it exists, and that a corr item exists
        # in the destination, and then go into it
        sourcepath = os.path.join(source, item)
        destpath = os.path.join(dest, item)
        Enter_dir(sourcepath, destpath, opts, indent+INDENT_INCREMENT, start_depth+1, max_depth)

    return
#-------------------------------------------------------------------------------

#--------------------------------------- main -----------------------------------
CLOP = DefineInputOptsnArgs(Version_Number[0]+Version_Number[1])  #Define the input command line opts and args. 
opts, source, dest, depth = ProcessInputOptsnArgs(CLOP)
if opts.dryrun: print "Dryrun option is ON. NO actual copying will occur"

#Most work done here
indent = ""
Enter_dir(source, dest, opts, indent, 0, depth)

print "\n"          #do some depth reporting
if depth:
    if max_depth_reached < depth:
        print "Was only necessary to go down %i levels. --depth %i was requested." % (max_depth_reached, depth)
    else:
        print "Went down %i levels as per -depth request." % (max_depth_reached)
else:
    if opts.recursive:
        print "Went down %i levels --recursively." % (max_depth_reached)

# finally, write out names of dirs that gave a problem
L_listerrors = set(L_listerrors)    #remove duplicate entries:
if len(L_listerrors):     #EGOF handling a raw_input yesno in one line, testing for uppercase Y
    if (raw_input("Warning: Unable to list %i directories. Show?(Y/y)" % len(L_listerrors)).upper() =="Y"):
        print "The following directories were not processed due to dir listing Errors"
        for d in L_listerrors:
            print d
