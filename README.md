# Jeeva  (Still testing. Do not download.)
**Testing**

### Overview
This is a file/directory utility useful for:

A. When called with **--compare**: for comparing 2 directories (or directory trees). No copying is done. 
Primarily useful for comparing directories/trees that are expected to be very similar or identical and you are trying to find where the differences are.

B. Mirroring directories, when called with **--copy**. Quick simple copy to another location with zero sophistication. Primarily useful for keeping a mirror on another hard drive or for frequent copying to a USB stick. Short copying time as allows one to selectively copy over to the destination directory only those files that are newer in source than in the destination directory, useful when the total number of files is large but the number of newer files is relatively small. Optionally recursively descend directory tree.


### Detailed Description:
A. Compare: 
`jeeva --compare Source Dest`  Compare the two directories Source and Dest, or, with `--recursive`, descend their directory trees and compare any corresponding directories. For each directory the display comprises 6 quantities:
   1. Number of regular files in source directory but not destination directory
   2. Number of regular files in both source and dest
   3. Number in dest but not source, 
   4. (and 5,6) The same 3 corresponding values but for directories instead of regular files

With `--details d_option` option displays actual file names in these 6 categories. `d_option` must be one of "yes", "query" or a 6 character mask (like "yyyyyy" or "ynynyn" or "nnnnnn") which selects for which of the 6 quantities above you wish to display file names..

B. Copying:
`jeeva --copy all Source Dest` : Copies all regular files from directory Source to directory Dest. Adding `--recursive` copies entire directory tree structure, overwriting Dest.
Option `--dryrun` shows what action would be taken without actually doing any copying, so that you can check beforehand 

`jeeva --copy newer Source Dest`  : copies regular files that are newer in Source. Files that are in Source but not in Dest are **not** copied. With `--recursive`, descends tree structure, copying newer regular files. Never copies directory files.

`jeeva --copy update Source Dest` : Similar to *newer* but additionally copies regular files that are in Source but not in Dest.  With `--recursive`, descends tree structure. With `--recursive and --mkdir yes` (or `--mkdir query`), directories that are in Source but not in Dest are also created and copied. 
