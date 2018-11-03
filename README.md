# Jeeva

### Overview
This is a file/directory utility useful for:

**A.** Primarily useful for comparing directories that are expected to be very similar/identical and you are trying to find where the differences are. Call with **--compare**. A read-only operation, no copying is done. Optionally can recursively descend directory tree.


**B.** Mirroring directories, when called with **--copy**. Quick simple copy to another location with zero sophistication. Primarily useful for keeping a mirror on another hard drive or for frequent copying to a USB stick. Has a short copying time as allows one to selectively copy over to the destination directory *only those files* that are newer in source than in the destination directory; useful when the total number of files is large but the number of newer files is relatively small. 

*nb*: There is a better documentation file at www.twentypede.com/leg4/jeeva1.4.html . Also there is a significant useful improvement that is not mentioned in the docs below.

### Detailed Description:
**A. Compare:**
`jeeva --compare Source Dest`  Compare the two directories Source and Dest, or, with `--recursive`, descend their directory trees and compare any corresponding directories. For each directory 6 quantities are returned:
   1. Number of regular files in source directory but not destination directory
   2. Number of regular files in both source and destination
   3. Number in destination but not source, 
   4. (and 5,6) The same 3 corresponding values but for directories instead of for regular files

With `--details d_option` option displays actual file names in these 6 categories. `d_option` must be one of "yes", "query" or a 6 character yes/no mask (e.g. "yyyyyy" or "ynynyn" or "nnnnnn") to select which of the 6 quantities you wish displayed.

Example: `jeeva --compare .\Videos D:\Shaheen\Mirror\Videos` produces:  
```Source folder:.\Videos        Destination folder:D:\Shaheen\Mirror\Videos
Videos (23,0,0 ; 16,3,0)
```  
indicating that the first directory contains 23 regular files not in the second directory, 16 sub-dirs not in second directory, and 3 sub-dirs are common to both directories. Adding `--recursive` produces similar output for the 3 sub-dirs that they have in common:  
```Source folder:.\Videos        Destination folder:D:\Shaheen\Mirror\Videos
Videos (23,0,0 ; 16,3,0)
   |->2017 (0,23,0 ; 0,0,0)
   |->Lumix (0,1,0 ; 1,2,0)
      |->Ohio 2018 (20,60,91 ; 0,0,0)
      |->India Trip Feb Mar 2018 (0,98,0 ; 0,0,0)
   |->2018 (2,7,0 ; 0,0,0)
```

**B. Copying:**
`jeeva --copy mod Source Dest`  : copies regular files that are newer in Source. Files that are in Source but not in Dest are **not** copied. With `--recursive`, does same while descending tree structure. Never copies directory files.

`jeeva --copy update Source Dest` : Similar to *mod* but additionally copies regular files that are in Source but not in Dest.  With `--recursive`, does same while descending tree structure. With `--recursive --mkdir yes` (or `--mkdir query`), additionally, directories that are in Source but not in Dest are created and copied along with their contents (shutil.copytree is used at the uppermost level here, so not to worry, you wil not have to laboriously descend the whole tree if you used `--mkdir query`).

Both Source and Dest must exist beforehand and, rather than that I implement a `jeeva --copy all Source Dest`, use your OS's directory tree copying utility to initially create Dest. (MS Windows use `xcopy` or `robocopy`. Linux/Unix/Apple use `cp -ar` or `cp -r`)

Option `--dryrun` shows what action would be taken *without doing any actual copying*, to allow a check beforehand.

### Author:
Shaheen Tonse
### License:
This is simple software, <500 lines, only imports os, shutil, optparse and collections. It is free and distributed without warranty. Apache License 2.0 applies, please read, (http://www.apache.org/licenses/LICENSE-2.0) especially if you plan to re-distribute.
