# Jeeva  (Still testing. Do not download.)
**Testing**

###Overview
This is a file/directory utility useful for:

A. When called with **--compare**: for comparing 2 directories/folders (or directory/folder trees). No copying is done. 
Primarily useful for comparing directories/trees that are expected to be very similar or identical and you are trying to find where the differences are.

B. Mirroring directories, when called with **--copy**. Quick simple copy to another location with zero sophistication. Primarily useful for keeping a mirror on another hard drive or for frequent copying to a USB stick. Short copying time as allows one to selectively copy over to the destination folder only those files that are newer in source than in the destination folder, useful when the total number of files is large but the number of newer files is relatively small. Optionally recursively descend directory tree.


###Detailed Description:
A. Compare: 
`jeeva --compare Source Dest`  Either for a single directory, or, with `--recursive`, down a directory tree. For each directory the display comprises 6 quantities:
   1. Number of  regular files in source folder but not destination directory
   2. # regular files in both source and dest
   3. # in dest but not source, 
   4,5,6. the same 3 corresponding values but for directories/folders instead of regular files

With `--details` option displays actual file names in these categories.

B. Copying:
`jeeva --copy all Source Dest` : Copies all regular files from directory Source to directory Dest. Adding `--recursive` copies entire directory tree structure, overwriting Dest.
Option `--dryrun` shows what action would be taken without actually doing any copying, so that you can check beforehand 

`jeeva --copy newer Source Dest`  : copies regular files that are newer in source. Files that are in Source but not in Dest are **not** copied. With `--recursive`, descends tree structure.

`jeeva --copy update Source Dest` : Similar to "newer" but additionally copies files that are in Source but not in Dest.  With `--recursive`, descends tree structure. With `--recursive and --mkdir yes`, directories that are in Source but not in Dest are also created and copied. 
